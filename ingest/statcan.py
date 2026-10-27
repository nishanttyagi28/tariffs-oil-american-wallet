"""Statistics Canada table 12-10-0011-01: merchandise trade by principal partners (monthly, CAD).
Full-table CSV download (no key): https://www150.statcan.gc.ca/n1/tbl/csv/12100011-eng.zip
"""
import io
import zipfile

import pandas as pd

from .common import http_get, record, save, save_bytes

URL = "https://www150.statcan.gc.ca/n1/tbl/csv/12100011-eng.zip"


def run(min_year: int = 2015):
    content = http_get(URL, timeout=180).content
    save_bytes(content, "statcan", "12100011-eng.zip")
    with zipfile.ZipFile(io.BytesIO(content)) as z:
        name = next(n for n in z.namelist() if n.endswith(".csv") and "MetaData" not in n)
        df = pd.read_csv(z.open(name), low_memory=False)
    df["period"] = pd.to_datetime(df["REF_DATE"] + "-01", errors="coerce")
    df = df[df.period.dt.year >= min_year]
    keep = [c for c in ["period", "GEO", "Trade", "Basis", "Seasonal adjustment", "Principal trading partners",
                        "UOM", "SCALAR_FACTOR", "VALUE"] if c in df.columns]
    df = df[keep].rename(columns=lambda c: c.lower().replace(" ", "_"))
    save(df, "statcan", "trade_principal_partners_monthly")
    return record("statcan", "trade_principal_partners_monthly", df, url=URL, date_col="period")
