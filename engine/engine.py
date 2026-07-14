#!/usr/bin/env python3
"""
DMC paper-trading engine — SIMULATED ONLY. Never places a real order.
No broker credentials, no auth, no order endpoints. Trades are rows in a JSON file.

MECHANIZATION NOTICE
DMC's rules contain genuinely subjective terms: "significant level", "decisive close",
"clean gain". A computer cannot be subjective, so this engine pins them to explicit
thresholds (below). Results therefore test THIS MECHANIZATION, not Hunter's judgment.
That distinction is the whole ballgame — do not skip past it.

  significant level = prior day H/L/C and prior week H/L/C
  decisive close    = candle body >= 50% of its range
  gain              = close beyond the level when the PRIOR close was not beyond it
  fail              = wick beyond, close not beyond  (used as a filter, not an entry)
  range lock        = |close - close[-10]| < 0.75 * ATR(10)  -> stand aside
  entry             = NEXT day's open (signal fires at the close; you can't fill at it)
  stop              = far side of the traded level, buffered 0.25 * ATR(14)
  target            = next level in the trade's direction (fallback 2R)
"""
import json, os, math
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))

CFG = {
    "start_equity": 200_000.0,
    "max_drawdown_pct": 10.0,      # hard halt
    "risk_per_trade_pct": 0.5,     # 0.5% = $1,000 at start
    "max_concurrent": 4,
    "max_open_risk_pct": 2.0,
    "decisive_body_ratio": 0.50,
    "chop_atr_mult": 0.75,
    "stop_buffer_atr": 0.25,
    "warmup_bars": 15,
}

def load_candles():
    raw = json.load(open(os.path.join(HERE, "data", "candles.json")))
    out = {}
    for sym, rows in raw.items():
        out[sym] = [{"t": r[0], "o": r[1], "h": r[2], "l": r[3], "c": r[4]} for r in rows]
    return out

def atr(bars, n=14):
    if len(bars) < 2: return 0.0
    trs = []
    for i in range(1, len(bars)):
        h, l, pc = bars[i]["h"], bars[i]["l"], bars[i-1]["c"]
        trs.append(max(h - l, abs(h - pc), abs(l - pc)))
    trs = trs[-n:]
    return sum(trs) / len(trs) if trs else 0.0

def levels_at(bars, i):
    """DMC levels visible at the CLOSE of bar i (uses completed bars only)."""
    lv = []
    p = bars[i-1]
    lv += [("prior day high", p["h"]), ("prior day low", p["l"]), ("prior day close", p["c"])]
    wk = bars[max(0, i-5):i]
    if wk:
        lv += [("prior week high", max(b["h"] for b in wk)),
               ("prior week low",  min(b["l"] for b in wk)),
               ("prior week close", wk[-1]["c"])]
    seen, out = set(), []
    for k, v in lv:
        r = round(v, 2)
        if r not in seen:
            seen.add(r); out.append({"kind": k, "price": r})
    return out

def decisive(b):
    rng = b["h"] - b["l"]
    return rng > 0 and abs(b["c"] - b["o"]) / rng >= CFG["decisive_body_ratio"]

def is_chop(bars, i):
    if i < 11: return False
    a = atr(bars[:i+1], 10)
    return abs(bars[i]["c"] - bars[i-10]["c"]) < CFG["chop_atr_mult"] * a * 1.0 if a else False

def signal_at(bars, i):
    """Return a gain signal at the close of bar i, or None."""
    if i < CFG["warmup_bars"]: return None
    today, prev = bars[i], bars[i-1]
    if not decisive(today): return None
    if is_chop(bars, i): return None
    lv = levels_at(bars, i)
    best = None
    for L in lv:
        p = L["price"]
        gained_up = today["c"] > p and prev["c"] <= p
        gained_dn = today["c"] < p and prev["c"] >= p
        if gained_up or gained_dn:
            dist = abs(today["c"] - p)
            if best is None or dist < best["dist"]:
                best = {"side": "long" if gained_up else "short",
                        "level": p, "kind": L["kind"], "dist": dist, "levels": lv}
    return best

def build_trade(bars, i, sig, equity):
    """Signal fires at close of bar i. Entry is the OPEN of bar i+1."""
    if i + 1 >= len(bars): return None
    e = bars[i+1]["o"]
    a14 = atr(bars[:i+1], 14)
    buf = CFG["stop_buffer_atr"] * a14
    lvl = sig["level"]
    if sig["side"] == "long":
        stop = lvl - buf
        if e <= stop: return None
        ups = sorted([L["price"] for L in sig["levels"] if L["price"] > e])
        tgt = ups[0] if ups else e + 2 * (e - stop)
    else:
        stop = lvl + buf
        if e >= stop: return None
        dns = sorted([L["price"] for L in sig["levels"] if L["price"] < e], reverse=True)
        tgt = dns[0] if dns else e - 2 * (stop - e)
    risk_per_unit = abs(e - stop)
    if risk_per_unit <= 0: return None
    rr = abs(tgt - e) / risk_per_unit
    if rr < 1.0: return None                       # DMC: target must beat the stop
    risk_cash = equity * CFG["risk_per_trade_pct"] / 100
    qty = risk_cash / risk_per_unit
    return {"side": sig["side"], "level": lvl, "level_kind": sig["kind"],
            "entry": round(e, 2), "stop": round(stop, 2), "target": round(tgt, 2),
            "qty": round(qty, 2), "risk_cash": round(risk_cash, 2),
            "risk_per_unit": round(risk_per_unit, 4), "planned_rr": round(rr, 2),
            "style": "confirmation"}

