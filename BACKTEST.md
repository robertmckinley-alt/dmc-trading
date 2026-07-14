# Backtesting DMC — how to do it without fooling yourself

## Run it

```bash
# 1. free key, instant, no card: https://www.alphavantage.co/support/#api-key
export ALPHAVANTAGE_KEY=your_key

# 2. pull 20+ years of daily bars (one call per symbol)
python3 engine/fetch.py SPY QQQ IWM AAPL NVDA TSLA JPM XOM

# 3. the honest run — rules examined pre-2022, then run untouched on data they never saw
python3 engine/backtest.py --split 2022-01-01

# 4. the test that catches curve-fitting
python3 engine/backtest.py --sweep

# 5. what friction actually costs you
python3 engine/backtest.py --costs 0     # compare against the default
```

Stdlib only. No dependencies. Also accepts `--provider tiingo` or `--provider csv --dir ./csv`
(any CSV with Date,Open,High,Low,Close — e.g. a TradingView export).

## Why this harness is built to attack the method, not flatter it

A backtest that replays the rules and prints a return is **worse than useless.** With enough knobs,
anything looks profitable on the data you tuned it on, and you'll walk away confident and wrong.
Six things here exist specifically to stop that:

**1. Out-of-sample split.** Rules get examined on the early era, then run *untouched* on data they
never saw. **Only the out-of-sample number is allowed to mean anything.** If in-sample is +0.4R and
out-of-sample is −0.1R, you didn't find an edge — you found a pattern in noise. The harness prints
the degradation explicitly, because that's the number people skip.

**2. Real costs.** Commission per share plus slippage on entry *and* exit. Run `--costs 0` and
compare: the gap between those two numbers is the tax reality charges on a strategy that trades a
lot. DMC trades a lot.

**3. Regime breakdown.** Bull / bear / chop, tagged by 200-day trend slope and price-vs-MA. **A
system that only works in one regime hasn't been tested — it's been lucky.** If DMC is +0.3R in
bull and −0.4R in chop, you don't have a strategy, you have a beta bet with extra steps.

**4. Bootstrap.** Resamples the trade sequence 10,000×. Gives you a real confidence interval on
expectancy, `P(expectancy > 0)`, and — the one nobody computes — **the distribution of max drawdown
you should actually expect**, including `P(you hit the 10% halt)`. Your realized drawdown was one
draw from that distribution. It could easily have been much worse.

**5. Parameter sensitivity sweep.** Sweeps the thresholds and prints every cell. **If the good
result sits on a knife-edge while its neighbours lose, that's curve-fit, not edge.** The harness
counts what fraction of the parameter space is profitable and tells you plainly if most of it
loses. A robust edge is a *plateau*, not a spike.

**6. Benchmark.** Buy-and-hold, same window, same symbols. **Beating zero is not the bar. Beating
SPY-and-doing-nothing is the bar** — because that's the alternative that costs no time, no stress,
and no commissions.

## The warning it prints, and why

With under ~2,500 total bars the harness prints:

```
*** WARNING: fewer than ~2500 bars total. This is NOT enough for a backtest. ***
```

and it will produce **zero trades** rather than a flattering number, because the 200-day regime
tagging needs 210 bars of warmup. **It fails loudly instead of fabricating.** That is deliberate.
A backtest that quietly returns a number on 50 bars is how people convince themselves of things.

## Rules for reading whatever it tells you

- **The in-sample number is not evidence.** Ignore it. It exists only to be compared against OOS.
- **Do not tune the parameters to improve the result.** That is the whole disease. If you sweep,
  sweep to check *robustness*, never to pick a winner. Picking the best cell of a grid you just
  searched is choosing the luckiest lottery ticket and calling it skill.
- **A positive result on one asset class in one decade is not an edge.** It's a hypothesis.
- **Nothing here tests the discretionary DMC** — human-chosen levels, real-time judgment,
  intraday timeframes, confluence zones. Those may be where the edge is. A backtest cannot reach
  them, and no result here can confirm *or* refute them.

## What we already know from the small sample

See [FINDINGS.md](FINDINGS.md). On ~50 daily bars across 5 names: level-gain hold rates near a coin
flip (every CI straddles 50%), and pooled expectancy negative at every target multiple 1R–3R —
but with confidence intervals that also straddle zero. **No demonstrated edge. Not demonstrated to
lose.** The honest state is "unknown," and it will stay unknown until this harness runs on a decade
of data.

*Simulated only. No real orders. Not financial advice.*
