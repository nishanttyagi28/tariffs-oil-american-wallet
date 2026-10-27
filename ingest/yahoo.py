"""Yahoo Finance chart API (daily OHLC, no key) for global indices, commodities, FX, rates, volatility."""
import time
from datetime import UTC, datetime

import pandas as pd

from .common import BROWSER_UA, http_get, record, save

URL = "https://query1.finance.yahoo.com/v8/finance/chart/{sym}"
# symbol: (name, asset_class, country_iso3, currency)
INSTRUMENTS = {
    "^GSPC": ("S&P 500", "equity_index", "USA", "USD"), "^IXIC": ("Nasdaq Composite", "equity_index", "USA", "USD"),
    "^NSEI": ("Nifty 50", "equity_index", "IND", "INR"), "^BSESN": ("BSE Sensex", "equity_index", "IND", "INR"),
    "^GDAXI": ("DAX", "equity_index", "DEU", "EUR"), "^STOXX50E": ("Euro Stoxx 50", "equity_index", "EUU", "EUR"),
    "^FTSE": ("FTSE 100", "equity_index", "GBR", "GBP"), "^N225": ("Nikkei 225", "equity_index", "JPN", "JPY"),
    "000001.SS": ("Shanghai Composite", "equity_index", "CHN", "CNY"), "^HSI": ("Hang Seng", "equity_index", "HKG", "HKD"),
    "^GSPTSE": ("S&P/TSX Composite", "equity_index", "CAN", "CAD"), "^MXX": ("Mexico IPC", "equity_index", "MEX", "MXN"),
    "GC=F": ("Gold futures", "commodity", None, "USD"), "BZ=F": ("Brent crude futures", "commodity", None, "USD"),
    "CL=F": ("WTI crude futures", "commodity", None, "USD"), "NG=F": ("Natural gas futures", "commodity", None, "USD"),
    "DX-Y.NYB": ("US Dollar Index (DXY)", "fx", "USA", "USD"), "INR=X": ("USD/INR", "fx", "IND", "INR"),
    "CNY=X": ("USD/CNY", "fx", "CHN", "CNY"), "CAD=X": ("USD/CAD", "fx", "CAN", "CAD"),
    "EURUSD=X": ("EUR/USD", "fx", "EUU", "USD"), "JPY=X": ("USD/JPY", "fx", "JPN", "JPY"),
    "MXN=X": ("USD/MXN", "fx", "MEX", "MXN"), "^VIX": ("CBOE VIX", "volatility", "USA", "USD"),
    "^TNX": ("US 10Y yield (x10 quote)", "rates", "USA", "USD"),
}


def run(start: str = "2015-01-01"):
    p1 = int(datetime.fromisoformat(start).replace(tzinfo=UTC).timestamp())
    p2 = int(datetime.now(UTC).timestamp())
    frames, failed = [], []
    for sym, (_name, _cls, _iso3, _ccy) in INSTRUMENTS.items():
        try:
            js = http_get(URL.format(sym=sym), params={"period1": p1, "period2": p2, "interval": "1d",
                                                       "events": "div,splits"}, ua=BROWSER_UA).json()
            res = js["chart"]["result"][0]
            q = res["indicators"]["quote"][0]
            adj = res["indicators"].get("adjclose", [{}])[0].get("adjclose")
            df = pd.DataFrame({"ts": res["timestamp"], "open": q["open"], "high": q["high"], "low": q["low"],
                               "close": q["close"], "volume": q.get("volume"), "adj_close": adj or q["close"]})
            off = res["meta"].get("gmtoffset", 0)
            df["date"] = pd.to_datetime(df.ts + off, unit="s").dt.normalize()
            df = df.dropna(subset=["close"]).drop(columns="ts").drop_duplicates("date", keep="last")
            df["symbol"] = sym
            frames.append(df)
        except Exception as e:
            failed.append(sym)
            print(f"Yahoo {sym} failed: {e}")
        time.sleep(0.5)
    out = pd.concat(frames, ignore_index=True)
    meta = pd.DataFrame([(s, *v) for s, v in INSTRUMENTS.items()],
                        columns=["symbol", "name", "asset_class", "country_iso3", "currency"])
    save(out, "yahoo", "market_prices_daily")
    save(meta, "yahoo", "instruments")
    return record("yahoo", "market_prices_daily", out, url=URL, date_col="date",
                  note=f"failed: {failed}" if failed else f"{len(frames)} instruments")
