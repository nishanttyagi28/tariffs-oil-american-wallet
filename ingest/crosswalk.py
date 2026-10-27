"""Census Schedule C country codes -> ISO2 -> ISO3 (via pycountry), joined to Natural Earth label points.
Small partners missing from Natural Earth 1:110m get hand-entered capital coordinates."""
import re

import pandas as pd
import pycountry

from .common import RAW, http_get, record, save, save_bytes

URL = "https://www.census.gov/foreign-trade/schedules/c/country.txt"
# Partners not in NE 110m (lat, lon) - approximate capital/centroid, for map placement only.
EXTRA_POINTS = {"SGP": (1.35, 103.82), "HKG": (22.32, 114.17), "BHR": (26.07, 50.55), "MLT": (35.94, 14.38),
                "MAC": (22.20, 113.55), "BRB": (13.19, -59.54), "MUS": (-20.35, 57.55), "LIE": (47.16, 9.55),
                "AND": (42.51, 1.52), "MCO": (43.74, 7.42), "ABW": (12.52, -69.97), "CUW": (12.17, -68.98),
                "BMU": (32.31, -64.75), "CYM": (19.31, -81.25), "SXM": (18.04, -63.07), "MDV": (3.20, 73.22),
                "SYC": (-4.68, 55.49), "TTO": (10.69, -61.22), "BRN": (4.54, 114.73), "LUX": (49.82, 6.13)}


def run():
    txt = http_get(URL, ua="Mozilla/5.0").text
    save_bytes(txt.encode(), "crosswalk", "schedule_c_country.txt")
    rows = []
    for line in txt.splitlines():
        m = re.match(r"^(\d{4})\s*\|\s*(.+?)\s*\|\s*([A-Z]{2})?\s*$", line)
        if m:
            code, name, iso2 = m.groups()
            c = pycountry.countries.get(alpha_2=iso2) if iso2 else None
            iso3 = c.alpha_3 if c else ({"XK": "XKX"}.get(iso2))
            rows.append({"cty_code": code, "census_name": name, "iso2": iso2, "iso3": iso3})
    df = pd.DataFrame(rows)
    ne = pd.read_parquet(RAW / "naturalearth" / "countries.parquet")[
        ["iso3", "name", "continent", "region_un", "subregion", "region_wb", "income_grp", "label_x", "label_y"]]
    ne = ne.drop_duplicates("iso3")
    df = df.merge(ne, on="iso3", how="left")
    for iso3, (lat, lon) in EXTRA_POINTS.items():
        m = df.iso3.eq(iso3) & df.label_y.isna()
        df.loc[m, "label_y"], df.loc[m, "label_x"] = lat, lon
    df = df.rename(columns={"label_x": "longitude", "label_y": "latitude", "name": "ne_name"})
    save(df, "crosswalk", "census_country_iso")
    return record("crosswalk", "census_country_iso", df, url=URL)
