# The one that makes the most sense — and the most money

Five ideas tested in this repo. Every active strategy lost to holding an index. So the honest
recommendation isn't a trick — it's the thing that kept winning while the tricks failed. But
"buy SPY" is lazy, so here's the actual, defensible version, with the numbers behind each choice.

## Scoreboard so far

| Strategy | Verdict |
|---|---|
| Mechanized DMC | −88% out-of-sample. Significant negative expectancy. |
| Overnight (buy close, sell open) | Real anomaly, loses to buy-and-hold on 33/35 names. |
| Congress copy-trading (NANC/KRUZ) | No significant alpha. It's tech beta. |
| **Broad-index buy & hold** | **The thing that beat all of the above.** |

## The core: total-market index, bought regularly, held for decades

SPY, 1993–2026 (34 years, monthly): **8.8% CAGR, Sharpe 0.65.** That is the benchmark four
"strategies" in this repo failed to beat. It costs ~0.03–0.09% in a fund like VTI/VOO, needs zero
skill, zero timing, and zero screen time.

## The one overlay that actually earns its keep

A 10-month moving-average switch (in when price > 10mo average, else cash) — Meb Faber's rule.
Same 34 years:

| | CAGR | Vol | Sharpe | **Max drawdown** |
|---|---|---|---|---|
| Buy & hold | 8.8% | 14.8% | 0.65 | **52.2%** |
| 10-month MA timing | 8.4% | 10.5% | **0.82** | **22.2%** |

It does **not** make more money — it makes 0.4% a year *less*. What it does is **cut the worst
drawdown from −52% to −22%** and lift risk-adjusted return (Sharpe 0.65 → 0.82). It only traded
~1.5×/year over 34 years, so costs are trivial.

**The catch, and it's a real one:** in a *taxable* account every exit is a taxable event, which
can erase the benefit. In a tax-advantaged account (IRA/401k) it's clean. And it will
underperform buy-and-hold in most years — its whole value shows up in the 2008/2020-type crashes.
Most people cannot stick with a rule that "loses" for years to pay off rarely. If you know you'd
abandon it, don't adopt it.

## What "makes the most money" actually depends on

- **Maximise expected dollars, can stomach −50%, won't touch it for 20+ years:** 100% total-market
  index, buy-and-hold, automate the contributions. Highest expected growth. This is the answer for
  most long-horizon money.
- **Want most of the return with half the gut-punch, in a tax-advantaged account:** add the
  10-month MA overlay. Better Sharpe, −22% worst case instead of −52%.
- **Closer to needing the money:** the return isn't the point anymore; not losing 50% at the wrong
  time is. Blend in bonds (a classic 60/40 lands ~7% with far shallower drawdowns).

## The rules that make ALL of these work — and matter more than the pick

1. **Cost is the one guaranteed edge.** 0.9% vs 0.04% in fees is ~20% of your money gone over 30
   years. This is the single highest-confidence lever in all of investing. Use the cheapest broad
   index fund.
2. **Automate contributions.** Dollar-cost-averaging monthly removes the timing decision that
   wrecks most people. The biggest predictor of returns isn't the strategy — it's not selling in
   the crash.
3. **Tax shelter first.** Max the IRA/401k before taxable. The tax drag dwarfs strategy choice.
4. **Do less.** Every test in this repo is a monument to activity losing to patience. The trades
   you don't make are where the money is.

## The honest close

I ran five ideas trying to beat "buy an index and wait." None did. That's not defeatism, it's the
base rate — decades of academic work say the same thing, and it's why the four rules above will do
more for your outcome than any signal I could hand you.

The boring answer is the profitable answer. That is the actual finding of this entire repo.

*Not financial advice. I am not a financial advisor. Past performance does not guarantee future
results. Your horizon, taxes and risk tolerance are yours, not mine.*
