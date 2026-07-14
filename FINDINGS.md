# Level-respect scan — does DMC work on any stock, or just SPY?

**Question:** DMC's whole model rests on one assumption — *when price gains a level, the level
holds.* Your stop sits just past the level. If the level gets reclaimed, you're stopped out.
So: does that assumption hold, and does it hold differently on different instruments?

**Method.** For every prior-day level (H/L/C) across ~50 daily bars per name:

- **GAIN** — close beyond the level when the prior close was not beyond it
- **HOLD** — price then extended 0.5×ATR before reclaiming the level (the trade works)
- **FAKE** — price reclaimed the level first, so the DMC stop gets hit
- **WICK-FAIL** — pierced the level, closed back inside (DMC calls this a "fail" — correctly)
- **GAP-RISK** — the open jumped >1×ATR from the prior close (your stop does not exist that day)

Reproduce: `python3 engine/scan.py`

## Results (Apr 30 → Jul 13 2026, daily bars)

| Symbol | Gains | Hold% | Fake% | Wick-fail% | Gap-risk% | ATR% |
|---|---|---|---|---|---|---|
| QQQ  | 53 | **58.5%** | 41.5% | 14.6% | 8.8% | 2.11% |
| SPY  | 48 | 47.9% | 52.1% | 33.3% | 2.9% | 1.24% |
| TSLA | 51 | 47.1% | 49.0% | 17.0% | 0.0% | 4.37% |
| NVDA | 46 | 41.3% | 58.7% | 37.3% | 0.0% | 3.72% |
| JPM  | 44 | 38.6% | 61.4% | 32.7% | 0.0% | 2.16% |

## Is any of it real? No.

| Symbol | Hold% | 95% CI | Verdict |
|---|---|---|---|
| QQQ  | 58.5% | [45.1%, 70.7%] | indistinguishable from a coin flip |
| SPY  | 47.9% | [34.5%, 61.7%] | indistinguishable from a coin flip |
| TSLA | 47.1% | [35.6%, 62.5%] | indistinguishable from a coin flip |
| NVDA | 41.3% | [28.3%, 55.7%] | indistinguishable from a coin flip |
| JPM  | 38.6% | [25.7%, 53.4%] | indistinguishable from a coin flip |

**Every interval straddles 50%.** On this sample, no instrument shows statistically
demonstrable level-respect — not even QQQ, which topped the table. The ranking is noise.

## What this does and does not mean

**It does not mean DMC fails.** A ~50% directional hit rate can still be very profitable if the
winners run further than the losers cost — and that is exactly what DMC's structure is built for:
stop just past the level (small), target at the next level (larger). **If there's an edge here, it
lives in the payoff asymmetry, not in directional accuracy.** This scan tests accuracy only.

It also means the intuition that "indices respect levels, volatile single names chop" is **not
supported**. TSLA (ATR 4.4%) held levels about as well as SPY. JPM — the boring bank — was worst.
That prediction was wrong, and the data says so.

## The gap-risk number is a trap

Single names show **0.0% gap risk** here. That is not because they're safe. It's because this
50-bar window happens to contain **no earnings reports** for NVDA, TSLA, or JPM. (JPM reports the
day after this data ends.) Gap risk didn't show up because the sample dodged it — the single most
important reason indices are structurally safer for a stop-at-the-level method. Do not read 0.0%
as "no gap risk."

## Honest limits

- ~50 bars, 5 names, one market regime (a mild uptrend). This is a probe, not a study.
- "Level" here = prior day H/L/C only. A discretionary trader draws levels differently.
- Daily bars. DMC is often traded intraday, where the statistics may differ entirely.
- Nothing here is tuned, and nothing here should be tuned to look better.

*Not financial advice. Simulated analysis only.*

---

# Part 2 — Payoff asymmetry: the test that decides it

Part 1 showed hold rates near 50% everywhere. That does **not** condemn DMC — a coin flip is
profitable if winners run further than losers cost, and DMC is *built* for that: tight stop just
past the level, target at the next level. So the real question is whether the payoff asymmetry
rescues the near-random directional accuracy.

**Method.** For every gain: entry = next session's open, stop = far side of the level + 0.25×ATR
(this defines 1R), then walk forward 15 bars. Measure MAE (heat taken) and MFE (what was actually
on the table), and simulate fixed targets at 1R → 3R. Stop wins any tie.

Reproduce: `python3 engine/payoff.py`

## Expectancy (R per trade) at each fixed target

| Symbol | N | 1.0R | 1.5R | 2.0R | 2.5R | 3.0R | med MFE | med MAE |
|---|---|---|---|---|---|---|---|---|
| SPY  | 25 | +0.17 | +0.35 | **+0.43** | +0.21 | +0.35 | 1.66 | −1.46 |
| QQQ  | 28 | +0.04 | −0.03 | −0.14 | −0.21 | −0.36 | 1.00 | −1.69 |
| NVDA | 30 | −0.07 | −0.11 | −0.07 | −0.09 | −0.14 | 1.95 | −2.37 |
| TSLA | 25 | −0.42 | −0.57 | −0.54 | −0.66 | −0.66 | 0.81 | −1.37 |
| JPM  | 24 | −0.14 | +0.02 | +0.09 | +0.14 | +0.05 | 1.05 | −0.97 |
| **POOLED** | **132** | **−0.08** | **−0.07** | **−0.05** | **−0.13** | **−0.16** | **1.15** | **−1.54** |

**Pooled expectancy is negative at every single target multiple.** There is no exit rule in this
family that rescues it. The hypothesis — "the edge lives in the payoff asymmetry" — is **not
supported**.

## The number that explains why

**Median MAE = −1.54R. Median MFE = +1.15R.**

The *typical* gain goes further against you than it ever goes for you. The median trade takes more
than a full R of heat — meaning the median trade is simply stopped out. There is no target you can
place that collects money the market never offered.

| Target | % of gains whose MFE ever reached it |
|---|---|
| 1.0R | 53.8% |
| 1.5R | 43.2% |
| 2.0R | 31.1% |
| 3.0R | 22.7% |

Only 31% of gains ever *touch* 2R. Aiming there means being wrong roughly 7 times out of 10.

## But it is still not statistically conclusive

Pooled at 2R: n=132, expectancy **−0.05R**, 95% CI **[−0.26, +0.16]**. **That straddles zero.**
So: the point estimate is negative at every target, and the honest verdict is still
*"no demonstrated edge"* rather than *"demonstrated to lose."* Those are different claims and
the difference matters.

SPY looks good (+0.43R at 2R). TSLA looks terrible (−0.54R). With n≈25 each, that spread is
almost certainly noise. Do not go trade SPY on the strength of that cell.

## Two traps in this table

1. **"Best target = 2R" was chosen by looking at this data.** That is curve-fitting. It's an upper
   bound on what you *could have* extracted, not an estimate of what you *will* extract.
2. **No costs.** Slippage and commissions are not modelled. Every number above is optimistic.

## Where this leaves DMC

On daily bars, with levels defined as prior-day H/L/C, and stops/targets placed mechanically:
**no edge is demonstrable, and the point estimates lean negative.**

What this does **not** test — and what a fair evaluation would need:
- Intraday timeframes, where DMC is often actually traded
- Levels chosen by human judgment rather than "prior day H/L/C"
- Discretionary filters: which levels matter, which closes are truly "decisive"
- Confluence zones (HTF + LTF alignment), which DMC treats as the high-probability setups

Those are exactly the subjective parts a backtest cannot reach. They may be where the edge lives.
They may also be where the story lives. This data cannot tell you which.

*Not financial advice. Simulated analysis only.*
