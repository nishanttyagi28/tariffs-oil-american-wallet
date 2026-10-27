"""US Census Bureau - U.S. trade in goods by country (monthly totals, no key).
Source workbook: https://www.census.gov/foreign-trade/balance/country.xlsx
Values are millions of USD, nominal, not seasonally adjusted (aggregate code 0004 is the SA world total).
"""
import io

import pandas as pd

from .common import RAW, http_get, record, save, save_bytes

URL = "https://www.census.gov/foreign-trade/balance/country.xlsx"
MONTHS = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]


def transform(df: pd.DataFrame, min_year: int = 2015) -> pd.DataFrame:
    df = df.copy()
    df.columns = [str(c).strip().upper() for c in df.columns]
    df = df[pd.to_numeric(df["YEAR"], errors="coerce") >= min_year]
    cols = [p + m for p in ("I", "E") for m in MONTHS if p + m in df.columns]
    long = df.melt(id_vars=["YEAR", "CTY_CODE", "CTYNAME"], value_vars=cols, var_name="col", value_name="value_musd")
    long["flow"] = long["col"].str[0].map({"I": "import", "E": "export"})
    long["month"] = long["col"].str[1:].map({m: i for i, m in enumerate(MONTHS, start=1)})
    long["year"] = long["YEAR"].astype(int)
    long["cty_code"] = long["CTY_CODE"].astype(str).str.strip().str.zfill(4)
    long["cty_name"] = long["CTYNAME"].astype(str).str.strip()
    long["value_musd"] = pd.to_numeric(long["value_musd"], errors="coerce")
    long = long.dropna(subset=["value_musd"])
    long["period"] = pd.to_datetime(long["year"].astype(str) + "-" + long["month"].astype(str).str.zfill(2) + "-01")
    # Census leaves not-yet-released months as 0 for every partner; keep months where World NSA (0015) > 0.
    world = long[long.cty_code.eq("0015")].groupby("period")["value_musd"].sum()
    good = set(world[world > 0].index)
    out = long[long.period.isin(good)][["year", "month", "cty_code", "cty_name", "flow", "value_musd", "period"]]
    return out.sort_values(["period", "cty_code", "flow"]).reset_index(drop=True)


def run(min_year: int = 2015, refresh: bool = False):
    cached = RAW / "census_country" / "country.xlsx"
    if cached.exists() and not refresh:
        content = cached.read_bytes()
    else:
        content = http_get(URL, ua="Mozilla/5.0").content
        save_bytes(content, "census_country", "country.xlsx")
    out = transform(pd.read_excel(io.BytesIO(content), dtype={"CTY_CODE": str}), min_year)
    save(out, "census_country", "trade_by_country_monthly")
    return record("census_country", "trade_by_country_monthly", out, url=URL, date_col="period")
