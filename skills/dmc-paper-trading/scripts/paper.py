#!/usr/bin/env python3
"""
DMC Paper Trading — simulated trade journal + level tools.

HARD RULE, ENFORCED BY DESIGN:
  This script talks to READ-ONLY market DATA endpoints only.
  It contains no brokerage/exchange credentials, no authentication, no signing,
  and no order/position/withdrawal endpoints. It cannot place a trade.
  Every "trade" here is a row in a local JSON file. Nothing else.

Stdlib only. No pip install required.

Usage:
  paper.py levels  SYM [--tf 1d] [--bars 40] [--ltf 1h]
  paper.py open    SYM --side long --level 150.25 --entry 150.40 --stop 149.10
                       --target 154.00 [--style confirmation] [--size 100]
                       [--range-locked] [--note "..."]
  paper.py mark    [--id N]
  paper.py check   [--id N]
  paper.py close   ID --price 153.20 [--reason "hit target"]
  paper.py list    [--all]
  paper.py stats
  paper.py grade   ID
  paper.py quote   SYM
"""

import argparse, json, os, sys, csv, io, math
import urllib.request, urllib.error
from datetime import datetime, timezone

LEDGER = os.environ.get("DMC_LEDGER", os.path.join(os.getcwd(), "dmc-paper", "ledger.json"))
UA = {"User-Agent": "Mozilla/5.0 (dmc-paper-trading; read-only market data)"}

# ---------------------------------------------------------------- safety rail
_FORBIDDEN = ("order", "/v1/orders", "withdraw", "position/close", "api-key", "secret")
def _assert_data_only(url: str):
    low = url.lower()
    for bad in ("/order", "/orders", "/withdraw", "/account", "/trade?", "/position"):
        if bad in low:
            raise SystemExit(f"REFUSED: '{url}' looks like a trading/account endpoint. "
                             "This tool is read-only market data. It does not place orders.")

# ---------------------------------------------------------------- data fetch
def _get(url, timeout=15):
    _assert_data_only(url)
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()

def _is_crypto(sym):
    s = sym.upper()
    return s.endswith(("USDT", "USDC", "BUSD")) or s in ("BTCUSD", "ETHUSD")

def fetch_candles(symbol, tf="1d", bars=60, provider="auto"):
    """Return list of dicts: {t, o, h, l, c, v}. Newest last."""
    if provider == "auto":
        provider = "binance" if _is_crypto(symbol) else "yahoo"
    try:
        if provider == "binance":
            return _binance(symbol, tf, bars)
        if provider == "yahoo":
            return _yahoo(symbol, tf, bars)
        if provider == "stooq":
            return _stooq(symbol, bars)
    except Exception as e:
        if provider == "yahoo":
            sys.stderr.write(f"[warn] yahoo failed ({e}); falling back to stooq daily\n")
            return _stooq(symbol, bars)
        raise
    raise SystemExit(f"unknown provider: {provider}")

_BINANCE_TF = {"1m":"1m","5m":"5m","15m":"15m","30m":"30m","1h":"1h","4h":"4h","1d":"1d","1w":"1w"}
def _binance(symbol, tf, bars):
    iv = _BINANCE_TF.get(tf)
    if not iv: raise SystemExit(f"binance: unsupported timeframe {tf}")
    url = f"https://api.binance.com/api/v3/klines?symbol={symbol.upper()}&interval={iv}&limit={min(bars,1000)}"
    raw = json.loads(_get(url))
    return [{"t": datetime.fromtimestamp(k[0]/1000, timezone.utc).isoformat(),
             "o": float(k[1]), "h": float(k[2]), "l": float(k[3]),
             "c": float(k[4]), "v": float(k[5])} for k in raw]

