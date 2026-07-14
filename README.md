# DMC Trading — analysis skills + paper-trading simulator

A level-based trading methodology ("Dumb Money Concepts") encoded as two Claude Code skills,
plus a **simulated** paper-trading engine and a dashboard.

**No broker. No exchange. No order endpoint. Nothing here can place a real trade, by design.**

---

## Read this before you read the numbers

DMC's rules contain genuinely subjective terms — *significant level*, *decisive close*, *clean gain*.
Code cannot be subjective, so the engine pins them to fixed thresholds.

**These results test one mechanization of DMC, not the method as a skilled trader would apply it.**
A bad result is not proof DMC fails. A good one is not proof it works.

Win-rate and performance claims in the original source material are the creator's own promotional
statements and are unverified. This repo is educational. It is not financial advice.

---

## Current state — the backtest is in, and it is not good

10 years, 10 instruments, 25,130 bars, **5,094 trades**. Full results: [BACKTEST-RESULTS.md](BACKTEST-RESULTS.md)

| Out-of-sample (2022→) | |
|---|---|
| Trades | 2,524 |
| Win rate | 33.0% |
| Expectancy | **−0.160 R**, 95% CI [−0.226, −0.094] |
| P(expectancy > 0) | **0.0%** |
| Equity from $200k | **$24,042 (−88%)** |
| Buy & hold SPY, same window | **+57%** |

**The confidence interval excludes zero.** This is not "no edge found" — the mechanized rules have
a statistically significant *negative* expectancy. It loses in bull, bear and chop. **0 of 9**
parameter settings are profitable. Removing all costs still leaves it negative.

**What this does not prove:** that discretionary DMC — human-chosen levels, confluence zones,
selective entries, intraday — loses. The bot takes ~500 trades/year; a trader takes a handful.
That gap is unbridgeable by code. But note that "the discretionary version works" is also the
unfalsifiable defense of every system that fails a backtest, and it should be treated with the
suspicion that implies.

---

## Research

- [BACKTEST-RESULTS.md](BACKTEST-RESULTS.md) — mechanized DMC, 10y, 5,094 trades: significant negative expectancy
- [FINDINGS.md](FINDINGS.md) — level-respect and payoff-asymmetry scans
- [OVERNIGHT.md](OVERNIGHT.md) — the overnight effect: real anomaly, dead strategy
- [OVERNIGHT-STOCKS.md](OVERNIGHT-STOCKS.md) — does it work on stocks? No, worse. Earnings decomposition.
- [BACKTEST.md](BACKTEST.md) — how to backtest without fooling yourself

## Layout

```
skills/
  dumb-money-concepts/     # the method — chart/setup analysis, analysis-only
    SKILL.md
    dmc-reference.md
  dmc-paper-trading/       # simulated journal + dashboard
    SKILL.md
    scripts/paper.py       # standalone CLI: levels, open, mark, check, close, stats, grade
    references/ledger-schema.md
engine/
  engine.py                # DMC rules engine (backtest + forward paper run)
  site.py                  # builds the dashboard
  data/candles.json        # daily OHLC, oldest first
  data/results.json        # engine output
docs/
  index.html               # the dashboard (GitHub Pages)
```

## Run it

```bash
python3 engine/engine.py     # evaluate levels, manage simulated positions
python3 engine/site.py       # rebuild docs/index.html
```

Stdlib only. No dependencies.

## The encoded rules

| Rule | Implementation |
|---|---|
| Level | Prior day H/L/C and prior week H/L/C |
| Gain | Close beyond the level when the prior close was not beyond it |
| Fail | Wick beyond, close not beyond — never an entry |
| Decisive | Body ≥ 50% of the candle's range |
| Range lock | \|close − close[−10]\| < 0.75 × ATR(10) → stand aside |
| Entry | **Next session's open** — you cannot fill at the signal close |
| Stop | Far side of the traded level + 0.25 × ATR(14) |
| Target | Next level in the trade's direction (must beat the stop, else no trade) |
| Tie | If a bar spans stop and target, the **stop** is taken |

## Risk configuration

$200,000 start · 0.5% risk per trade · max 4 concurrent · max 2% open risk ·
**hard halt at 10% drawdown ($180,000)**.

## Install the skills

```bash
cp -r skills/dumb-money-concepts  ~/.claude/skills/
cp -r skills/dmc-paper-trading    ~/.claude/skills/
```

---

*Simulated only. Not financial advice. No real orders are placed and none can be.*
