"""FRED via fredgraph.csv (no key). NOTE: use a plain user agent - browser UAs time out."""
import io
import time

import pandas as pd

from .common import http_get, record, save

URL = "https://fred.stlouisfed.org/graph/fredgraph.csv"
SERIES = {
    # prices & household
    "CPIAUCSL": ("CPI all items (SA)", "M"), "CPILFESL": ("Core CPI (SA)", "M"),
    "PCEPI": ("PCE price index", "M"), "PCEPILFE": ("Core PCE price index", "M"),
    "CES0500000003": ("Avg hourly earnings, private ($)", "M"), "UNRATE": ("Unemployment rate %", "M"),
    "PAYEMS": ("Nonfarm payrolls (k)", "M"), "UMCSENT": ("UMich consumer sentiment", "M"),
    "PSAVERT": ("Personal saving rate %", "M"), "RSAFS": ("Retail sales ($M)", "M"),
    "IR": ("Import price index, all", "M"), "IREXFDFLS": ("Import price index ex food & fuel", "M"),
    "IREXPET": ("Import price index ex petroleum", "M"), "BOPGSTB": ("Trade balance goods & services ($M)", "M"),
    "GASREGW": ("US regular gasoline retail ($/gal)", "W"), "MORTGAGE30US": ("30y mortgage rate %", "W"),
    "B235RC1Q027SBEA": ("Customs duties, SAAR ($B)", "Q"), "T10YIE": ("10y breakeven inflation %", "D"),
    # rates, fx, risk, oil
    "FEDFUNDS": ("Fed funds rate %", "M"), "DGS10": ("10y Treasury %", "D"), "DGS2": ("2y Treasury %", "D"),
    "DTWEXBGS": ("Broad USD index", "D"), "DEXINUS": ("INR per USD", "D"), "DEXCHUS": ("CNY per USD", "D"),
    "DEXCAUS": ("CAD per USD", "D"), "DEXUSEU": ("USD per EUR", "D"), "DEXJPUS": ("JPY per USD", "D"),
    "DEXMXUS": ("MXN per USD", "D"), "VIXCLS": ("VIX", "D"), "DCOILBRENTEU": ("Brent spot $/bbl", "D"),
    "DCOILWTICO": ("WTI spot $/bbl", "D"), "DHHNGSP": ("Henry Hub gas $/MMBtu", "D"),
}


def run(start: str = "2015-01-01"):
    frames, failed = [], []
    for sid, (label, freq) in SERIES.items():
        try:
            txt = http_get(URL, params={"id": sid, "cosd": start}, timeout=90).text
            df = pd.read_csv(io.StringIO(txt))
            df.columns = ["period", "value"]
            df["value"] = pd.to_numeric(df["value"], errors="coerce")
            df = df.dropna()
            df["series_id"], df["label"], df["frequency"] = sid, label, freq
            frames.append(df)
        except Exception as e:
            failed.append(sid)
            print(f"FRED {sid} failed: {e}")
        time.sleep(0.4)
    out = pd.concat(frames, ignore_index=True)
    out["period"] = pd.to_datetime(out["period"])
    save(out, "fred", "fred_series")
    return record("fred", "fred_series", out, url=URL, date_col="period",
                  note=f"failed: {failed}" if failed else f"{len(frames)} series")
