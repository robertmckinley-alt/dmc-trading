# The overnight effect — buy at close, sell at open

**Verdict: the anomaly is real and well-documented. The strategy does not work.**
Both of those things are true at once, and the gap between them is the whole lesson.

Data: daily bars 2016-07 → 2026-07, 10 instruments. Out-of-sample = 2022-01-01 onward.

## The effect is real

| Symbol | Overnight bp/day | Intraday bp/day | t-stat |
|---|---|---|---|
| SPY | **+3.61** | +1.98 | 2.49 |
| QQQ | **+5.29** | +3.11 | 3.08 |
| IWM | **+6.20** | **−1.55** | 3.43 |
| GLD | **+5.17** | −0.42 | 3.39 |
| NVDA | **+18.01** | +7.12 | 4.71 |

IWM made **all** of its money overnight and **lost** money during the trading day. That's the
published finding (Lou, Polk & Skouras 2019; Cliff, Cooper & Gulen 2008), reproduced here.

## The strategy still loses to doing nothing

Out-of-sample (2022→), 1bp/side costs:

| Symbol | | CAGR | Sharpe | Max DD |
|---|---|---|---|---|
| SPY | overnight | **−0.7%** | **−0.01** | 25.4% |
| | buy & hold | **+10.7%** | **0.67** | 25.4% |
| QQQ | overnight | +2.8% | 0.27 | 30.0% |
| | buy & hold | **+14.1%** | **0.68** | 35.2% |
| IWM | overnight | +2.3% | 0.23 | 23.2% |
| | buy & hold | **+6.4%** | **0.39** | 28.0% |
| JPM | overnight | −2.8% | −0.12 | 30.0% |
| | buy & hold | **+18.6%** | **0.81** | 39.5% |

Buy-and-hold wins on **8 of 10** names, on both return and Sharpe.

**Look at SPY's drawdown column: 25.4% either way.** You take the *identical* drawdown and collect
a *fraction* of the return. That is the worst trade in the table.

## The edge decayed after it was published

| | SPY | QQQ | IWM | AAPL | TSLA | JPM |
|---|---|---|---|---|---|---|
| pre-2022 (bp/day) | 4.99 | 6.79 | 8.60 | 6.01 | 19.00 | 6.82 |
| 2022→ (bp/day) | **1.94** | **3.47** | **3.29** | **−4.03** | **7.60** | **1.30** |
| decay | −3.05 | −3.32 | −5.31 | −10.04 | −11.41 | −5.52 |

**Every symbol but one decayed.** AAPL flipped negative. This is what a known, published,
arbitraged anomaly looks like as it dies.

## And this is what you're actually being paid for

Worst single overnight moves:

- **SPY: −10.4%** (2020-03-16), −7.4%, −6.7%
- **IWM: −9.1%** (2020-03-16)
- **NVDA: −19.3%** (2018-11-16 earnings), −14.7%, −14.2%

The overnight return isn't an anomaly so much as a **risk premium**. You're compensated for
holding through the hours when news breaks and you *cannot* trade or hedge. March 2020 is the bill
coming due. There is no free lunch in it — you're just taking the risk everyone else went home to
avoid, and being paid slightly for it. Less and less, lately.

## The honest summary

The effect is real, published, reproducible — **and unharvestable.** You round-trip every single
day, so costs scale with the effect; the premium has compressed since it became famous; the Sharpe
is worse than doing nothing; and the drawdown is identical. It is a textbook example of why
"a real statistical effect" and "a system that makes money" are completely different claims.

*Simulated. Not financial advice. I am not a financial advisor.*
