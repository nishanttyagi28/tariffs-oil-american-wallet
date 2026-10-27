"""EIA spot prices (daily): Brent RBRTE and WTI RWTC history workbooks. No key."""
import io

import pandas as pd

from .common import http_get, record, save, save_bytes

SERIES = {"brent": "https://www.eia.gov/dnav/pet/hist_xls/RBRTEd.xls",
          "wti": "https://www.eia.gov/dnav/pet/hist_xls/RWTCd.xls"}


def run():
    frames = []
    for name, url in SERIES.items():
        content = http_get(url, timeout=120).content
        save_bytes(content, "eia", url.rsplit("/", 1)[1])
        df = pd.read_excel(io.BytesIO(content), sheet_name="Data 1", skiprows=2, engine="xlrd")
        df.columns = ["date", "price_usd_bbl"]
        df["benchmark"] = name
        frames.append(df.dropna())
    out = pd.concat(frames, ignore_index=True)
    out["date"] = pd.to_datetime(out["date"])
    save(out, "eia", "crude_spot_daily")
    return record("eia", "crude_spot_daily", out, url=SERIES["brent"], date_col="date")