_Y_RANGE = {"1m":"5d","5m":"1mo","15m":"1mo","30m":"1mo","1h":"3mo","1d":"1y","1wk":"5y"}
def _yahoo(symbol, tf, bars):
    iv = {"1h":"60m","1w":"1wk"}.get(tf, tf)
    rng = _Y_RANGE.get(tf, "1y")
    url = (f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol.upper()}"
           f"?interval={iv}&range={rng}")
    d = json.loads(_get(url))
    res = d["chart"]["result"][0]
    ts = res["timestamp"]; q = res["indicators"]["quote"][0]
    out = []
    for i, t in enumerate(ts):
        if q["open"][i] is None or q["close"][i] is None:
            continue
        out.append({"t": datetime.fromtimestamp(t, timezone.utc).isoformat(),
                    "o": q["open"][i], "h": q["high"][i], "l": q["low"][i],
                    "c": q["close"][i], "v": (q.get("volume") or [None])[i] or 0})
    return out[-bars:]

def _stooq(symbol, bars):
    s = symbol.lower()
    if "." not in s: s += ".us"
    url = f"https://stooq.com/q/d/l/?s={s}&i=d"
    txt = _get(url).decode()
    rows = list(csv.DictReader(io.StringIO(txt)))
    out = [{"t": r["Date"], "o": float(r["Open"]), "h": float(r["High"]),
            "l": float(r["Low"]), "c": float(r["Close"]),
            "v": float(r.get("Volume") or 0)} for r in rows if r.get("Close")]
    return out[-bars:]

def last_price(symbol, provider="auto"):
    c = fetch_candles(symbol, "1d" if not _is_crypto(symbol) else "1h", 3, provider)
    return c[-1]["c"]

# ---------------------------------------------------------------- DMC levels
def dmc_levels(candles, n=6):
    """DMC levels from the most recent COMPLETED candles: prior highs, lows, closes.
    Returns list of {price, kind, bar} newest first."""
    out = []
    for i, k in enumerate(reversed(candles[:-1][-n:])):   # exclude the live/last candle
        age = i + 1
        out.append({"price": k["h"], "kind": f"prior high (-{age})", "bar": k["t"]})
        out.append({"price": k["l"], "kind": f"prior low (-{age})",  "bar": k["t"]})
        out.append({"price": k["c"], "kind": f"prior close (-{age})","bar": k["t"]})
    return out

def confluence(htf, ltf, tol_pct=0.15):
    """Zones = HTF level and LTF level within tol_pct of each other."""
    zones = []
    for a in htf:
        for b in ltf:
            if a["price"] == 0: continue
            if abs(a["price"] - b["price"]) / a["price"] * 100 <= tol_pct:
                lo, hi = sorted((a["price"], b["price"]))
                zones.append({"low": lo, "high": hi, "mid": (lo+hi)/2,
                              "htf": a["kind"], "ltf": b["kind"]})
    zones.sort(key=lambda z: z["mid"])
    merged = []
    for z in zones:
        if merged and z["low"] <= merged[-1]["high"]:
            merged[-1]["high"] = max(merged[-1]["high"], z["high"])
            merged[-1]["mid"] = (merged[-1]["low"] + merged[-1]["high"]) / 2
        else:
            merged.append(dict(z))
    return merged

def gain_fail(candles, level, lookback=10):
    """Classify recent behavior at a level. A GAIN needs a CLOSE beyond. A wick is not a gain."""
    recent = candles[-lookback:]
    events = []
    for k in recent:
        touched = k["l"] <= level <= k["h"]
        closed_above = k["c"] > level
        closed_below = k["c"] < level
        wick_only_above = k["h"] > level and not closed_above
        wick_only_below = k["l"] < level and not closed_below
        body = abs(k["c"] - k["o"]); rng = max(k["h"] - k["l"], 1e-9)
        decisive = (body / rng) >= 0.5
        if touched or k["h"] > level > k["l"]:
            if closed_above:
                events.append({"t": k["t"], "event": "GAIN (close above)",
                               "decisive": decisive, "close": k["c"]})
            elif closed_below:
                events.append({"t": k["t"], "event": "GAIN (close below)" if k["o"] > level
                               else "FAIL (rejected, closed below)",
                               "decisive": decisive, "close": k["c"]})
            elif wick_only_above or wick_only_below:
                events.append({"t": k["t"], "event": "FAIL (wick only, no close beyond)",
                               "decisive": False, "close": k["c"]})
    return events

