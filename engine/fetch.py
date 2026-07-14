#!/usr/bin/env python3
"""
Fetch long daily history. Read-only market data. No broker, no orders.

  export ALPHAVANTAGE_KEY=xxxx
  python3 fetch.py SPY QQQ IWM AAPL NVDA TSLA JPM XOM

Free key: https://www.alphavantage.co/support/#api-key  (25 calls/day, 20+ yrs per call)
Alternatives: --provider tiingo (TIINGO_KEY), --provider csv --dir ./csv
Writes data/candles.json  -> {"SYM": [[date, o, h, l, c], ...]}, oldest first.
"""
import json, os, sys, time, csv, argparse, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
OUT  = os.path.join(HERE, "data", "candles.json")

def _get(url):
    for bad in ("/order", "/orders", "/account", "/withdraw", "/position"):
        if bad in url.lower():
            raise SystemExit("REFUSED: that looks like a trading endpoint. Data only.")
    req = urllib.request.Request(url, headers={"User-Agent": "dmc-backtest (read-only data)"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()

def alphavantage(sym, key):
    url = ("https://www.alphavantage.co/query?function=TIME_SERIES_DAILY"
           f"&symbol={sym}&outputsize=full&apikey={key}")
    d = json.loads(_get(url))
    if "Time Series (Daily)" not in d:
        raise SystemExit(f"{sym}: {d.get('Note') or d.get('Information') or d.get('Error Message') or d}")
    ts = d["Time Series (Daily)"]
    rows = [[dt, float(v["1. open"]), float(v["2. high"]),
             float(v["3. low"]), float(v["4. close"])] for dt, v in ts.items()]
    return sorted(rows)

def tiingo(sym, key):
    url = (f"https://api.tiingo.com/tiingo/daily/{sym}/prices"
           f"?startDate=2005-01-01&token={key}&format=json")
    d = json.loads(_get(url))
    return sorted([[r["date"][:10], r["adjOpen"], r["adjHigh"], r["adjLow"], r["adjClose"]] for r in d])

def from_csv(sym, d):
    """Any CSV with Date,Open,High,Low,Close columns (e.g. a TradingView export)."""
    path = os.path.join(d, f"{sym}.csv")
    rows = []
    with open(path) as f:
        for r in csv.DictReader(f):
            k = {kk.lower(): vv for kk, vv in r.items()}
            rows.append([k["date"][:10], float(k["open"]), float(k["high"]),
                         float(k["low"]), float(k["close"])])
    return sorted(rows)

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("symbols", nargs="+")
    ap.add_argument("--provider", default="alphavantage",
                    choices=["alphavantage", "tiingo", "csv"])
    ap.add_argument("--dir", default="./csv")
    ap.add_argument("--merge", action="store_true", help="keep existing symbols in candles.json")
    a = ap.parse_args()

    out = {}
    if a.merge and os.path.exists(OUT):
        out = json.load(open(OUT))

    for i, s in enumerate(a.symbols):
        s = s.upper()
        if a.provider == "alphavantage":
            key = os.environ.get("ALPHAVANTAGE_KEY") or sys.exit("set ALPHAVANTAGE_KEY")
            rows = alphavantage(s, key)
            if i < len(a.symbols) - 1: time.sleep(13)     # free tier: be polite
        elif a.provider == "tiingo":
            key = os.environ.get("TIINGO_KEY") or sys.exit("set TIINGO_KEY")
            rows = tiingo(s, key)
        else:
            rows = from_csv(s, a.dir)
        out[s] = rows
        print(f"{s}: {len(rows)} bars   {rows[0][0]} -> {rows[-1][0]}")

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(out, open(OUT, "w"))
    print(f"\nwrote {OUT}")
