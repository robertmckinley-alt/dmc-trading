# Backtest results — 10 years, 10 instruments, 5,094 trades

**Data:** daily bars, 2016-07-14 → 2026-07-14. SPY QQQ IWM AAPL NVDA TSLA JPM XOM GLD TLT.
25,130 bars. Costs: $0.005/share + 2bps slippage each side.

Reproduce: `python3 engine/backtest.py --split 2022-01-01`

---

## The result

| | In-sample (pre-2022) | **Out-of-sample (2022→)** |
|---|---|---|
| Trades | 2,570 | **2,524** |
| Win rate | 33.1% | **33.0%** |
| Expectancy | −0.174 R | **−0.160 R** |
| 95% CI | [−0.233, −0.115] | **[−0.226, −0.094]** |
| Profit factor | 0.77 | **0.79** |
| Equity (from $200k) | $19,738 | **$24,042 (−88%)** |
| Max drawdown | 91.1% | **89.7%** |

**The out-of-sample confidence interval excludes zero.** This is no longer "not enough data."
With n=2,524, the mechanized DMC rules have a **statistically significant negative expectancy.**

Bootstrap, 10,000 resamples of the out-of-sample trade sequence:

- expectancy 95% CI **[−0.227, −0.097] R**
- **P(expectancy > 0) = 0.0%**
- median max drawdown **88.7%**, 95th percentile **94.5%**
- **P(hitting the 10% halt) = 100.0%**

## It loses in every regime

| Regime | n | Win rate | Expectancy |
|---|---|---|---|
| Bull | 1,184 | 33.1% | −0.159 R |
| Bear | 377 | 31.8% | −0.141 R |
| Chop | 963 | 33.4% | −0.169 R |

This is not a strategy that "only works in trends." It's uniformly negative. There is no market
condition in ten years where these rules made money.

## There is no parameter escape hatch

| decisive | stop buffer | expectancy | n | PF |
|---|---|---|---|---|
| 0.35 | 0.10 | −0.288 | 6936 | 0.74 |
| 0.35 | 0.25 | −0.177 | 6775 | 0.72 |
| 0.35 | 0.50 | −0.062 | 6101 | 0.90 |
| 0.50 | 0.10 | −0.306 | 5214 | 0.74 |
| 0.50 | 0.25 | −0.167 | 5094 | 0.77 |
| 0.50 | 0.50 | −0.085 | 4659 | 0.87 |
| 0.65 | 0.10 | −0.172 | 3408 | 0.77 |
| 0.65 | 0.25 | −0.136 | 3348 | 0.80 |
| 0.65 | 0.50 | −0.063 | 3124 | 0.88 |

**0 of 9 parameter combinations are profitable.** Normally a sweep finds one lucky green cell you
have to be disciplined enough to ignore. Here there isn't one. The entire parameter space loses.
That is a *plateau*, which makes the finding robust rather than fragile.

## Costs are most of it — but not all of it

Frictionless (zero commission, zero slippage):

- expectancy **−0.053 R**, 95% CI **[−0.091, −0.015]** — **still excludes zero**
- equity −77% instead of −88%

So roughly two-thirds of the damage is transaction costs. But **stripping costs to zero does not
make it profitable.** The rules are negative before you pay a cent. Costs turn a bad system into a
catastrophic one; they are not the cause of the badness.

The cost bill is enormous because the mechanization takes **~500 trades a year**. Every prior-day
and prior-week high/low/close is a level, and it trades every decisive close through any of them.
That is roughly two trades a day, forever.

## The benchmark

Out-of-sample, doing nothing:

| SPY | QQQ | IWM | AAPL | NVDA | TSLA | JPM | XOM | GLD | TLT |
|---|---|---|---|---|---|---|---|---|---|
| +57% | +79% | +31% | +73% | **+604%** | −1% | +111% | +128% | +121% | −42% |

Buy SPY and go to the beach: **+57%.** Trade mechanized DMC: **−88%.**

---

## What this proves, precisely

**It proves this mechanization of DMC loses money.** Not "shows no edge" — *loses*, significantly,
across 10 years, 10 instruments, both samples, every regime, and every parameter setting tested,
with or without costs.

## What it does NOT prove — and this matters

It does **not** prove that DMC as taught, or as traded by a skilled discretionary trader, loses.
The gap between the two is real and large:

- **Selectivity.** This bot takes ~500 trades/year. It fires on *every* decisive close through
  *any* prior-day or prior-week level. A discretionary trader takes a handful of high-conviction
  setups. Selectivity is not a detail here — it's most of the method.
- **Confluence.** DMC says the good setups are where HTF and LTF levels *align*. The bot ignores
  that filter entirely.
- **Human judgment.** "Significant level" and "decisive close" are judgment calls. Code can't make
  them.
- **Timeframe.** This is daily bars. DMC is often traded intraday, where the statistics could be
  entirely different.

## But be careful with that defense

"The discretionary version still works" is also **the standard, unfalsifiable defense of every
system that fails a backtest.** It cannot be tested, which means it cannot be wrong, which is
exactly what should make you suspicious of it.

The honest position: the mechanical core of DMC — *gain a level, ride it, stop on the far side* —
**has no edge on daily bars.** Whatever value the method has must come entirely from the
discretionary layer on top. That layer might be real skill. It might also be where the survivorship
and the storytelling live. **This data cannot tell you which, and neither can anyone selling you
the course.**

If you want to test the discretionary layer, the only honest way is forward: log every real-time
judgment call *before* you know the outcome, and hold yourself to the same statistical bar you
just held the bot to. The paper-trading journal in this repo exists for exactly that.

*Simulated. No real orders. Not financial advice.*
