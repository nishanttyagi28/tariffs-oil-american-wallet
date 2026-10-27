"""IMF PortWatch chokepoint reference layer (name, lat/lon, industry share) via ArcGIS FeatureServer (no key)."""
import pandas as pd

from .common import http_get, record, save

URL = ("https://services9.arcgis.com/weJ1QsnbMYJlCHdG/arcgis/rest/services/"
       "PortWatch_chokepoints_database/FeatureServer/0/query")


def run():
    js = http_get(URL, params={"where": "1=1", "outFields": "*", "returnGeometry": "false", "f": "json"},
                  timeout=120).json()
    if "error" in js:
        raise RuntimeError(js["error"])
    df = pd.DataFrame([f["attributes"] for f in js.get("features", [])])
    df.columns = [c.lower() for c in df.columns]
    save(df, "portwatch", "chokepoints_ref")
    return record("portwatch", "chokepoints_ref", df, url=URL, note=f"{len(df.columns)} cols")