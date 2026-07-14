#!/usr/bin/env python3
"""
DMC BACKTEST HARNESS — built to try to FALSIFY the method, not to flatter it.

A backtest that just replays the rules and prints a return is worse than useless: with enough
knobs, anything looks profitable on the data you tuned it on. This harness is deliberately
adversarial. Six things it does that a naive backtest doesn't:

  1. OUT-OF-SAMPLE SPLIT   Rules are examined on the in-sample era, then run untouched on data
                           they never saw. Only the OOS number is allowed to mean anything.
  2. REAL COSTS            Commission + slippage on entry and exit. Free backtests lie.
  3. REGIME BREAKDOWN      Bull / bear / chop, tagged by 200d trend and realized vol. A system
                           that only works in one regime has not been tested, it has been lucky.
  4. BOOTSTRAP CIs         Resample the trade sequence 10,000x -> confidence interval on
                           expectancy, and the DISTRIBUTION of max drawdown you should expect.
  5. PARAMETER SENSITIVITY Sweep the thresholds. If the good result sits on a knife-edge while
                           its neighbours are negative, that is curve-fit, not edge.
  6. BENCHMARK             vs buy-and-hold. Beating zero is not the bar. Beating SPY is.

Usage:
  python3 backtest.py                        # full run, default params
  python3 backtest.py --split 2022-01-01     # in-sample before, out-of-sample after
  python3 backtest.py --sweep                # parameter sensitivity grid
  python3 backtest.py --costs 0              # frictionless (to see what costs actually cost you)
"""
import json, os, math, random, argparse, statistics as st
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
random.seed(7)

P = {  # the mechanization. DO NOT tune these to make the curve pretty.
    "decisive": 0.50,      # body / range for a "decisive" close
    "chop_atr": 0.75,      # range-lock filter
    "stop_buf": 0.25,      # ATR buffer beyond the level
    "target_R": 2.0,       # fallback target if no next level
    "horizon":  15,        # bars before marking out
    "risk_pct": 0.5,
    "equity":   200_000.0,
    "max_dd":   10.0,
    "max_pos":  4,
    "commission_per_share": 0.005,
    "slippage_bps": 2.0,   # each side
}

def load():
    raw = json.load(open(os.path.join(HERE, "data", "candles.json")))
    return {s: [{"t":r[0],"o":r[1],"h":r[2],"l":r[3],"c":r[4]} for r in v] for s, v in raw.items()}

def atr(bs, i, n=14):
    trs = [max(bs[k]["h"]-bs[k]["l"], abs(bs[k]["h"]-bs[k-1]["c"]), abs(bs[k]["l"]-bs[k-1]["c"]))
           for k in range(max(1, i-n+1), i+1)]
    return sum(trs)/len(trs) if trs else 0.0

def sma(bs, i, n):
    if i < n: return None
    return sum(b["c"] for b in bs[i-n+1:i+1]) / n

def regime(bs, i):
    """bull / bear / chop from 200d trend slope + price vs MA."""
    m_now, m_prev = sma(bs, i, 200), sma(bs, i-20, 200)
    if m_now is None or m_prev is None: return "n/a"
    slope = (m_now - m_prev) / m_prev * 100
    above = bs[i]["c"] > m_now
    if slope > 1.0 and above:  return "bull"
    if slope < -1.0 and not above: return "bear"
    return "chop"

def levels(bs, i):
    p = bs[i-1]
    wk = bs[max(0, i-5):i]
    lv = [p["h"], p["l"], p["c"]]
    if wk: lv += [max(b["h"] for b in wk), min(b["l"] for b in wk), wk[-1]["c"]]
    return sorted(set(round(x, 4) for x in lv))

def cost(px, qty, p):
    return qty * p["commission_per_share"] + abs(px) * qty * p["slippage_bps"] / 10_000

