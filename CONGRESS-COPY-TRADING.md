# Copy-trading Congress (the "Pelosi trade")

**Verdict: no demonstrable alpha. It's beta with a tech tilt.**

## The cleanest possible test

You don't have to simulate this. **It already exists as real money, live, out-of-sample.**

- **NANC** — Unusual Whales Subversive Democratic Trading ETF. Buys what Democrat lawmakers
  disclose. (The ticker is not subtle.)
- **KRUZ** — the Republican version.

Both launched Feb 2023. They eat the same 45-day disclosure lag you would, pay real costs, and
are exactly the product a retail copy-trader would actually buy. This is a live forward test
of the entire idea, run with other people's money, and it has been running for 3.4 years.

## Raw performance, since NANC inception (2023-02-07)

| | Total | CAGR | Vol | Sharpe | Max DD |
|---|---|---|---|---|---|
| **NANC** (Democrats) | **+98.4%** | 22.3% | 16.8% | **1.28** | 20.9% |
| **KRUZ** (Republicans) | +75.0% | 17.9% | 14.3% | 1.22 | 15.8% |
| **SPY** (do nothing) | +81.1% | 19.0% | 15.1% | **1.23** | 19.0% |

NANC beat SPY by **+17.2 points**. This is the number that goes viral.

But look at the vol column: 16.8% vs 15.1%. It took **more risk**. And the Sharpe ratios —
**1.28 vs 1.23** — are almost identical. That's the tell.

## The regression kills it

Daily returns regressed on SPY:

| ETF | Beta | Alpha/yr | **t(alpha)** | Verdict |
|---|---|---|---|---|
| NANC | 1.06 | +1.8% | **0.65** | **not significant** |
| KRUZ | 0.65 | +4.1% | **0.73** | **not significant** |

Alpha needs t > 1.96 to be distinguishable from zero. Neither gets close.

Two-factor (SPY + QQQ) — to test whether it's simply a tech tilt:

| ETF | Alpha bp/day | t | SPY beta | QQQ beta |
|---|---|---|---|---|
| **NANC** | **+0.23** | **+0.23** | +0.65 | +0.33 |
| KRUZ | +1.95 | +0.85 | +0.90 | −0.19 |

**NANC's alpha collapses to +0.23 bp/day with a t-stat of 0.23 — statistically indistinguishable
from zero.** Once you account for the fact that it's 0.65 SPY + 0.33 QQQ, there is nothing left.

**NANC is a tech-tilted index fund wearing a costume.** Its outperformance is the Nasdaq
outperforming. You could have replicated it with two ETFs and no politicians.

## Why the "Pelosi returns" story survives anyway

**1. The 45-day lag.** STOCK Act filings can land six weeks after the trade. Whatever information
advantage existed has decayed by the time you can act. "Do lawmakers beat the market?" and "does
the *publicly copyable* version beat the market?" are different questions, and **only the second
one is available to you.**

**2. Selection on the outcome.** You've heard of Pelosi's trades *because* they were spectacular.
Nobody writes threads about the congressman who lagged the S&P. The set of politicians you'd have
picked *in advance* is not the set you're hearing about now — and note that even asking me to test
"Pelosi specifically" is selecting on the dependent variable. That's the same error, one level up.

**3. Concentrated tech beta looks like genius in a tech bull market.** Big single-name calls on
NVDA/AAPL/MSFT during 2023-2025 produce enormous returns. So did holding QQQ.

## Limits of this test

- 3.4 years, n≈860 days. A longer window could change the t-stats.
- I could not obtain raw disclosure data (the public House/Senate S3 feeds now return 403), so this
  is a test of the *implemented, investable* version, not a from-scratch simulation of individual
  lawmakers.
- NANC/KRUZ have their own fee and construction decisions that a DIY copier wouldn't share.

But note which direction those limits cut: a DIY version would have **higher** costs and **worse**
execution than a professionally-run ETF. The ETF is the optimistic case.

## Bottom line

The lawmakers may well be beating the market. **You cannot.** By the time you can see the trade,
the edge is gone, and what's left is a levered bet on tech that you could buy for 3bp in QQQ.

*Not financial advice. I am not a financial advisor.*
