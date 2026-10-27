"""Natural Earth 1:110m admin-0 countries: ISO codes, region, label point (map lat/long).
Attributes are read straight from the shapefile's .dbf (no GIS dependency)."""
import io
import struct
import zipfile

import pandas as pd

from .common import http_get, record, save, save_bytes

URL = "https://naciscdn.org/naturalearth/110m/cultural/ne_110m_admin_0_countries.zip"
KEEP = ["ADMIN", "NAME", "NAME_LONG", "FORMAL_EN", "ISO_A2", "ISO_A3", "ISO_A3_EH", "ADM0_A3", "CONTINENT",
        "REGION_UN", "SUBREGION", "REGION_WB", "ECONOMY", "INCOME_GRP", "POP_EST", "GDP_MD", "LABEL_X", "LABEL_Y"]


def read_dbf(b: bytes) -> pd.DataFrame:
    n, hlen, rlen = struct.unpack("<xxxxIHH", b[:12])
    fields, pos = [], 32
    while b[pos] != 0x0D:
        name = b[pos:pos + 11].split(b"\x00")[0].decode()
        ftype, flen = chr(b[pos + 11]), b[pos + 16]
        fields.append((name, ftype, flen))
        pos += 32
    recs, off = [], hlen
    for _ in range(n):
        rec, p = {}, off + 1
        for name, ftype, flen in fields:
            raw = b[p:p + flen].decode("utf-8", errors="replace").strip()
            p += flen
            if ftype in "NF":
                try:
                    rec[name] = float(raw) if raw else None
                except ValueError:
                    rec[name] = None
            else:
                rec[name] = raw
        recs.append(rec)
        off += rlen
    return pd.DataFrame(recs)


def run():
    content = http_get(URL, ua="Mozilla/5.0").content
    save_bytes(content, "naturalearth", "ne_110m_admin_0_countries.zip")
    with zipfile.ZipFile(io.BytesIO(content)) as z:
        dbf = next(n for n in z.namelist() if n.lower().endswith(".dbf"))
        df = read_dbf(z.read(dbf))
    df = df[[c for c in KEEP if c in df.columns]].rename(columns=str.lower)
    # ISO_A3 is -99 for a few (France, Norway, Kosovo); fall back to ISO_A3_EH / ADM0_A3.
    df["iso3"] = df["iso_a3"].where(df["iso_a3"] != "-99", df["iso_a3_eh"])
    df["iso3"] = df["iso3"].where(df["iso3"] != "-99", df["adm0_a3"])
    save(df, "naturalearth", "countries")
    return record("naturalearth", "countries", df, url=URL)
