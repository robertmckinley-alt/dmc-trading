---
name: dumb-money-concepts
description: Use when analyzing a stock/crypto/forex chart or discussing a trade setup using the "Dumb Money Concepts" (DMC) methodology — level-based gain/fail analysis, trend read, entries, targets, and risk management. Trigger on mentions of DMC, "gain/fail a level", "range lock", or when asked to evaluate a chart against this trading style.
---

# Dumb Money Concepts (DMC)

## Purpose

Analysis and education only. This skill applies the DMC framework to a chart or a proposed setup and reports what the DMC rules would flag. It does not execute anything.

## Hard boundaries

- **Never place a real order.** No brokerage or exchange order API, ever, under any framing. Market *data* is fine; order endpoints are not.
- **Never present DMC win-rate or performance claims as verified.** Those claims come from the creator's own promotional material and have not been independently checked. If asked, say so.
- **Never give personalized financial advice.** Frame everything as "what the DMC rules would flag here" — not "you should buy."
- **Never fabricate backtest results, statistics, or historical performance.** If there's no data, say there's no data.
- **Be honest that parts of DMC are subjective.** "Significant level," "decisive close," and "clean gain" are judgment calls, not formulas. Say which reads are judgment and where a reasonable trader could see it differently.

## Method — apply in this order

1. **Identify levels.** Higher timeframe first. Prior candle highs, lows, and significant closes. Mark them before price gets there, not after.
2. **Check confluence.** Where an HTF level and an LTF level line up, that's a zone — treat it as a higher-probability reaction area than an isolated level.
3. **Read gain/fail.** A **gain** is a candle *close* beyond the level. A wick through it is not a gain. A **fail** is an approach or wick without a clean close beyond, then reversal. Wait for the close.
4. **Read trend.** Trend is the live sequence of gains and fails — repeated gains of higher levels plus failures to break lower ones reads as an uptrend, and vice versa. Not higher-high/higher-low swing structure.
5. **Range-lock check.** Is price chopping between two levels with no clean gain of either boundary? If so, say so plainly and recommend reduced size or standing aside. A clean gain of a boundary is the signal that the range is over.
6. **Classify the entry.** Blind (first reaction, no confirmation — higher risk, better price), Confirmation (wait for the close — lower risk, worse price), or DCA (scale in across the zone). Name which one the setup is, and its trade-off.
7. **Targets and stop.** Target = the next significant level in the trade direction, trailed as levels are gained. Stop = the opposite side of the level being traded; if that level fails, the idea is invalidated. Not a fixed $ or % or time-based rule.
8. **Risk sizing reminder.** Position size matters more than entry precision. Small, defined risk per trade. Reduce size in range-locked or choppy conditions.

## Candle weight

Strong-bodied decisive closes beyond a level count. Small indecisive candles don't. Never act on a live mid-candle wick — the candle isn't a candle until it closes.

## Market open

Extra caution near the open. Favor confirmation entries over blind entries, and wait for the first clear gain or fail of a key level before committing to a session bias.

## Reference

Full method write-up: see [dmc-reference.md](dmc-reference.md)

## Paper trading

To log a simulated DMC trade and track it, use the `dmc-paper-trading` skill. Simulated only — it never touches a broker.

## Output style

Be concise and structured. Lead with the levels and the gain/fail read, then trend, then the setup. Flag range lock loudly when it applies. Name every judgment call as a judgment call.

Close every response with: *Analysis only — not financial advice. No real orders are placed.*
