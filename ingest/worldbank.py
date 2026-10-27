"""World Bank WDI API (annual, no key)."""
import pandas as pd

from .common import http_get, record, save

URL = "https://api.worldbank.org/v2/country/{c}/indicator/{i}"
COUNTRIES = "USA;CHN;IND;CAN;MEX;JPN;DEU;FRA;ITA;GBR;KOR;VNM;BRA;EUU;WLD"
INDICATORS = {
    "NE.TRD.GNFS.ZS": "trade_pct_gdp",
    "NE.EXP.GNFS.ZS": "exports_pct_gdp",
    "NE.IMP.GNFS.ZS": "imports_pct_gdp",
    "NY.GDP.MKTP.CD": "gdp_usd",
    "NY.GDP.MKTP.KD.ZG": "gdp_growth_pct",
    "FP.CPI.TOTL.ZG": "inflation_pct",
    "SP.POP.TOTL": "population",
}


def run():
    rows = []
    for ind, name in INDICATORS.items():
        js = http_get(URL.format(c=COUNTRIES, i=ind), params={"format": "json", "date": "2015:2026", "per_page": 2000}).json()
        for d in js[1] or []:
            rows.append({"iso3": d["countryiso3code"], "country": d["country"]["value"], "indicator": ind,
                         "indicator_name": name, "year": int(d["date"]), "value": d["value"]})
    df = pd.DataFrame(rows)
    df["period"] = pd.to_datetime(df.year.astype(str) + "-01-01")
    save(df, "worldbank", "wdi_annual")
    return record("worldbank", "wdi_annual", df, url=URL, date_col="period")
