"""IMF PortWatch daily chokepoint transits (ArcGIS FeatureServer, no key)."""
import pandas as pd

from .common import http_get, record, save

URL = ("https://services9.arcgis.com/weJ1QsnbMYJlCHdG/arcgis/rest/services/"
       "Daily_Chokepoints_Data/FeatureServer/0/query")


def run(start: str = "2019-01-01", page_size: int = 2000):
    rows, offset = [], 0
    while True:
        params = {"where": f"date >= DATE '{start}'", "outFields": "*", "orderByFields": "ObjectId",
                  "resultOffset": offset, "resultRecordCount": page_size, "f": "json"}
        js = http_get(URL, params=params, timeout=120).json()
        if "error" in js:
            raise RuntimeError(js["error"])
        feats = js.get("features", [])
        rows += [f["attributes"] for f in feats]
        if not feats or not js.get("exceededTransferLimit"):
            break
        offset += len(feats)
    df = pd.DataFrame(rows)
    df.columns = [c.lower() for c in df.columns]
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    save(df, "portwatch", "chokepoints_daily")
    return record("portwatch", "chokepoints_daily", df, url=URL, date_col="date")