def trades_for(sym, bs, p, start=None, end=None):
    out = []
    for i in range(210, len(bs) - 2):                 # 210 = 200d MA warmup
        d = bs[i]["t"]
        if start and d < start: continue
        if end and d >= end: continue
        a = atr(bs, i)
        if a <= 0: continue
        t, prev = bs[i], bs[i-1]
        rng = t["h"] - t["l"]
        if rng <= 0 or abs(t["c"]-t["o"])/rng < p["decisive"]: continue
        if i >= 11 and abs(t["c"] - bs[i-10]["c"]) < p["chop_atr"] * atr(bs, i, 10): continue

        lv = levels(bs, i)
        best = None
        for L in lv:
            up = t["c"] > L and prev["c"] <= L
            dn = t["c"] < L and prev["c"] >= L
            if up or dn:
                dist = abs(t["c"] - L)
                if best is None or dist < best[2]:
                    best = ("long" if up else "short", L, dist)
        if not best: continue
        side, L, _ = best
        e = bs[i+1]["o"]
        stop = L - p["stop_buf"]*a if side == "long" else L + p["stop_buf"]*a
        R = (e - stop) if side == "long" else (stop - e)
        if R <= 0: continue
        if side == "long":
            ups = [x for x in lv if x > e]
            tgt = min(ups) if ups else e + p["target_R"]*R
        else:
            dns = [x for x in lv if x < e]
            tgt = max(dns) if dns else e - p["target_R"]*R
        if abs(tgt - e) / R < 1.0: continue          # target must beat the stop

        exit_px, exit_d, why = None, None, None
        for k in range(i+1, min(i+1+p["horizon"], len(bs))):
            b = bs[k]
            if side == "long":
                if b["l"] <= stop: exit_px, why = stop, "stop"; exit_d = b["t"]; break
                if b["h"] >= tgt:  exit_px, why = tgt,  "target"; exit_d = b["t"]; break
            else:
                if b["h"] >= stop: exit_px, why = stop, "stop"; exit_d = b["t"]; break
                if b["l"] <= tgt:  exit_px, why = tgt,  "target"; exit_d = b["t"]; break
        if exit_px is None:
            b = bs[min(i+p["horizon"], len(bs)-1)]
            exit_px, exit_d, why = b["c"], b["t"], "timeout"
        out.append({"sym":sym,"date":bs[i+1]["t"],"exit_date":exit_d,"side":side,
                    "entry":e,"stop":stop,"target":tgt,"exit":exit_px,"R_unit":R,
                    "why":why,"regime":regime(bs, i)})
    return out

def run(C, p, start=None, end=None):
    tr = []
    for s, bs in C.items():
        tr += trades_for(s, bs, p, start, end)
    tr.sort(key=lambda x: x["date"])

    eq, peak, mdd, curve, open_n = p["equity"], p["equity"], 0.0, [], {}
    for t in tr:
        risk = eq * p["risk_pct"]/100
        qty  = risk / t["R_unit"]
        gross = (t["exit"]-t["entry"])*qty if t["side"]=="long" else (t["entry"]-t["exit"])*qty
        fees  = cost(t["entry"], qty, p) + cost(t["exit"], qty, p)
        pl = gross - fees
        t["qty"], t["pl"], t["fees"] = qty, pl, fees
        t["R"] = pl / risk if risk else 0
        eq += pl
        peak = max(peak, eq)
        mdd = max(mdd, (peak-eq)/peak*100)
        curve.append({"date": t["exit_date"], "equity": eq})
        if eq <= p["equity"]*(1-p["max_dd"]/100):
            t["halted"] = True
    return tr, eq, mdd, curve

def stats(tr, eq, mdd, p, label):
    if not tr: return print(f"{label}: no trades")
    rs = [t["R"] for t in tr]
    w = [r for r in rs if r > 0]
    n = len(rs); mean = sum(rs)/n; sd = st.pstdev(rs) or 1e-9
    se = sd/math.sqrt(n)
    gw = sum(t["pl"] for t in tr if t["pl"]>0); gl = abs(sum(t["pl"] for t in tr if t["pl"]<=0))
    pf = gw/gl if gl else float("inf")
    fees = sum(t["fees"] for t in tr)
    print(f"\n{label}")
    print(f"  trades          {n}")
    print(f"  win rate        {len(w)/n*100:.1f}%")
    print(f"  expectancy      {mean:+.3f} R    95% CI [{mean-1.96*se:+.3f}, {mean+1.96*se:+.3f}]")
    print(f"  profit factor   {pf:.2f}")
    print(f"  total           {sum(rs):+.1f} R")
    print(f"  equity          ${eq:,.0f}   ({(eq/p['equity']-1)*100:+.2f}%)")
    print(f"  max drawdown    {mdd:.2f}%")
    print(f"  costs paid      ${fees:,.0f}")
    return {"n":n,"exp":mean,"ci":[mean-1.96*se, mean+1.96*se],"pf":pf,
            "eq":eq,"mdd":mdd,"wr":len(w)/n*100}

def bootstrap(tr, p, iters=10000):
    rs = [t["R"] for t in tr]
    if len(rs) < 10: return
    exps, dds = [], []
    for _ in range(iters):
        s = [random.choice(rs) for _ in rs]
        exps.append(sum(s)/len(s))
        eq = peak = 1.0; dd = 0.0
        for r in s:
            eq *= (1 + r*p["risk_pct"]/100)
            peak = max(peak, eq); dd = max(dd, (peak-eq)/peak*100)
        dds.append(dd)
    exps.sort(); dds.sort()
    lo, hi = exps[int(.025*iters)], exps[int(.975*iters)]
    print(f"\n  BOOTSTRAP (10k resamples of the trade sequence)")
    print(f"    expectancy 95%   [{lo:+.3f}, {hi:+.3f}] R")
    print(f"    P(expectancy>0)  {sum(1 for e in exps if e>0)/iters*100:.1f}%")
    print(f"    max drawdown     median {dds[iters//2]:.1f}%   95th pct {dds[int(.95*iters)]:.1f}%")
    print(f"    P(hit the {p['max_dd']}% halt)  {sum(1 for d in dds if d>=p['max_dd'])/iters*100:.1f}%")

