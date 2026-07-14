#!/usr/bin/env python3
"""Generate the DMC paper-trading dashboard (single self-contained HTML)."""
import json, os, math, statistics as st
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
R = json.load(open(os.path.join(HERE, "data", "results.json")))
CFG, curve = R["config"], R["curve"]
trades = sorted(R["trades"], key=lambda t: t["id"])
closed = [t for t in trades if t["status"] == "closed"]
openp  = [t for t in trades if t["status"] == "open"]
rs = [t["r"] for t in closed]
wins = [r for r in rs if r > 0]; losses = [r for r in rs if r <= 0]
n = len(rs)

start = CFG["start_equity"]; final = R["final_equity"]
maxdd = max(c["dd_pct"] for c in curve) if curve else 0
curdd = curve[-1]["dd_pct"] if curve else 0
wr = (len(wins)/n*100) if n else 0
avg_w = (sum(wins)/len(wins)) if wins else 0
avg_l = (sum(losses)/len(losses)) if losses else 0
exp   = (sum(rs)/n) if n else 0
gross_w = sum(t["pl"] for t in closed if t["pl"] > 0)
gross_l = abs(sum(t["pl"] for t in closed if t["pl"] <= 0))
pf = (gross_w/gross_l) if gross_l else float("inf")
sd = st.pstdev(rs) if n > 1 else 0
se = sd/math.sqrt(n) if n else 0
ci_lo, ci_hi = exp - 1.96*se, exp + 1.96*se
# trades needed to resolve expectancy to +/- 0.10R at 95%
need = int((1.96*sd/0.10)**2) if sd else 0
pl_total = final - start

comp = []
for t in trades:
    ok_stop = (t["stop"] < t["level"]) if t["side"] == "long" else (t["stop"] > t["level"])
    ok_rr = t["planned_rr"] >= 1.0
    comp.append(ok_stop and ok_rr)
compliance = (sum(comp)/len(comp)*100) if comp else 0

def j(x): return json.dumps(x)
labels = [c["date"] for c in curve]
eq = [c["equity"] for c in curve]
dd = [-c["dd_pct"] for c in curve]

# R histogram buckets
buckets = ["<-2","-2..-1","-1..0","0..1","1..2",">2"]
def bkt(r):
    if r < -2: return 0
    if r < -1: return 1
    if r <= 0: return 2
    if r <= 1: return 3
    if r <= 2: return 4
    return 5
hist = [0]*6
for r in rs: hist[bkt(r)] += 1

daily_pl = {}
for t in closed:
    daily_pl[t["exit_date"]] = daily_pl.get(t["exit_date"], 0) + t["pl"]
dp_lab = sorted(daily_pl)
dp_val = [round(daily_pl[d],2) for d in dp_lab]

rows = ""
for t in trades:
    r = f"{t['r']:+.2f}" if t.get("r") is not None else "—"
    pl = f"${t['pl']:+,.0f}" if t.get("pl") is not None else "—"
    cls = "win" if (t.get("r") or 0) > 0 else ("loss" if t["status"]=="closed" else "openrow")
    ex = t.get("exit") or "—"
    rows += f"""<tr class="{cls}">
      <td>{t['id']}</td><td class="sym">{t['symbol']}</td>
      <td><span class="side {t['side']}">{t['side'].upper()}</span></td>
      <td>{t['signal_date']}</td><td class="lvl">{t['level']}<em>{t['level_kind']}</em></td>
      <td>{t['entry']}</td><td>{t['stop']}</td><td>{t['target']}</td>
      <td>{t['planned_rr']}</td><td>{ex}</td>
      <td>{t.get('reason') or 'open'}</td><td class="r">{r}</td><td class="pl">{pl}</td></tr>"""

verdict = ("NOT ENOUGH DATA" if n < 30 else ("EDGE NOT SHOWN" if ci_hi < 0 else
           ("POSITIVE EDGE" if ci_lo > 0 else "INCONCLUSIVE")))

