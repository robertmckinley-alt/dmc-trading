# Does the overnight trade work on stocks? No — and it's worse than on SPY.

Universe: 30 mega-caps (the top ~20 of NASDAQ and NYSE by market cap) + 5 ETFs.
10 years of daily bars. Out-of-sample = 2022-01-01 onward. Costs 1bp/side.

## The headline

| | Overnight beats buy & hold (Sharpe) |
|---|---|
| ETFs | **0 / 5** |
| Individual stocks | **2 / 30** |

Median overnight Sharpe on stocks: **−0.06**. Median buy-and-hold: **+0.53**.

| | Overnight | Buy & hold |
|---|---|---|
| **AAPL** | −15.4% CAGR · Sharpe **−0.89** · 65% DD | +13.6% · 0.59 · 33% DD |
| **JNJ** | −9.8% · **−1.13** | +9.1% · +0.58 |
| **WMT** | −5.7% · −0.37 | +20.9% · +0.96 |
| **GOOGL** | −4.5% · −0.10 | +22.4% · +0.78 |

The two "winners" (ORCL, TSLA) out of 30 are about what chance hands you. Picking them *because*
they topped a 30-name search is the definition of curve-fitting.

---

## I asserted a mechanism. The data corrected me.

I claimed overnight fails on single stocks because **you eat every earnings gap**. That is only
half right, and the half that's wrong matters. Here is the actual decomposition:

### Earnings nights vs ordinary nights (19 mega-caps, real reported dates, pre/post-market aware)

| Symbol | Earnings nights | mean | **σ** | worst | best | Ordinary nights | mean |
|---|---|---|---|---|---|---|---|
| META | 40 | +1.55% | **10.15%** | −24.5% | +19.8% | 2472 | +1.73 bp |
| NFLX | 40 | −0.08% | **9.93%** | **−29.7%** | +16.9% | 2472 | +7.17 bp |
| ORCL | 40 | +0.98% | 9.04% | −14.5% | +32.2% | 2472 | +3.61 bp |
| INTC | 40 | −2.38% | 8.30% | −24.5% | +23.1% | 2472 | +7.78 bp |
| NVDA | 40 | +2.69% | 7.28% | −19.3% | +26.1% | 2472 | +13.95 bp |
| AAPL | 40 | +1.13% | 3.56% | −5.7% | +7.9% | 2472 | **−0.33 bp** |
| JNJ | 40 | +0.00% | 1.66% | −3.3% | +4.0% | 2472 | +0.85 bp |

**An earnings night is 5.0× more volatile than an ordinary night** (median σ 5.46% vs 1.08%).

### But earnings nights are not where the losses come from

- Earnings nights = **1.6%** of all nights held
- Mean cumulative contribution from **earnings** nights: **+27.9%**
- Mean cumulative contribution from **ordinary** nights: **+765.1%**

**Earnings nights are, on average, positive.** They are not eating your returns. They are eating
your *risk-adjusted* returns — a 5× volatility spike, four times a year, on a coin flip you cannot
forecast. You get paid a little for it and you take enormous variance to collect.

So the real reason overnight-only loses on stocks is duller and more damning:

### The ordinary-night drift is simply too small — and for some names, negative

Ordinary-night drift, bp/night:

```
AMD    +19.96   ████████████████
NVDA   +13.95   ███████████
TSLA   +12.56   ██████████
AMZN    +9.95   ████████
MSFT    +4.88   ████
GOOGL   +2.26   █
JNJ     +0.85
WMT     -0.07   <-- NEGATIVE
AAPL    -0.33   <-- NEGATIVE
PG      -1.94   <-- NEGATIVE
```

**AAPL's overnight drift is negative.** Apple's decade of returns was earned during the *trading
day*, not overnight. Same for Walmart and P&G. For those names, "buy at close, sell at open" is
systematically buying the worse half of the day, every day, and paying a spread twice for the
privilege.

Where the drift *is* strong — AMD, NVDA, TSLA — you're just capturing the beta of high-volatility
momentum names, and you'd have done better holding them outright.

---

## The honest summary

1. **The overnight premium is real on indices** and reproduces the literature.
2. **It is not universal on single stocks.** 3 of 19 mega-caps have *negative* overnight drift.
3. **Earnings nights add return but 5× the volatility** — you are paid a small premium for
   accepting a quarterly coin flip. That destroys Sharpe, not CAGR.
4. **You round-trip daily**, so costs scale with the effect and eat what's left.
5. **Buy-and-hold beat it on 33 of 35 instruments** tested.

There is no version of "buy at close, sell at open" here that beats doing nothing.

*Simulated. Not financial advice. I am not a financial advisor.*
