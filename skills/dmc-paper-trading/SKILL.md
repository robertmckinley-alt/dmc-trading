---
name: dmc-paper-trading
description: Log, track and analyze SIMULATED (paper) trades using the Dumb Money Concepts level-based method, and rebuild the paper-trading dashboard. Use when the user wants to paper trade DMC, journal a simulated trade, check open paper positions, run the daily DMC scan, review win rate / expectancy / drawdown, or update their paper-trading site. Never places real orders.
---

# DMC Paper Trading

Simulated trades only. This skill logs trades to a local JSON ledger and renders a dashboard.

## Hard boundaries — non-negotiable

- **No brokerage. No exchange. No order endpoint. Ever.** Read-only market *data* only. If the user asks to connect a broker or place a live order, decline and say why.
- **Never fabricate results.** If a fetch fails, say the fetch failed. Do not invent a candle, a fill, or a statistic.
- **Never tune the rules until the equity curve looks good.** That is curve-fitting, and it is the single easiest way to lose real money later. If the result is bad, report the bad result.
- **Never call a small sample an edge.** Under ~30 trades, the only honest verdict is "not enough data."

## The mechanization problem — say this out loud

DMC contains subjective terms: *significant level*, *decisive close*, *clean gain*. Code cannot be subjective, so the engine pins them to fixed thresholds. **Results test the mechanization, not the method.** Never let the user walk away thinking a backtest number is a verdict on DMC itself. Say it explicitly, every time.

## Daily cycle

1. `python3 engine.py` — fetch/refresh candles, evaluate levels, fire signals, manage open positions, mark to market.
2. `python3 site.py` — rebuild `dmc-dashboard.html`.
3. Report: what triggered, what closed, current equity, current drawdown, distance to the halt floor.
4. State the sample size and refuse to over-read it.

## Rules the engine encodes

| Rule | Implementation |
|---|---|
| Level | Prior day H/L/C and prior week H/L/C |
| Gain | Close beyond the level when the prior close was not beyond it |
| Fail | Wick beyond, close not beyond — never an entry |
| Decisive | Body ≥ 50% of the candle's range |
| Range lock | \|close − close[−10]\| < 0.75 × ATR(10) → stand aside |
| Entry | Next session's **open** — you cannot fill at the signal close |
| Stop | Far side of the traded level + 0.25 × ATR(14) |
| Target | Next level in the trade's direction (must beat the stop, else no trade) |
| Tie | If a bar spans stop and target, the **stop** is taken |

## Risk configuration

Starting equity $200,000 · 0.5% risk per trade · max 4 concurrent · max 2% open risk · **hard halt at 10% drawdown ($180,000)**. When the floor is hit the engine stops opening trades and the dashboard shows HALTED. Do not override it.

## Not modelled — mention when reporting

Slippage, commissions, gaps through the stop, and partial fills. Real results would be **worse** than these. Say so.

## Ledger schema

See [references/ledger-schema.md](references/ledger-schema.md)

## Standalone journal CLI

`scripts/paper.py` logs manual trades (`open`, `mark`, `check`, `close`, `stats`, `grade`) and computes DMC levels for any symbol. `grade` scores a trade on **rule compliance, not outcome** — a rule-perfect trade can lose and a sloppy one can win.

## Output style

Lead with equity, drawdown, and sample size. Then the trades. Then the honest read on what the sample can and cannot support.

Close with: *Simulated only — no real orders. Not financial advice.*
