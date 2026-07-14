#!/usr/bin/env python3
"""
PAYOFF-ASYMMETRY SCAN — the test that actually decides whether DMC can work.

The level-respect scan showed hold rates near 50% everywhere: DMC gains a level and it's
roughly a coin flip whether the level holds. That alone does NOT condemn the method — a
coin flip is profitable if winners run further than losers cost.

So: after a gain, how far does price actually run before it turns?

For every gain event:
  entry = NEXT session's open (you cannot fill at the signal close)
  stop  = far side of the level + 0.25*ATR   -> this defines 1R
  then walk forward up to 15 bars and record:
     MAE  = worst adverse excursion, in R   (how much heat you eat)
     MFE  = best favorable excursion, in R  (how much was actually on the table)
  and simulate fixed targets at 1R, 1.5R, 2R, 2.5R, 3R.
  Conservative: if a bar spans both stop and target, the STOP is taken.

If DMC has an edge, it shows up HERE - as expectancy that turns positive at some target
multiple. If expectancy is negative at EVERY multiple, no exit rule saves it.
"""
import json, os, statistics as st, math

HERE = os.path.dirname(os.path.abspath(__file__))
C = json.load(open(os.path.join(HERE, "data", "candles.json")))
BUF, HORIZON = 0.25, 15
TARGETS = [1.0, 1.5, 2.0, 2.5, 3.0]

def bars(s): return [{"t":r[0],"o":r[1],"h":r[2],"l":r[3],"c":r[4]} for r in C[s]]
def atr(bs,i,n=14):
    trs=[max(bs[k]["h"]-bs[k]["l"], abs(bs[k]["h"]-bs[k-1]["c"]), abs(bs[k]["l"]-bs[k-1]["c"]))
         for k in range(max(1,i-n+1), i+1)]
    return sum(trs)/len(trs) if trs else 0.0

def events(sym):
    bs, out = bars(sym), []
    for i in range(15, len(bs)-2):
        a = atr(bs,i)
        if a<=0: continue
        p,t = bs[i-1], bs[i]
        rng = t["h"]-t["l"]
        if rng<=0 or abs(t["c"]-t["o"])/rng < 0.5: continue      # decisive closes only
        for L in (p["h"], p["l"], p["c"]):
            up = t["c"]>L and p["c"]<=L
            dn = t["c"]<L and p["c"]>=L
            if not(up or dn): continue
            e = bs[i+1]["o"]
            stop = L - BUF*a if up else L + BUF*a
            R = (e-stop) if up else (stop-e)
            if R <= 0: continue                                   # entry already past the stop
            mae=mfe=0.0; res={T:None for T in TARGETS}
            for k in range(i+1, min(i+1+HORIZON, len(bs))):
                b=bs[k]
                if up:
                    adv=(b["l"]-e)/R; fav=(b["h"]-e)/R
                else:
                    adv=(e-b["h"])/R; fav=(e-b["l"])/R
                mae=min(mae,adv); mfe=max(mfe,fav)
                for T in TARGETS:
                    if res[T] is not None: continue
                    if adv <= -1.0: res[T] = -1.0                 # stop first (conservative)
                    elif fav >= T:  res[T] = T
            # unresolved at horizon -> mark out at last close
            for T in TARGETS:
                if res[T] is None:
                    b=bs[min(i+HORIZON,len(bs)-1)]
                    res[T] = ((b["c"]-e)/R) if up else ((e-b["c"])/R)
            out.append({"sym":sym,"mae":mae,"mfe":mfe,"res":res})
    return out

allev=[]
per={}
for s in C:
    ev=events(s); per[s]=ev; allev+=ev

def line(name, ev):
    if not ev: return
    mfes=[e["mfe"] for e in ev]; maes=[e["mae"] for e in ev]
    row=f"{name:<8}{len(ev):>6}"
    for T in TARGETS:
        rs=[e["res"][T] for e in ev]
        row+=f"{sum(rs)/len(rs):>+8.2f}"
    row+=f"{st.median(mfes):>9.2f}{st.median(maes):>9.2f}"
    print(row)

print("\nPAYOFF-ASYMMETRY SCAN — expectancy (R per trade) at each fixed target\n")
hdr=f"{'SYM':<8}{'N':>6}" + "".join(f"{str(T)+'R':>8}" for T in TARGETS) + f"{'med MFE':>9}{'med MAE':>9}"
print(hdr); print("-"*len(hdr))
for s in C: line(s, per[s])
print("-"*len(hdr))
line("POOLED", allev)
print("-"*len(hdr))

rs1=[e["res"][2.0] for e in allev]
n=len(rs1); mean=sum(rs1)/n; sd=st.pstdev(rs1); se=sd/math.sqrt(n)
print(f"\nPooled, target = 2R:  n={n}   expectancy {mean:+.3f}R"
      f"   95% CI [{mean-1.96*se:+.3f}, {mean+1.96*se:+.3f}]")

best=None
for T in TARGETS:
    rs=[e["res"][T] for e in allev]; m=sum(rs)/len(rs)
    if best is None or m>best[1]: best=(T,m)
print(f"Best fixed target on this data: {best[0]}R  ->  expectancy {best[1]:+.3f}R")

mfes=[e["mfe"] for e in allev]
for T in TARGETS:
    hit=sum(1 for m in mfes if m>=T)/len(mfes)*100
    print(f"  MFE reached {T}R at some point: {hit:5.1f}% of gains")

print("\nNOTE: the 'best target' above is chosen BY LOOKING AT THIS DATA. That is curve-fitting.")
print("It is an upper bound on what you could have got, not an estimate of what you will get.\n")
json.dump({"n":len(allev),"targets":TARGETS,
           "pooled":{str(T):sum(e['res'][T] for e in allev)/len(allev) for T in TARGETS}},
          open(os.path.join(HERE,"data","payoff.json"),"w"), indent=2)
