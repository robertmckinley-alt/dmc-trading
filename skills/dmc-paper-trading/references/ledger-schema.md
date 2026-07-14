# Ledger / results schema

`data/candles.json` — `{ "SYM": [[date, open, high, low, close], ...] }`, oldest first.

`data/results.json`

```jsonc
{
  "config": { "start_equity": 200000, "max_drawdown_pct": 10, "risk_per_trade_pct": 0.5,
              "max_concurrent": 4, "max_open_risk_pct": 2.0 },
  "symbols": ["SPY","QQQ"],
  "floor": 180000,
  "halted": false,
  "trades": [{
    "id": 1, "symbol": "SPY", "side": "long|short",
    "level": 745.40, "level_kind": "prior day high",
    "signal_date": "2026-07-08",   // close that fired the signal
    "entry_date": "2026-07-09",    // fill = NEXT session's open
    "entry": 747.35, "stop": 743.10, "target": 751.31,
    "qty": 235.29, "risk_cash": 1000.0, "risk_per_unit": 4.25,
    "planned_rr": 1.87, "style": "confirmation",
    "status": "open|closed", "exit": 751.31, "exit_date": "2026-07-10",
    "reason": "target hit|stop hit", "r": 1.87, "pl": 932.40
  }],
  "curve": [{ "date": "...", "equity": 200000.0, "realized": 200000.0,
              "peak": 200000.0, "dd_pct": 0.0, "open": 0, "halted": false }]
}
```

**R** = (exit − entry) / (entry − stop), sign-adjusted for side. One R = one unit of planned risk. Judge the system in R, not dollars — dollars flatter a big account.

**Equity** = start + realized P/L + unrealized (open positions marked to the day's close).

**Drawdown** = (peak − equity) / peak. Peak is the running high-water mark of *equity*, not of realized P/L.
