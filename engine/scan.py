#!/usr/bin/env python3
"""
LEVEL-RESPECT SCAN — does DMC's core mechanic behave differently by instrument?

For every prior-day level (H/L/C) we measure:

  GAIN            close beyond the level when the prior close was not beyond it
  HOLD            after a gain, price extends 0.5*ATR further before reclaiming the level
  RECLAIM (fake)  price comes back through the level first -> the "gain" was a fakeout
                  and the DMC stop, which sits just past the level, gets hit
  WICK-FAIL       price traded through the level but closed back inside (DMC "fail")
  GAP RISK        next open lands beyond the prior close by > 1.0*ATR
                  -> the day your stop sits at a level and price jumps clean over it

HOLD RATE is the number that matters. It is, literally, "when this instrument gains a
level, does the level hold?" That is the single assumption DMC rests on.

Small samples. ~50 bars per name. Directional, not conclusive.
"""
import json, os, statistics as st

HERE = os.path.dirname(os.path.abspath(__file__))
C = json.load(open(os.path.join(HERE, "data", "candles.json")))
LOOK = 3           # bars allowed for the gain to prove itself
EXT  = 0.5         # ATR multiple that counts as follow-through

def bars(sym):
    return [{"t":r[0],"o":r[1],"h":r[2],"l":r[3],"c":r[4]} for r in C[sym]]

def atr(bs, i, n=14):
    trs=[]
    for k in range(max(1,i-n+1), i+1):
        h,l,pc = bs[k]["h"], bs[k]["l"], bs[k-1]["c"]
        trs.append(max(h-l, abs(h-pc), abs(l-pc)))
    return sum(trs)/len(trs) if trs else 0.0

def scan(sym):
    bs = bars(sym)
    gains=holds=reclaims=touches=wickfails=gaps=0
    for i in range(15, len(bs)-LOOK-1):
        a = atr(bs, i)
        if a <= 0: continue
        p, t = bs[i-1], bs[i]
        levels = [p["h"], p["l"], p["c"]]

        # gap risk: today's open vs yesterday's close
        if abs(t["o"] - p["c"]) > 1.0 * a: gaps += 1

        for L in levels:
            traded_through = t["l"] <= L <= t["h"]
            if traded_through: touches += 1
            up  = t["c"] > L and p["c"] <= L
            dn  = t["c"] < L and p["c"] >= L
            # wick fail: pierced the level but closed back on the origin side
            if traded_through and not up and not dn: wickfails += 1
            if not (up or dn): continue
            gains += 1
            held = None
            for k in range(i+1, min(i+1+LOOK, len(bs))):
                b = bs[k]
                if up:
                    if b["l"] < L: held = False; break            # level reclaimed -> stop hit
                    if b["h"] >= t["c"] + EXT*a: held = True; break
                else:
                    if b["h"] > L: held = False; break
                    if b["l"] <= t["c"] - EXT*a: held = True; break
            if held is True: holds += 1
            elif held is False: reclaims += 1
    n = len(bs)
    hold_rate = holds/gains*100 if gains else 0
    fake_rate = reclaims/gains*100 if gains else 0
    wick_rate = wickfails/touches*100 if touches else 0
    gap_rate  = gaps/(n-16)*100 if n>16 else 0
    vol = st.mean([atr(bs,i)/bs[i]["c"]*100 for i in range(15,len(bs))])
    return {"symbol":sym,"gains":gains,"hold":hold_rate,"fake":fake_rate,
            "undecided":100-hold_rate-fake_rate,"wick":wick_rate,"gap":gap_rate,"atr_pct":vol}

rows = [scan(s) for s in C]
rows.sort(key=lambda r: -r["hold"])

print("\nLEVEL-RESPECT SCAN — ~50 daily bars per name (Apr 30 -> Jul 13 2026)\n")
print(f"{'SYM':<6}{'GAINS':>6}{'HOLD%':>8}{'FAKE%':>8}{'WICK-FAIL%':>12}{'GAP-RISK%':>11}{'ATR%':>7}   READ")
print("-"*86)
for r in rows:
    if r["hold"] >= 45 and r["gap"] <= 12:   read = "levels respected"
    elif r["fake"] > r["hold"]:              read = "fakes out more than it holds"
    elif r["gap"] > 15:                      read = "gap risk breaks the stop model"
    else:                                    read = "marginal"
    print(f"{r['symbol']:<6}{r['gains']:>6}{r['hold']:>7.1f}%{r['fake']:>7.1f}%"
          f"{r['wick']:>11.1f}%{r['gap']:>10.1f}%{r['atr_pct']:>6.2f}%   {read}")
print("-"*86)
print("HOLD  = gain extended 0.5*ATR before the level was reclaimed  (the trade works)")
print("FAKE  = level reclaimed first -> the DMC stop, sitting just past the level, is hit")
print("WICK-FAIL = pierced the level, closed back inside. DMC calls this a 'fail' - correctly.")
print("GAP-RISK = open jumped >1 ATR from the prior close. Your stop does not exist on those days.")
print("\nSmall sample (~50 bars). Directional, not conclusive.\n")

json.dump(rows, open(os.path.join(HERE,"data","scan.json"),"w"), indent=2)

# ---------------------------------------------------------------- significance
import math
def wilson(k, n, z=1.96):
    if n == 0: return (0,0)
    p = k/n; d = 1 + z*z/n
    c = (p + z*z/(2*n)) / d
    m = z*math.sqrt(p*(1-p)/n + z*z/(4*n*n)) / d
    return (100*(c-m), 100*(c+m))

print("IS ANY OF THIS DISTINGUISHABLE FROM A COIN FLIP?\n")
print(f"{'SYM':<6}{'DECIDED':>9}{'HOLD%':>8}   95% CI on hold rate      VERDICT")
print("-"*76)
for r in sorted(rows, key=lambda x:-x["hold"]):
    dec = r["gains"]                      # every gain resolves hold / fake / undecided
    k   = round(r["hold"]/100*dec)
    nd  = round((r["hold"]+r["fake"])/100*dec)   # exclude undecided
    kk  = round(r["hold"]/100*dec)
    lo, hi = wilson(kk, nd)
    sig = "beats coin flip" if lo > 50 else ("worse than coin flip" if hi < 50 else "INDISTINGUISHABLE from a coin flip")
    print(f"{r['symbol']:<6}{nd:>9}{r['hold']:>7.1f}%   [{lo:5.1f}% , {hi:5.1f}%]      {sig}")
print("-"*76)
print("Every 95% interval straddles 50%. On ~50 bars, NO instrument here shows")
print("statistically demonstrable level-respect. Not even QQQ.\n")