def range_lock(candles, upper, lower, lookback=12):
    """Locked if NO candle in lookback closed beyond either boundary."""
    recent = candles[-lookback:]
    closes = [k["c"] for k in recent]
    broke_up = any(c > upper for c in closes)
    broke_dn = any(c < lower for c in closes)
    locked = not broke_up and not broke_dn
    return {"locked": locked, "bars_checked": len(recent),
            "closed_above_upper": broke_up, "closed_below_lower": broke_dn,
            "upper": upper, "lower": lower}

# ---------------------------------------------------------------- ledger
def load():
    if not os.path.exists(LEDGER):
        return {"trades": [], "next_id": 1}
    with open(LEDGER) as f:
        return json.load(f)

def save(d):
    os.makedirs(os.path.dirname(LEDGER), exist_ok=True)
    with open(LEDGER, "w") as f:
        json.dump(d, f, indent=2)

def r_multiple(t, exit_price):
    risk = abs(t["entry"] - t["stop"])
    if risk == 0: return 0.0
    move = (exit_price - t["entry"]) if t["side"] == "long" else (t["entry"] - exit_price)
    return move / risk

# ---------------------------------------------------------------- commands
def cmd_levels(a):
    htf = fetch_candles(a.symbol, a.tf, a.bars, a.provider)
    lv = dmc_levels(htf, a.n)
    px = htf[-1]["c"]
    print(f"\n{a.symbol.upper()}  {a.tf}  last close {px:.4f}   (levels exclude the live candle)\n")
    print(f"{'LEVEL':>12}  {'DIST%':>7}  SOURCE")
    for l in sorted(lv, key=lambda x: -x["price"]):
        d = (l["price"] - px) / px * 100
        mark = "  <-- price" if abs(d) < 0.2 else ""
        print(f"{l['price']:>12.4f}  {d:>+6.2f}%  {l['kind']}{mark}")
    if a.ltf:
        ltf = fetch_candles(a.symbol, a.ltf, a.bars, a.provider)
        z = confluence(lv, dmc_levels(ltf, a.n), a.tol)
        print(f"\nCONFLUENCE ZONES ({a.tf} x {a.ltf}, tol {a.tol}%):")
        if not z: print("  none")
        for zz in z:
            print(f"  {zz['low']:.4f} - {zz['high']:.4f}   [{zz['htf']} + {zz['ltf']}]")
    hi = max(l["price"] for l in lv); lo = min(l["price"] for l in lv)
    rl = range_lock(htf, hi, lo)
    print(f"\nRANGE-LOCK CHECK (outer levels {lo:.4f} / {hi:.4f}, last {rl['bars_checked']} bars):")
    print("  RANGE LOCKED — no clean close beyond either boundary. Reduce size or stand aside."
          if rl["locked"] else "  not locked — a boundary has been closed beyond.")
    print("\nAnalysis only — not financial advice. No real orders are placed.\n")

def cmd_quote(a):
    print(f"{a.symbol.upper()}  last {last_price(a.symbol, a.provider):.4f}")

