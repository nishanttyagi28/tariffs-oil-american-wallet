"""OPTIONAL: US Census International Trade API (HS chapter x country x calculated duty).
Enabled only when CENSUS_API_KEY is set in E:/da-flagship/.env. Skipped gracefully otherwise.
"""
import os

import pandas as pd

from .common import http_get, load_env, record, save

URL = "https://api.census.gov/data/timeseries/intltrade/imports/hs"
FOCUS = {"5700": "China", "5330": "India", "1220": "Canada", "2010": "Mexico", "5880": "Japan",
         "0003": "European Union", "5520": "Vietnam", "4280": "Germany", "5800": "Korea, South"}


def run(start: str = "2023-01"):
    load_env()
    key = os.environ.get("CENSUS_API_KEY")
    if not key:
        return record("census_hs", "imports_hs2_country_duty", None, url=URL, status="skipped",
                      note="CENSUS_API_KEY not set; optional source")
    frames = []
    for code in FOCUS:
        params = {"get": "CTY_CODE,CTY_NAME,I_COMMODITY,I_COMMODITY_SDESC,GEN_VAL_MO,CON_VAL_MO,CAL_DUT_MO",
                  "time": f"from {start}", "COMM_LVL": "HS2", "CTY_CODE": code, "key": key}
        js = http_get(URL, params=params).json()
        frames.append(pd.DataFrame(js[1:], columns=js[0]))
    df = pd.concat(frames, ignore_index=True)
    df = df.loc[:, ~df.columns.duplicated()]
    for c in ("GEN_VAL_MO", "CON_VAL_MO", "CAL_DUT_MO"):
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df["period"] = pd.to_datetime(df["time"] + "-01")
    save(df, "census_hs", "imports_hs2_country_duty")
    return record("census_hs", "imports_hs2_country_duty", df, url=URL, date_col="period")