def by_regime(tr):
    print("\n  BY REGIME")
    for g in ("bull","bear","chop"):
        sub = [t["R"] for t in tr if t["regime"]==g]
        if not sub: continue
        w = len([r for r in sub if r>0])/len(sub)*100
        print(f"    {g:<6} n={len(sub):<5} win {w:5.1f}%   expectancy {sum(sub)/len(sub):+.3f} R")

def benchmark(C, start, end):
    print("\n  BENCHMARK — buy & hold")
    for s, bs in C.items():
        w = [b for b in bs if (not start or b["t"]>=start) and (not end or b["t"]<end)]
        if len(w) > 1:
            print(f"    {s:<6} {(w[-1]['c']/w[0]['c']-1)*100:+7.1f}%   ({w[0]['t']} -> {w[-1]['t']})")

def sweep(C, p, start, end):
    print("\nPARAMETER SENSITIVITY — if only one cell is green, it is curve-fit, not edge\n")
    print(f"{'decisive':>9}{'stopbuf':>9}" + "".join(f"{t:>9}" for t in ("exp R","n","PF")))
    print("-"*45)
    green = 0; cells = 0
    for dec in (0.35, 0.50, 0.65):
        for buf in (0.10, 0.25, 0.50):
            q = dict(p); q["decisive"]=dec; q["stop_buf"]=buf
            tr, eq, mdd, _ = run(C, q, start, end)
            if not tr: continue
            rs=[t["R"] for t in tr]; e=sum(rs)/len(rs)
            gw=sum(t["pl"] for t in tr if t["pl"]>0); gl=abs(sum(t["pl"] for t in tr if t["pl"]<=0))
            pf=gw/gl if gl else 0
            cells += 1; green += (e > 0)
            print(f"{dec:>9.2f}{buf:>9.2f}{e:>+9.3f}{len(rs):>9}{pf:>9.2f}")
    print("-"*45)
    print(f"{green}/{cells} parameter combinations are profitable.")
    if cells and green/cells < 0.5:
        print("Most of the parameter space LOSES. Any winner here is a lottery ticket, not an edge.")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", default=None, help="date splitting in-sample / out-of-sample")
    ap.add_argument("--sweep", action="store_true")
    ap.add_argument("--costs", type=float, default=None, help="override slippage bps (0 = frictionless)")
    a = ap.parse_args()

    p = dict(P)
    if a.costs is not None:
        p["slippage_bps"] = a.costs
        p["commission_per_share"] = 0.0 if a.costs == 0 else p["commission_per_share"]

    C = load()
    span = f"{min(b[0]['t'] for b in C.values())} -> {max(b[-1]['t'] for b in C.values())}"
    bars = sum(len(v) for v in C.values())
    print(f"\nDMC BACKTEST   symbols={list(C)}   bars={bars}   span {span}")
    print(f"costs: {p['commission_per_share']}/share + {p['slippage_bps']}bps each side")
    if bars < 2500:
        print("\n*** WARNING: fewer than ~2500 bars total. This is NOT enough for a backtest. ***")
        print("*** Run fetch.py with an API key for 10+ years before believing any number here. ***")

    if a.sweep:
        sweep(C, p, None, a.split); raise SystemExit

    if a.split:
        tr, eq, mdd, _ = run(C, p, None, a.split)
        s1 = stats(tr, eq, mdd, p, f"IN-SAMPLE  (before {a.split})")
        if tr: by_regime(tr)
        tr2, eq2, mdd2, _ = run(C, p, a.split, None)
        s2 = stats(tr2, eq2, mdd2, p, f"OUT-OF-SAMPLE  (from {a.split})  <-- the only number that counts")
        if tr2: by_regime(tr2); bootstrap(tr2, p)
        benchmark(C, a.split, None)
        if s1 and s2:
            print(f"\n  DEGRADATION  in-sample {s1['exp']:+.3f}R -> out-of-sample {s2['exp']:+.3f}R")
            if s1["exp"] > 0 and s2["exp"] <= 0:
                print("  The edge did not survive contact with unseen data. That is the usual outcome.")
    else:
        tr, eq, mdd, _ = run(C, p)
        s = stats(tr, eq, mdd, p, "FULL SAMPLE (in-sample — treat with suspicion)")
        if tr: by_regime(tr); bootstrap(tr, p)
        benchmark(C, None, None)

    print("\nNo real orders. Simulated. Not financial advice.\n")