def cmd_open(a):
    d = load()
    if a.side == "long" and a.stop >= a.entry:
        sys.exit("REJECTED: long stop must sit BELOW entry.")
    if a.side == "short" and a.stop <= a.entry:
        sys.exit("REJECTED: short stop must sit ABOVE entry.")
    risk = abs(a.entry - a.stop)
    rr = abs(a.target - a.entry) / risk if risk else 0
    t = {"id": d["next_id"], "symbol": a.symbol.upper(), "side": a.side,
         "level": a.level, "entry": a.entry, "stop": a.stop, "target": a.target,
         "style": a.style, "size": a.size, "range_locked": bool(a.range_locked),
         "note": a.note or "", "opened": datetime.now(timezone.utc).isoformat(),
         "status": "open", "exit": None, "closed": None, "reason": None,
         "risk_per_unit": round(risk, 6), "planned_rr": round(rr, 2)}
    d["trades"].append(t); d["next_id"] += 1; save(d)
    print(f"\nPAPER trade #{t['id']} logged (SIMULATED — no order was placed).")
    print(f"  {t['side'].upper()} {t['symbol']}  entry {t['entry']}  stop {t['stop']}  target {t['target']}")
    print(f"  level {t['level']}  style {t['style']}  risk/unit {t['risk_per_unit']}  planned R:R {t['planned_rr']}")
    if t["range_locked"]:
        print("  ! flagged RANGE LOCKED — DMC says reduce size or stand aside here.")
    if rr < 1: print(f"  ! planned R:R is {rr:.2f} (<1). Target is closer than the stop.")
    print()

def cmd_mark(a):
    d = load(); rows = [t for t in d["trades"] if t["status"] == "open"]
    if a.id: rows = [t for t in rows if t["id"] == a.id]
    if not rows: return print("no open paper trades.")
    print(f"\n{'ID':>3} {'SYM':<10} {'SIDE':<5} {'ENTRY':>10} {'LAST':>10} {'R':>7} {'P/L':>10}")
    tot = 0.0
    for t in rows:
        px = last_price(t["symbol"], a.provider)
        r = r_multiple(t, px)
        pl = (px - t["entry"]) * t["size"] * (1 if t["side"] == "long" else -1)
        tot += pl
        print(f"{t['id']:>3} {t['symbol']:<10} {t['side']:<5} {t['entry']:>10.4f} "
              f"{px:>10.4f} {r:>+7.2f} {pl:>+10.2f}")
    print(f"{'':>48}{'TOTAL':>7} {tot:>+10.2f}   (unrealized, simulated)\n")

def cmd_check(a):
    """Walk candles since entry. Did stop or target hit first? Conservative: stop wins a tie."""
    d = load(); rows = [t for t in d["trades"] if t["status"] == "open"]
    if a.id: rows = [t for t in rows if t["id"] == a.id]
    if not rows: return print("no open paper trades.")
    changed = False
    for t in rows:
        cs = fetch_candles(t["symbol"], a.tf, a.bars, a.provider)
        opened = t["opened"][:10]
        cs = [k for k in cs if k["t"][:10] >= opened] or cs[-1:]
        hit = None
        for k in cs:
            if t["side"] == "long":
                if k["l"] <= t["stop"]: hit = ("stop", t["stop"], k["t"]); break
                if k["h"] >= t["target"]: hit = ("target", t["target"], k["t"]); break
            else:
                if k["h"] >= t["stop"]: hit = ("stop", t["stop"], k["t"]); break
                if k["l"] <= t["target"]: hit = ("target", t["target"], k["t"]); break
        if hit:
            kind, px, when = hit
            t["status"] = "closed"; t["exit"] = px; t["closed"] = when
            t["reason"] = f"{kind} hit"; t["r"] = round(r_multiple(t, px), 2)
            t["pl"] = round((px - t["entry"]) * t["size"] * (1 if t["side"]=="long" else -1), 2)
            changed = True
            print(f"#{t['id']} {t['symbol']} -> {kind.upper()} at {px} on {when[:16]}  "
                  f"R {t['r']:+.2f}  P/L {t['pl']:+.2f}")
        else:
            print(f"#{t['id']} {t['symbol']} -> still open (neither stop nor target touched)")
    if changed: save(d)
    print("\nSimulated fills. Conservative: if a bar spans both stop and target, the stop is taken.\n")

