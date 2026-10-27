"""UN Comtrade public preview (no key, one period per call): partner-reported exports TO the USA
(mirror data) for China, India, Canada, Mexico, Japan, Germany, Vietnam. Best-effort cross-check source."""
import time
from datetime import date

import pandas as pd

from .common import http_get, record, save

URL = "https://comtradeapi.un.org/public/v1/preview/C/M/HS"
REPORTERS = {156: "China", 699: "India", 124: "Canada", 484: "Mexico", 392: "Japan", 276: "Germany", 704: "Vietnam"}


def run(start_year: int = 2024):
    today = date.today()
    periods = [f"{y}{m:02d}" for y in range(start_year, today.year + 1) for m in range(1, 13)
               if (y, m) < (today.year, today.month)]
    rows, failed = [], 0
    for rep in REPORTERS:
        empty_streak = 0
        for p in periods:
            params = {"reporterCode": rep, "partnerCode": 842, "flowCode": "X", "cmdCode": "TOTAL", "period": p}
            try:
                data = http_get(URL, params=params, timeout=90, retries=3).json().get("data", []) or []
            except Exception as e:  # noqa: BLE001  preview endpoint is best-effort
                failed += 1
                print(f"comtrade {rep} {p} failed: {e}")
                data = []
            empty_streak = 0 if data else empty_streak + 1
            for d in data:
                rows.append({"reporter_code": rep, "reporter": REPORTERS[rep], "partner_code": 842,
                             "flow": d.get("flowCode"), "period": pd.to_datetime(str(d.get("period")) + "01"),
                             "value_usd": d.get("primaryValue")})
            time.sleep(1.1)
            if empty_streak >= 4 and p[:4] == str(today.year):  # reporter not yet published further months
                break
    df = pd.DataFrame(rows, columns=["reporter_code", "reporter", "partner_code", "flow", "period", "value_usd"])
    df = df.drop_duplicates(["reporter_code", "period"])
    save(df, "comtrade", "mirror_exports_to_us_monthly")
    return record("comtrade", "mirror_exports_to_us_monthly", df, url=URL, date_col="period",
                  note=f"failed calls: {failed}")
