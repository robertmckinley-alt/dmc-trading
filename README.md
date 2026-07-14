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

## Current state of the simulation

Seeded with real daily SPY/QQQ bars (2026-04-30 → 2026-07-13), rules run forward:

| | |
|---|---|
| Closed trades | **6** |
| Win / loss | 1W / 5L |
| Expectancy | **−0.50R** |
| 95% CI on expectancy | **[−1.39R, +0.39R]** |
| Equity | $197,653 from $200,000 |
| Max drawdown | 2.31% (limit 10%) |

It lost money on this sample — and **six trades tells you nothing.** The confidence interval
straddles zero: this is statistically indistinguishable from a coin flip. At the observed variance
you would need roughly **300 trades** to resolve expectancy to ±0.10R.

The thresholds have **not** been tuned to make the curve look better. Tuning rules to fit past data
is curve-fitting, and it is the most reliable way to lose real money later. The ugly number stays.

Slippage and commissions are **not** modelled. Live results would be worse.

---

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
