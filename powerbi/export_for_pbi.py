"""Export the warehouse tables the Power BI model needs to Parquet in powerbi/data/.

Power BI Desktop reads these with Parquet.Document (root folder = the DataRoot M parameter), so the
DuckDB file is never opened or locked by Desktop. Column names are converted to clean display names
here (e.g. imports_musd -> "Imports $M"), and every "%" column is a fraction (0.05 = 5%).

    python powerbi/export_for_pbi.py
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "warehouse" / "tradewar.duckdb"
OUT = ROOT / "powerbi" / "data"

TOKENS = {"musd": "$M", "usd": "USD", "pct": "%", "pp": "pp", "yoy": "YoY", "mom": "MoM", "iso3": "ISO3", "cpi": "CPI",
          "r12m": "R12M", "ly": "LY", "ann": "Ann.", "id": "ID", "dwt": "DWT", "sma": "SMA", "ytd": "YTD", "eu27": "EU27",
          "wb": "WB", "md": "$M", "gdp": "GDP", "wti": "WTI", "vix": "VIX", "dxy": "DXY", "ust": "UST", "gscpi": "GSCPI",
          "cf": "CF", "lo80": "Lo 80", "hi80": "Hi 80", "lo95": "Lo 95", "hi95": "Hi 95", "ahe": "AHE", "irf": "IRF",
          "car": "CAR", "pce": "PCE", "lo90": "Lo 90", "hi90": "Hi 90", "ci": "CI", "aic": "AIC", "musd_ly": "$M LY", "us": "US", "sa": "SA", "gs": "G&S", "sp500": "S&P 500", "url": "URL", "se": "SE",
          "ets": "ETS", "sarima": "SARIMA", "lightgbm": "LightGBM", "t0": "T0", "k": "K", "dow": "DoW"}
SMALL = {"vs", "per", "of", "since", "in"}
OVERRIDES = {"date_day": "Date", "month_date": "Month", "trade_date": "Date", "obs_date": "Date", "country_iso3": "ISO3",
             "country_name": "Country", "symbol": "Symbol", "series_id": "Series ID", "chokepoint_id": "Chokepoint ID",
             "chokepoint_name": "Chokepoint", "instrument_name": "Instrument", "partner_group": "Partner Group",
             "n_total": "Transits", "n_tanker": "Tanker Transits", "n_total_7d_avg": "Transits 7d Avg",
             "n_tanker_7d_avg": "Tanker Transits 7d Avg", "is_post": "Is Post-Tariff", "flow": "Flow", "partner": "Partner",
             "partner_code": "Partner Code", "category": "Category", "exposure_group": "Exposure Group",
             "exposure_label": "Exposure", "event_id": "Event ID", "event_date": "Event Date", "month": "Month No", "month_label": "Month Label",
             "year_month": "Year-Month", "iso_dow": "Weekday No", "event": "Event", "event_name": "Event Name",
             "significant_5pct": "Significant 5%", "share_of_us_imports": "Share of US Imports", "share_of_us_exports": "Share of US Exports"}


def pretty(c: str) -> str:
    if c in OVERRIDES:
        return OVERRIDES[c]
    parts = c.split("_")
    out = []
    for i, p in enumerate(parts):
        if p in SMALL and i > 0:
            out.append(p)
        elif p in TOKENS:
            out.append(TOKENS[p])
        elif re.fullmatch(r"\d+d", p) or re.fullmatch(r"\d{4}", p):
            out.append(p)
        elif p in ("is", "n"):
            out.append({"is": "Is", "n": "#"}[p])
        else:
            out.append(p.capitalize())
    s = " ".join(out).replace(" %", " %")
    return s


# table name in Power BI -> (SQL, columns that are percent points and must be divided by 100 to become fractions)
TABLES: dict[str, tuple[str, list[str]]] = {
    "Date": ("""
        with d as (select * from core.dim_date where date_day >= date '2019-01-01'),
        last as (select * from core.dim_date order by date_day desc limit 1),
        ext as (
          select cast(g as date) as date_day from generate_series(date '2027-01-01', date '2027-12-31', interval 1 day) t(g)
        )
        select * from d
        union all
        select e.date_day, cast(date_trunc('month', e.date_day) as date), year(e.date_day), quarter(e.date_day), month(e.date_day),
               strftime(e.date_day, '%b %Y'), strftime(e.date_day, '%Y-%m'), isodow(e.date_day), isodow(e.date_day) >= 6, day(e.date_day) = 1,
               l.trade_phase_code, l.trade_phase_order, l.trade_phase, l.war_phase_code, l.war_phase_order, l.war_phase,
               'Other', l.is_war_period
        from ext e cross join last l
        order by 1""", []),
    "Country": ("""
        select *, replace(trim(regexp_replace(regexp_replace(country_name, '\\s*\\(.*\\)', ''), ',\\s*except.*$', '')), 'Burma', 'Myanmar') as map_name
        from core.dim_country""", []),
    "CPI Category": ("select * from core.dim_cpi_category", []),
    "Instrument": ("select * from core.dim_market_instrument", []),
    "Chokepoint": ("select * from core.dim_chokepoint", []),
    "Trade": ("select * from core.fct_trade_monthly where month_date >= date '2019-01-01'", []),
    "Tariff Rate": ("select * from core.fct_tariff_rate_monthly where month_date >= date '2024-01-01' and month_date <= date '2026-12-01'",
                    ["statutory_rate_pct", "max_rate_in_month_pct", "effective_rate_gross_pct", "effective_rate_net_pct"]),
    "Customs": ("select * from core.fct_customs_revenue_monthly where month_date >= date '2019-01-01'",
                ["effective_rate_gross_pct", "effective_rate_net_pct"]),
    "CPI": ("select * from core.fct_cpi_monthly where month_date >= date '2019-01-01'", []),
    "Macro": ("select * from core.fct_macro_monthly where month_date >= date '2019-01-01'",
              ["unemployment_rate_pct", "personal_saving_rate_pct", "mortgage_30y_pct", "fed_funds_pct", "ust_10y_pct", "ust_2y_pct",
               "breakeven_10y_pct", "yield_curve_10y2y_pct"]),
    "Market": ("select * from core.fct_market_daily where trade_date >= date '2023-01-01'", []),
    "Oil": ("select * from core.fct_oil_daily where obs_date >= date '2023-01-01'", []),
    "Chokepoint Daily": ("select * from core.fct_chokepoint_daily where obs_date >= date '2023-01-01'", []),
    "Country Before After": ("select * from powerbi.mart_country_before_after", ["peak_statutory_rate_pct", "current_statutory_rate_pct"]),
    "Trade Diversion": ("select * from powerbi.mart_trade_diversion where month_date >= date '2023-01-01'", []),
    "Household": ("select * from powerbi.mart_household_impact", ["effective_rate_gross_pct"]),
    "Oil Shock": ("select * from powerbi.mart_oil_shock", []),
    "Events": ("""
        select event_id, event_date, 'Tariff' as event_family, measure as event, country_iso3, rate_pct / 100.0 as rate_pct,
               description, source_url from seeds.tariff_events
        union all
        select event_id, event_date, 'Iran war', event, 'IRN', null, category, source_url from seeds.war_events
        order by event_date""", []),
    "Partner": ("""
        select * from (values ('CHN','China','CHN',1), ('CAN','Canada','CAN',2), ('MEX','Mexico','MEX',3),
                              ('EU27','European Union','EUU',4), ('IND','India','IND',5), ('JPN','Japan','JPN',6),
                              ('VNM','Vietnam','VNM',7), ('TWN','Taiwan','TWN',8), ('KOR','South Korea','KOR',9),
                              ('TOTAL','US total','ALL',10)) t(partner_code, partner, tariff_iso3, partner_order)""", []),
    "Trade Metric": ("select * from (values ('Imports',1), ('Exports',2), ('Trade balance',3), ('Total trade',4)) t(metric, metric_order)", []),
    "Counterfactual": ("select * from ml.ml_trade_counterfactual", []),
    "Tariff Effect": ("select split_part(series_id, '|', 1) as partner_code, * from ml.ml_trade_effect_summary", []),
    "Model Metrics": ("select * from ml.ml_model_metrics", []),
    "Pass-through": ("select * from ml.ml_cpi_passthrough", []),
    "Event Study": ("select * from ml.ml_event_study", ["raw_return_pct", "car_pct"]),
    "IRF": ("select * from ml.ml_irf", []),
    "Vol Regimes": ("select * from ml.ml_vol_regimes where trade_date >= date '2024-01-01'", ["garch_vol_ann_pct"]),
    "Forecasts": ("select * from ml.ml_forecasts", []),
}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(DB), read_only=True)
    schema = {}
    for name, (sql, pp_cols) in TABLES.items():
        cur = con.cursor()
        cur.execute(f"select * from ({sql}) limit 0")
        cols = [d[0] for d in cur.description]
        types = [str(d[1]) for d in cur.description]
        cur.close()
        sel = []
        for c in cols:
            expr = f'"{c}" / 100.0' if c in pp_cols else f'"{c}"'
            if c.startswith("is_") or c in ("significant_5pct", "significant_95", "all_days_verified"):
                expr = f'cast("{c}" as boolean)'
            sel.append(f'{expr} as "{pretty(c)}"')
        names = [pretty(c) for c in cols]
        dup = {x for x in names if names.count(x) > 1}
        assert not dup, f"duplicate display names in {name}: {dup}"
        path = OUT / f"{name}.parquet"
        p = str(path).replace("\\", "/")
        con.cursor().execute(f"copy (select {', '.join(sel)} from ({sql})) to '{p}' (format parquet)").close()
        cur = con.cursor()
        n = cur.execute(f"select count(*) from '{p}'").fetchall()[0][0]
        cur.close()
        schema[name] = [{"source": c, "name": pretty(c), "type": t} for c, t in zip(cols, types)]
        print(f"{name:<22} {n:>7,} rows  {len(cols):>3} cols")
    (OUT / "_schema.json").write_text(json.dumps(schema, indent=1), encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()