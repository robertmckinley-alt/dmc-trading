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
