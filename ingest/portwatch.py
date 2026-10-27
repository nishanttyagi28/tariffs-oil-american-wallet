"""IMF PortWatch daily chokepoint transits (no key).
Primary: ArcGIS Hub CSV export of item 3da2b9ca97684916b75c4013f95d18ab (Daily_Chokepoints_Data).
Fallback: the FeatureServer /query endpoint (paged), which intermittently returns 'Invalid URL'.
"""
import io

import pandas as pd

from .common import http_get, record, save, save_bytes

ITEM = "3da2b9ca97684916b75c4013f95d18ab"
HUB_CSV = f"https://hub.arcgis.com/api/v3/datasets/{ITEM}_0/downloads/data"
QUERY = ("https://services9.arcgis.com/weJ1QsnbMYJlCHdG/arcgis/rest/services/"
         "Daily_Chokepoints_Data/FeatureServer/0/query")


def _from_hub() -> pd.DataFrame:
    r = http_get(HUB_CSV, params={"format": "csv", "spatialRefId": 4326, "where": "1=1"}, timeout=300)
    save_bytes(r.content, "portwatch", "chokepoints_daily.csv")
    return pd.read_csv(io.BytesIO(r.content))


def _from_query(page_size: int = 2000) -> pd.DataFrame:
    rows, offset = [], 0
    while True:
        js = http_get(QUERY, params={"where": "1=1", "outFields": "*", "orderByFields": "ObjectId",
                                     "resultOffset": offset, "resultRecordCount": page_size, "f": "json"},
                      timeout=120).json()
        if "error" in js:
            raise RuntimeError(js["error"])
        feats = js.get("features", [])
        rows += [f["attributes"] for f in feats]
        if not feats or not js.get("exceededTransferLimit"):
            break
        offset += len(feats)
    df = pd.DataFrame(rows)
    df["date"] = pd.to_datetime(df["date"], unit="ms", errors="coerce")
    return df


def run(start: str = "2019-01-01"):
    try:
        df, url = _from_hub(), HUB_CSV
    except Exception as e:  # noqa: BLE001
        print(f"portwatch hub csv failed ({e}); trying FeatureServer query")
        df, url = _from_query(), QUERY
    df.columns = [c.lower() for c in df.columns]
    df["date"] = pd.to_datetime(df["date"].astype(str).str.slice(0, 10).str.replace("/", "-"), errors="coerce")
    df = df[df["date"] >= start].drop(columns=[c for c in ("objectid",) if c in df.columns])
    save(df, "portwatch", "chokepoints_daily")
    return record("portwatch", "chokepoints_daily", df, url=url, date_col="date",
                  note=f"{df['portid'].nunique()} chokepoints")
