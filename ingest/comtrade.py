"""UN Comtrade public preview (no key, <=500 rows/call): partner-reported exports TO the USA
(mirror data) for China, India, Canada, Mexico, Japan, Germany, Vietnam."""
import time

import pandas as pd

from .common import http_get, record, save

URL = "https://comtradeapi.un.org/public/v1/preview/C/M/HS"
REPORTERS = {156: "China", 699: "India", 124: "Canada", 484: "Mexico", 392: "Japan", 276: "Germany", 704: "Vietnam"}


def run(years=(2024, 2025, 2026)):
    rows = []
    for rep in REPORTERS:
        for y in years:
            periods = ",".join(f"{y}{m:02d}" for m in range(1, 13))
            params = {"reporterCode": rep, "partnerCode": 842, "flowCode": "X", "cmdCode": "TOTAL", "period": periods}
            try:
                data = http_get(URL, params=params, timeout=90).json().get("data", []) or []
            except Exception as e:  # preview endpoint is best-effort
                print(f"comtrade {rep} {y} failed: {e}")
                data = []
            for d in data:
                rows.append({"reporter_code": rep, "reporter": REPORTERS[rep], "partner_code": 842,
                             "flow": d.get("flowCode"), "period": pd.to_datetime(str(d.get("period")) + "01"),
                             "value_usd": d.get("primaryValue")})
            time.sleep(1.5)
    df = pd.DataFrame(rows)
    save(df, "comtrade", "mirror_exports_to_us_monthly")
    return record("comtrade", "mirror_exports_to_us_monthly", df, url=URL, date_col="period")
