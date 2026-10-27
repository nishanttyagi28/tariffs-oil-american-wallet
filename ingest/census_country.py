"""US Census Bureau - U.S. trade in goods by country (monthly totals, no key).
Source workbook: https://www.census.gov/foreign-trade/balance/country.xlsx
Values are millions of USD, nominal, not seasonally adjusted.
"""
import io

import pandas as pd

from .common import http_get, record, save, save_bytes

URL = "https://www.census.gov/foreign-trade/balance/country.xlsx"
MONTHS = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]


def run(min_year: int = 2015):
    content = http_get(URL, ua="Mozilla/5.0").content
    save_bytes(content, "census_country", "country.xlsx")
    df = pd.read_excel(io.BytesIO(content), dtype={"CTY_CODE": str})
    df.columns = [str(c).strip().upper() for c in df.columns]
    rows = []
    for _, r in df.iterrows():
        year = int(r["YEAR"])
        if year < min_year:
            continue
        for i, m in enumerate(MONTHS, start=1):
            for flow, prefix in (("import", "I"), ("export", "E")):
                col = prefix + m
                if col in df.columns and pd.notna(r[col]):
                    rows.append((year, i, str(r["CTY_CODE"]).zfill(4), str(r["CTYNAME"]).strip(), flow, float(r[col])))
    out = pd.DataFrame(rows, columns=["year", "month", "cty_code", "cty_name", "flow", "value_musd"])
    out["period"] = pd.to_datetime(dict(year=out.year, month=out.month, day=1))
    # Census leaves not-yet-released months as 0 for every partner; drop months where World NSA (code 0015) is 0.
    world = out[out.cty_code.eq("0015")].groupby("period").value_musd.sum()
    good = world[world > 0].index
    out = out[out.period.isin(good)]
    save(out, "census_country", "trade_by_country_monthly")
    return record("census_country", "trade_by_country_monthly", out, url=URL, date_col="period")