def cmd_close(a):
    d = load()
    t = next((x for x in d["trades"] if x["id"] == a.id), None)
    if not t: sys.exit(f"no trade #{a.id}")
    if t["status"] != "open": sys.exit(f"#{a.id} already closed")
    t["status"] = "closed"; t["exit"] = a.price
    t["closed"] = datetime.now(timezone.utc).isoformat()
    t["reason"] = a.reason or "manual"
    t["r"] = round(r_multiple(t, a.price), 2)
    t["pl"] = round((a.price - t["entry"]) * t["size"] * (1 if t["side"]=="long" else -1), 2)
    save(d)
    print(f"#{t['id']} closed at {a.price}  R {t['r']:+.2f}  P/L {t['pl']:+.2f}  ({t['reason']})")

def cmd_list(a):
    d = load()
    rows = d["trades"] if a.all else [t for t in d["trades"] if t["status"] == "open"]
    if not rows: return print("nothing to show.")
    print(f"\n{'ID':>3} {'SYM':<10} {'SIDE':<5} {'STYLE':<13} {'ENTRY':>9} {'STOP':>9} "
          f"{'TGT':>9} {'STATUS':<7} {'R':>6}")
    for t in rows:
        r = f"{t['r']:+.2f}" if t.get("r") is not None and t["status"]=="closed" else "-"
        flag = " [RANGE-LOCKED]" if t.get("range_locked") else ""
        print(f"{t['id']:>3} {t['symbol']:<10} {t['side']:<5} {t['style']:<13} "
              f"{t['entry']:>9.4f} {t['stop']:>9.4f} {t['target']:>9.4f} "
              f"{t['status']:<7} {r:>6}{flag}")
    print()

def cmd_stats(a):
    d = load()
    cl = [t for t in d["trades"] if t["status"] == "closed"]
    if not cl: return print("no closed paper trades yet.")
    rs = [t["r"] for t in cl]; pls = [t.get("pl", 0) for t in cl]
    wins = [r for r in rs if r > 0]; losses = [r for r in rs if r <= 0]
    wr = len(wins) / len(rs) * 100
    avg_w = sum(wins)/len(wins) if wins else 0
    avg_l = sum(losses)/len(losses) if losses else 0
    exp = sum(rs)/len(rs)
    print(f"\nDMC PAPER STATS  ({len(cl)} closed, simulated)")
    print(f"  win rate      {wr:.1f}%   ({len(wins)}W / {len(losses)}L)")
    print(f"  avg win        {avg_w:+.2f} R")
    print(f"  avg loss       {avg_l:+.2f} R")
    print(f"  expectancy     {exp:+.2f} R per trade")
    print(f"  total          {sum(rs):+.2f} R   |   P/L {sum(pls):+.2f}")
    print("\n  by entry style:")
    for st in sorted({t["style"] for t in cl}):
        g = [t["r"] for t in cl if t["style"] == st]
        w = len([r for r in g if r > 0]) / len(g) * 100
        print(f"    {st:<14} n={len(g):<3} win {w:>5.1f}%  exp {sum(g)/len(g):+.2f} R")
    rl = [t["r"] for t in cl if t.get("range_locked")]
    if rl:
        print(f"\n  trades taken while RANGE LOCKED: n={len(rl)}  exp {sum(rl)/len(rl):+.2f} R")
        print("  (DMC says reduce size or stand aside in a range lock — check if these are dragging you.)")
    print("\n  Small samples mean nothing. This is a log of your discipline, not proof of an edge.")
    print("  Simulated results only. Not financial advice.\n")

