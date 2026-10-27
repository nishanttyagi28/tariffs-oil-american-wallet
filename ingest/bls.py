"""BLS CPI-U by category via public API v1 (no key; 25 queries/day, <=25 series, <=10 years per query).
One POST per run; cached for the day to respect the limit."""
import json
from datetime import date

import pandas as pd

from .common import RAW, http_get, record, save

URL = "https://api.bls.gov/publicAPI/v1/timeseries/data/"
# CUUR0000 = CPI-U, US city average, not seasonally adjusted (YoY comparisons).
SERIES = {
    "CUUR0000SA0": "All items",
    "CUUR0000SA0L1E": "Core (less food & energy)",
    "CUUR0000SACL1E": "Core goods (commodities less food & energy)",
    "CUUR0000SASLE": "Core services (services less energy)",
    "CUUR0000SAA": "Apparel",
    "CUUR0000SEAE": "Footwear",
    "CUUR0000SAH3": "Household furnishings & supplies",
    "CUUR0000SEHJ": "Furniture & bedding",
    "CUUR0000SEHK": "Appliances",
    "CUUR0000SETA01": "New vehicles",
    "CUUR0000SETA02": "Used cars & trucks",
    "CUUR0000SEEE01": "Computers & peripherals",
    "CUUR0000SERE01": "Toys",
    "CUUR0000SEFP01": "Coffee",
    "CUUR0000SAF11": "Food at home",
    "CUUR0000SEFV": "Food away from home",
    "CUUR0000SETB01": "Gasoline (all types)",
    "CUUR0000SEHF01": "Electricity",
    "CUUR0000SAH1": "Shelter",
    "CUUR0000SEHA": "Rent of primary residence",
    "CUUR0000SAM2": "Medical care services",
    "CUUR0000SETD": "Motor vehicle maintenance & repair",
    "CUUR0000SETG01": "Airline fares",
    "CUUR0000SERA": "Video & audio",
    "CUUR0000SEHM": "Tools, hardware, outdoor equipment",
}


def run(startyear: int = 2017, endyear: int | None = None):
    endyear = endyear or date.today().year
    cache = RAW / "bls" / f"cpi_raw_{date.today().isoformat()}.json"
    if cache.exists():
        js = json.loads(cache.read_text())
    else:
        body = {"seriesid": list(SERIES), "startyear": str(startyear), "endyear": str(endyear)}
        js = http_get(URL, method="POST", json_body=body, headers={"Content-Type": "application/json"}).json()
        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_text(json.dumps(js))
    if js.get("status") != "REQUEST_SUCCEEDED":
        raise RuntimeError(f"BLS: {js.get('status')} {js.get('message')}")
    rows = []
    for s in js["Results"]["series"]:
        for d in s["data"]:
            if not d["period"].startswith("M") or d["period"] == "M13":
                continue
            try:
                v = float(d["value"])
            except ValueError:
                continue
            rows.append({"series_id": s["seriesID"], "category": SERIES.get(s["seriesID"]),
                         "period": pd.Timestamp(int(d["year"]), int(d["period"][1:]), 1), "index_value": v})
    df = pd.DataFrame(rows).sort_values(["series_id", "period"])
    missing = sorted(set(SERIES) - set(df.series_id))
    save(df, "bls", "cpi_categories_monthly")
    return record("bls", "cpi_categories_monthly", df, url=URL, date_col="period",
                  note=f"missing series: {missing}" if missing else "")