HTML = f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<title>DMC Paper Trading — Live Tracker</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
<style>
*{{box-sizing:border-box}}
body{{margin:0;background:#0b0d12;color:#e6e9ef;font:14px/1.5 -apple-system,BlinkMacSystemFont,'Segoe UI',Inter,sans-serif}}
.wrap{{max-width:1240px;margin:0 auto;padding:28px 20px 80px}}
h1{{font-size:26px;margin:0 0 4px;letter-spacing:-.02em}}
.sub{{color:#7c8698;font-size:13px;margin-bottom:22px}}
.banner{{background:#1a1206;border:1px solid #7a4d0a;color:#f0b854;padding:12px 16px;border-radius:10px;margin-bottom:20px;font-size:13px}}
.banner b{{color:#ffd489}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(168px,1fr));gap:12px;margin-bottom:20px}}
.card{{background:#12151d;border:1px solid #1f2530;border-radius:12px;padding:14px 16px}}
.card .k{{color:#7c8698;font-size:11px;text-transform:uppercase;letter-spacing:.07em}}
.card .v{{font-size:24px;font-weight:600;margin-top:5px;letter-spacing:-.02em}}
.card .n{{font-size:11px;color:#6b7486;margin-top:2px}}
.pos{{color:#3ddc84}} .neg{{color:#ff5f6d}} .warn{{color:#f0b854}} .mut{{color:#7c8698}}
.panel{{background:#12151d;border:1px solid #1f2530;border-radius:12px;padding:18px;margin-bottom:18px}}
.panel h2{{font-size:13px;text-transform:uppercase;letter-spacing:.08em;color:#7c8698;margin:0 0 14px}}
.two{{display:grid;grid-template-columns:1fr 1fr;gap:18px}}
@media(max-width:900px){{.two{{grid-template-columns:1fr}}}}
table{{width:100%;border-collapse:collapse;font-size:12.5px}}
th{{text-align:left;color:#7c8698;font-weight:500;padding:8px 9px;border-bottom:1px solid #1f2530;font-size:11px;text-transform:uppercase;letter-spacing:.05em}}
td{{padding:9px;border-bottom:1px solid #171b24}}
tr.win td.r,tr.win td.pl{{color:#3ddc84;font-weight:600}}
tr.loss td.r,tr.loss td.pl{{color:#ff5f6d;font-weight:600}}
tr.openrow{{background:#0f1620}} tr.openrow td{{color:#8fa6c4}}
.sym{{font-weight:600}}
.side{{padding:2px 7px;border-radius:5px;font-size:10px;font-weight:700}}
.side.long{{background:#0f3323;color:#3ddc84}} .side.short{{background:#33161a;color:#ff8a92}}
.lvl em{{display:block;font-style:normal;color:#6b7486;font-size:10.5px}}
.verdict{{font-size:22px;font-weight:700;letter-spacing:-.01em}}
.bar{{height:7px;background:#1f2530;border-radius:4px;overflow:hidden;margin-top:7px}}
.bar i{{display:block;height:100%;background:linear-gradient(90deg,#3ddc84,#26a5f5)}}
.ci{{font-family:ui-monospace,Menlo,monospace;font-size:13px;color:#9fb0c9}}
ul.notes{{margin:10px 0 0;padding-left:18px;color:#8e99ab;font-size:12.5px}}
ul.notes li{{margin-bottom:5px}}
.foot{{color:#5d6678;font-size:11.5px;text-align:center;margin-top:26px;line-height:1.7}}
</style></head><body><div class="wrap">

<h1>DMC Paper Trading — Live Tracker</h1>
<div class="sub">Simulated only · no broker connected · no real orders · generated {R['generated'][:16].replace('T',' ')} UTC</div>

<div class="banner">
<b>Read this before you read the numbers.</b> DMC's rules are partly subjective — "significant level",
"decisive close", "clean gain" are human judgment calls. This engine had to pin them to fixed thresholds
to run at all. So these results test <b>one mechanization of DMC</b>, not the method as a skilled trader
would apply it. A bad result here is not proof DMC fails; a good one is not proof it works.
</div>

<div class="grid">
  <div class="card"><div class="k">Equity</div>
    <div class="v {'pos' if pl_total>=0 else 'neg'}">${final:,.0f}</div>
    <div class="n">from ${start:,.0f} · {pl_total:+,.0f}</div></div>
  <div class="card"><div class="k">Return</div>
    <div class="v {'pos' if pl_total>=0 else 'neg'}">{pl_total/start*100:+.2f}%</div>
    <div class="n">{len(curve)} sessions</div></div>
  <div class="card"><div class="k">Max Drawdown</div>
    <div class="v {'neg' if maxdd>=CFG['max_drawdown_pct'] else 'warn' if maxdd>5 else ''}">{maxdd:.2f}%</div>
    <div class="n">limit {CFG['max_drawdown_pct']}% · now {curdd:.2f}%</div></div>
  <div class="card"><div class="k">Win Rate</div>
    <div class="v">{wr:.0f}%</div><div class="n">{len(wins)}W / {len(losses)}L</div></div>
  <div class="card"><div class="k">Expectancy</div>
    <div class="v {'pos' if exp>0 else 'neg'}">{exp:+.2f}R</div>
    <div class="n">per trade</div></div>
  <div class="card"><div class="k">Profit Factor</div>
    <div class="v {'pos' if pf>=1 else 'neg'}">{('∞' if pf==float('inf') else f'{pf:.2f}')}</div>
    <div class="n">gross W / gross L</div></div>
  <div class="card"><div class="k">Sample</div>
    <div class="v {'warn' if n<30 else ''}">{n}</div>
    <div class="n">closed trades</div></div>
  <div class="card"><div class="k">Kill Switch</div>
    <div class="v {'neg' if R['halted'] else 'pos'}">{'HALTED' if R['halted'] else 'ARMED'}</div>
    <div class="n">floor ${R['floor']:,.0f}</div></div>
</div>

<div class="panel">
  <h2>Equity curve vs. drawdown floor</h2>
  <canvas id="eq" height="94"></canvas>
</div>

<div class="two">
  <div class="panel"><h2>Underwater (drawdown %)</h2><canvas id="dd" height="150"></canvas></div>
  <div class="panel"><h2>R-multiple distribution</h2><canvas id="hist" height="150"></canvas></div>
</div>

<div class="two">
  <div class="panel"><h2>Realized P/L by day</h2><canvas id="dpl" height="150"></canvas></div>
  <div class="panel">
    <h2>Viability — the honest read</h2>
    <div class="verdict {'neg' if verdict in ('EDGE NOT SHOWN',) else 'warn' if verdict!='POSITIVE EDGE' else 'pos'}">{verdict}</div>
    <div class="bar"><i style="width:{min(100, n/30*100):.0f}%"></i></div>
    <div class="n mut" style="margin-top:6px">{n} of ~30 trades — the bare minimum before a win rate means anything at all.</div>
    <ul class="notes">
      <li>Expectancy <b>{exp:+.2f}R</b>, 95% CI <span class="ci">[{ci_lo:+.2f}, {ci_hi:+.2f}]</span> per trade.</li>
      <li>That interval {'straddles zero — the data cannot yet distinguish this from a coin flip.' if ci_lo<0<ci_hi else 'excludes zero, but on a tiny sample that is fragile.'}</li>
      <li>To pin expectancy to ±0.10R with 95% confidence you would need roughly <b>{need if need else '—'} trades</b> at the current variance.</li>
      <li>A week of daily-timeframe signals produces a handful of trades. <b>One week cannot establish viability.</b> It can only establish whether the rules were followed.</li>
      <li>DMC rule compliance across all trades: <b>{compliance:.0f}%</b> (stop on the far side of the level, target beyond the stop).</li>
    </ul>
  </div>
</div>

<div class="panel">
  <h2>Trade log — {len(trades)} total ({len(closed)} closed, {len(openp)} open)</h2>
  <table><thead><tr>
    <th>#</th><th>Sym</th><th>Side</th><th>Signal</th><th>Level gained</th><th>Entry</th>
    <th>Stop</th><th>Target</th><th>R:R</th><th>Exit</th><th>Outcome</th><th>R</th><th>P/L</th>
  </tr></thead><tbody>{rows}</tbody></table>
</div>

<div class="panel">
  <h2>Run configuration</h2>
  <ul class="notes">
    <li>Starting equity <b>${start:,.0f}</b> · max drawdown <b>{CFG['max_drawdown_pct']}%</b> (halt at ${R['floor']:,.0f}) · risk <b>{CFG['risk_per_trade_pct']}%</b> per trade · max <b>{CFG['max_concurrent']}</b> concurrent · max <b>{CFG['max_open_risk_pct']}%</b> open risk</li>
    <li>Universe: <b>{', '.join(R['symbols'])}</b> · daily candles · levels from prior day + prior week H/L/C</li>
    <li>Gain = close beyond a level when the prior close was not. Wicks never count. Decisive = body ≥ 50% of range.</li>
    <li>Range-lock filter: |close − close[−10]| &lt; 0.75 × ATR(10) → stand aside.</li>
    <li>Entry fills at the <b>next session's open</b>, never at the signal close. Stop = far side of the level + 0.25×ATR(14). Target = next level in the trade's direction.</li>
    <li>If a bar spans both stop and target, the <b>stop</b> is taken. Slippage and commissions are <b>not</b> modelled — real results would be worse.</li>
  </ul>
</div>

<div class="foot">
  Simulated paper trading. No brokerage or exchange is connected. No real orders are placed and none can be.<br>
  Not financial advice. Past simulated performance says nothing about future results.<br>
  Win-rate claims in the original DMC source material are the creator's own and remain unverified.
</div>
</div>

<script>
const G='#7c8698', GRID='#1a1f29';
Chart.defaults.color=G; Chart.defaults.borderColor=GRID; Chart.defaults.font.family='-apple-system,Segoe UI,sans-serif';
new Chart(document.getElementById('eq'),{{type:'line',data:{{labels:{j(labels)},datasets:[
 {{label:'Equity',data:{j(eq)},borderColor:'#26a5f5',backgroundColor:'rgba(38,165,245,.10)',fill:true,tension:.25,pointRadius:0,borderWidth:2}},
 {{label:'Start ${start:,.0f}',data:{j([start]*len(labels))},borderColor:'#3a4353',borderDash:[5,5],pointRadius:0,borderWidth:1,fill:false}},
 {{label:'Halt floor',data:{j([R['floor']]*len(labels))},borderColor:'#ff5f6d',borderDash:[3,3],pointRadius:0,borderWidth:1,fill:false}}
]}},options:{{plugins:{{legend:{{labels:{{boxWidth:10,font:{{size:11}}}}}}}},scales:{{x:{{grid:{{color:GRID}},ticks:{{maxTicksLimit:10,font:{{size:10}}}}}},y:{{grid:{{color:GRID}},ticks:{{callback:v=>'$'+(v/1000).toFixed(0)+'k',font:{{size:10}}}}}}}}}}}});
new Chart(document.getElementById('dd'),{{type:'line',data:{{labels:{j(labels)},datasets:[{{label:'Drawdown %',data:{j(dd)},borderColor:'#ff5f6d',backgroundColor:'rgba(255,95,109,.14)',fill:true,tension:.2,pointRadius:0,borderWidth:1.5}}]}},options:{{plugins:{{legend:{{display:false}}}},scales:{{x:{{grid:{{display:false}},ticks:{{maxTicksLimit:6,font:{{size:10}}}}}},y:{{grid:{{color:GRID}},ticks:{{callback:v=>v+'%',font:{{size:10}}}}}}}}}}}});
new Chart(document.getElementById('hist'),{{type:'bar',data:{{labels:{j(buckets)},datasets:[{{data:{j(hist)},backgroundColor:['#ff5f6d','#ff8a92','#ffb3b8','#9fe6bf','#5fd99a','#3ddc84'],borderRadius:4}}]}},options:{{plugins:{{legend:{{display:false}}}},scales:{{x:{{grid:{{display:false}},ticks:{{font:{{size:10}}}}}},y:{{grid:{{color:GRID}},ticks:{{stepSize:1,font:{{size:10}}}}}}}}}}}});
new Chart(document.getElementById('dpl'),{{type:'bar',data:{{labels:{j(dp_lab)},datasets:[{{data:{j(dp_val)},backgroundColor:{j(['#3ddc84' if v>0 else '#ff5f6d' for v in dp_val])},borderRadius:4}}]}},options:{{plugins:{{legend:{{display:false}}}},scales:{{x:{{grid:{{display:false}},ticks:{{font:{{size:10}}}}}},y:{{grid:{{color:GRID}},ticks:{{callback:v=>'$'+v,font:{{size:10}}}}}}}}}}}});
</script></body></html>"""

out = os.path.join(HERE, "dmc-dashboard.html")
open(out, "w").write(HTML)
print(f"wrote {out}  ({len(HTML):,} bytes)")
print(f"verdict: {verdict} | n={n} | exp {exp:+.2f}R | CI [{ci_lo:+.2f},{ci_hi:+.2f}] | equity ${final:,.0f} | maxDD {maxdd:.2f}%")