def run(mode="backtest"):
    candles = load_candles()
    syms = list(candles)
    n = min(len(candles[s]) for s in syms)
    dates = [candles[syms[0]][k]["t"] for k in range(n)]

    equity = CFG["start_equity"]
    peak = equity
    floor_ = CFG["start_equity"] * (1 - CFG["max_drawdown_pct"] / 100)
    open_pos, closed, curve, daily = [], [], [], []
    halted = False
    tid = 1

    for i in range(n):
        day = dates[i]
        # ---- manage open positions on today's bar (stop wins ties: conservative)
        still = []
        for t in open_pos:
            b = candles[t["symbol"]][i]
            if b["t"] != day: still.append(t); continue
            hit = None
            if t["side"] == "long":
                if b["l"] <= t["stop"]:   hit = ("stop", t["stop"])
                elif b["h"] >= t["target"]: hit = ("target", t["target"])
            else:
                if b["h"] >= t["stop"]:   hit = ("stop", t["stop"])
                elif b["l"] <= t["target"]: hit = ("target", t["target"])
            if hit:
                kind, px = hit
                move = (px - t["entry"]) if t["side"] == "long" else (t["entry"] - px)
                pl = move * t["qty"]
                t.update({"status": "closed", "exit": round(px, 2), "exit_date": day,
                          "reason": f"{kind} hit", "pl": round(pl, 2),
                          "r": round(move / t["risk_per_unit"], 2)})
                equity += pl
                closed.append(t)
            else:
                still.append(t)
        open_pos = still

        # ---- drawdown guard
        peak = max(peak, equity)
        if equity <= floor_ and not halted:
            halted = True

        # ---- look for new signals at today's close
        entries_today = []
        if not halted and len(open_pos) < CFG["max_concurrent"]:
            open_risk = sum(t["risk_cash"] for t in open_pos)
            for s in syms:
                if len(open_pos) + len(entries_today) >= CFG["max_concurrent"]: break
                if any(t["symbol"] == s for t in open_pos): continue
                bars = candles[s]
                sig = signal_at(bars, i)
                if not sig: continue
                t = build_trade(bars, i, sig, equity)
                if not t: continue
                if open_risk + t["risk_cash"] > equity * CFG["max_open_risk_pct"] / 100: continue
                t.update({"id": tid, "symbol": s, "signal_date": day,
                          "entry_date": dates[i+1] if i+1 < n else None,
                          "status": "open", "exit": None, "r": None, "pl": None})
                tid += 1; open_risk += t["risk_cash"]
                entries_today.append(t)
        # entries fill on the NEXT bar's open
        for t in entries_today:
            open_pos.append(t)

        # ---- mark to market
        unreal = 0.0
        for t in open_pos:
            b = candles[t["symbol"]][i]
            if t["entry_date"] and b["t"] >= t["entry_date"]:
                move = (b["c"] - t["entry"]) if t["side"] == "long" else (t["entry"] - b["c"])
                unreal += move * t["qty"]
        eq = equity + unreal
        peak = max(peak, eq)
        dd = (peak - eq) / peak * 100 if peak else 0
        curve.append({"date": day, "equity": round(eq, 2), "realized": round(equity, 2),
                      "peak": round(peak, 2), "dd_pct": round(dd, 2),
                      "open": len(open_pos), "halted": halted})
        daily.append({"date": day, "closed_today": [t["id"] for t in closed if t.get("exit_date") == day],
                      "opened_today": [t["id"] for t in entries_today]})

    return {"config": CFG, "mode": mode, "generated": datetime.utcnow().isoformat() + "Z",
            "symbols": syms, "floor": floor_,
            "trades": closed + open_pos, "curve": curve, "daily": daily,
            "final_equity": curve[-1]["equity"] if curve else CFG["start_equity"],
            "halted": halted}

if __name__ == "__main__":
    res = run()
    json.dump(res, open(os.path.join(HERE, "data", "results.json"), "w"), indent=2)
    cl = [t for t in res["trades"] if t["status"] == "closed"]
    op = [t for t in res["trades"] if t["status"] == "open"]
    rs = [t["r"] for t in cl]
    w = [r for r in rs if r > 0]
    print(f"bars: {len(res['curve'])}  symbols: {res['symbols']}")
    print(f"closed: {len(cl)}   open: {len(op)}")
    if rs:
        print(f"win rate: {len(w)/len(rs)*100:.1f}%   expectancy: {sum(rs)/len(rs):+.2f} R   total: {sum(rs):+.2f} R")
    print(f"final equity: ${res['final_equity']:,.2f}   max dd: {max(c['dd_pct'] for c in res['curve']):.2f}%")
    print(f"halted: {res['halted']}")
