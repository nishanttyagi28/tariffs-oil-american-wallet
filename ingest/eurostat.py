"""Eurostat - EU27 trade with partners by SITC (monthly, EUR millions). JSON-stat API, no key."""
import itertools

import pandas as pd

from .common import http_get, record, save

URL = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/ext_st_eu27_2020sitc"


def _jsonstat_to_df(js: dict) -> pd.DataFrame:
    ids, sizes = js["id"], js["size"]
    cats = []
    for d in ids:
        idx = js["dimension"][d]["category"]["index"]
        cats.append(sorted(idx, key=idx.get))
    values = js["value"]
    rows = []
    for n, combo in enumerate(itertools.product(*cats)):
        v = values.get(str(n)) if isinstance(values, dict) else values[n]
        if v is not None:
            rows.append((*combo, v))
    return pd.DataFrame(rows, columns=[*ids, "value"])


def run(since: str = "2015-01"):
    frames = []
    for partner in ("US", "CN", "EXT_EU27_2020"):
        for flow in ("EXP", "IMP"):
            params = {"format": "JSON", "geo": "EU27_2020", "partner": partner, "sitc06": "TOTAL",
                      "stk_flow": flow, "indic_et": "TRD_VAL", "freq": "M", "sinceTimePeriod": since}
            frames.append(_jsonstat_to_df(http_get(URL, params=params).json()))
    df = pd.concat(frames, ignore_index=True)
    df["period"] = pd.to_datetime(df["time"] + "-01")
    df = df.rename(columns={"value": "value_meur"})[["period", "geo", "partner", "stk_flow", "sitc06", "value_meur"]]
    save(df, "eurostat", "eu27_trade_partner_monthly")
    return record("eurostat", "eu27_trade_partner_monthly", df, url=URL, date_col="period")