def cmd_grade(a):
    """Grade a trade against DMC RULE COMPLIANCE — not against its outcome."""
    d = load()
    t = next((x for x in d["trades"] if x["id"] == a.id), None)
    if not t: sys.exit(f"no trade #{a.id}")
    checks = []
    if t["side"] == "long":
        ok = t["stop"] < t["level"]
        checks.append((ok, "Stop sits below the traded level (level failure = invalidation)"))
    else:
        ok = t["stop"] > t["level"]
        checks.append((ok, "Stop sits above the traded level (level failure = invalidation)"))
    near = abs(t["entry"] - t["level"]) / max(t["level"], 1e-9) * 100
    checks.append((near <= 1.0, f"Entry is at the level, not chasing ({near:.2f}% away)"))
    checks.append((t["planned_rr"] >= 1.0,
                   f"Target is further than the stop (planned R:R {t['planned_rr']})"))
    checks.append((t["style"] in ("blind", "confirmation", "dca"),
                   f"Entry style declared ({t['style']})"))
    checks.append((not t.get("range_locked"),
                   "Not taken inside a range lock" if not t.get("range_locked")
                   else "TAKEN INSIDE A RANGE LOCK — DMC says reduce size or stand aside"))
    print(f"\nDMC RULE COMPLIANCE — trade #{t['id']} {t['symbol']} {t['side']}")
    for ok, txt in checks:
        print(f"  [{'PASS' if ok else 'FAIL'}] {txt}")
    score = sum(1 for ok, _ in checks if ok)
    print(f"\n  {score}/{len(checks)} DMC rules followed.")
    print("  This grades PROCESS, not outcome. A rule-perfect trade can lose;")
    print("  a rule-breaking trade can win. Judge the process over many trades.")
    print("\n  Note: 'significant level' and 'decisive close' are subjective in DMC.")
    print("  This grader checks the mechanical rules only.\n")

# ---------------------------------------------------------------- cli
def main():
    p = argparse.ArgumentParser(description="DMC paper trading (simulated only — never places real orders)")
    p.add_argument("--provider", default="auto", choices=["auto","yahoo","binance","stooq"])
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("levels"); s.add_argument("symbol")
    s.add_argument("--tf", default="1d"); s.add_argument("--bars", type=int, default=60)
    s.add_argument("--n", type=int, default=5); s.add_argument("--ltf", default=None)
    s.add_argument("--tol", type=float, default=0.15); s.set_defaults(f=cmd_levels)

    s = sub.add_parser("quote"); s.add_argument("symbol"); s.set_defaults(f=cmd_quote)

    s = sub.add_parser("open"); s.add_argument("symbol")
    s.add_argument("--side", required=True, choices=["long","short"])
    s.add_argument("--level", type=float, required=True)
    s.add_argument("--entry", type=float, required=True)
    s.add_argument("--stop", type=float, required=True)
    s.add_argument("--target", type=float, required=True)
    s.add_argument("--style", default="confirmation", choices=["blind","confirmation","dca"])
    s.add_argument("--size", type=float, default=100)
    s.add_argument("--range-locked", action="store_true")
    s.add_argument("--note", default=""); s.set_defaults(f=cmd_open)

    s = sub.add_parser("mark"); s.add_argument("--id", type=int); s.set_defaults(f=cmd_mark)

    s = sub.add_parser("check"); s.add_argument("--id", type=int)
    s.add_argument("--tf", default="1d"); s.add_argument("--bars", type=int, default=60)
    s.set_defaults(f=cmd_check)

    s = sub.add_parser("close"); s.add_argument("id", type=int)
    s.add_argument("--price", type=float, required=True)
    s.add_argument("--reason", default=""); s.set_defaults(f=cmd_close)

    s = sub.add_parser("list"); s.add_argument("--all", action="store_true"); s.set_defaults(f=cmd_list)
    s = sub.add_parser("stats"); s.set_defaults(f=cmd_stats)
    s = sub.add_parser("grade"); s.add_argument("id", type=int); s.set_defaults(f=cmd_grade)

    a = p.parse_args()
    a.f(a)

if __name__ == "__main__":
    main()
