"""NY Fed Global Supply Chain Pressure Index (monthly, no key)."""
import io

import pandas as pd

from .common import http_get, record, save, save_bytes

URL = "https://www.newyorkfed.org/medialibrary/research/interactives/gscpi/downloads/gscpi_data.xlsx"


def run():
    content = http_get(URL, ua="Mozilla/5.0").content
    save_bytes(content, "gscpi", "gscpi_data.xlsx")
    sheets = pd.read_excel(io.BytesIO(content), sheet_name=None, header=None)
    best = None
    for name, s in sheets.items():
        for i in range(min(10, len(s))):
            d = pd.to_datetime(s.iloc[:, 0], errors="coerce", format="mixed")
            v = pd.to_numeric(s.iloc[:, 1], errors="coerce")
            ok = d.notna() & v.notna()
            if ok.sum() > 100:
                best = pd.DataFrame({"period": d[ok].values, "gscpi": v[ok].values})
                break
        if best is not None:
            break
    if best is None:
        raise RuntimeError("could not locate GSCPI series in workbook")
    best["period"] = pd.to_datetime(best["period"]).dt.to_period("M").dt.to_timestamp()
    best = best.drop_duplicates("period")
    save(best, "gscpi", "gscpi_monthly")
    return record("gscpi", "gscpi_monthly", best, url=URL, date_col="period")
