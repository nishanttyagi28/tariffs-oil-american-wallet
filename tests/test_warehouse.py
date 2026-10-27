"""Smoke tests on the built DuckDB warehouse (star schema + Power BI marts)."""
import pytest

TABLES = [
    "core.dim_date", "core.dim_country", "core.dim_cpi_category", "core.dim_market_instrument", "core.dim_chokepoint",
    "core.fct_trade_monthly", "core.fct_tariff_rate_monthly", "core.fct_customs_revenue_monthly", "core.fct_cpi_monthly",
    "core.fct_macro_monthly", "core.fct_market_daily", "core.fct_oil_daily", "core.fct_chokepoint_daily",
    "powerbi.mart_country_before_after", "powerbi.mart_trade_diversion", "powerbi.mart_household_impact",
    "powerbi.mart_oil_shock", "powerbi.mart_market_event_window",
]


@pytest.mark.parametrize("table", TABLES)
def test_table_non_empty(con, table):
    assert con.execute(f"select count(*) from {table}").fetchone()[0] > 0


def test_us_imports_2024_plausible(con):
    total = con.execute("select sum(imports_musd) from core.fct_trade_monthly where year(month_date)=2024").fetchone()[0]
    assert 3.0e6 < total < 3.5e6  # Census: ~$3.27T goods imports in 2024


def test_hormuz_collapse_visible(con):
    v = con.execute("select last30_vs_prewar_pct from core.dim_chokepoint where chokepoint_name ilike '%Hormuz%'").fetchone()[0]
    assert v < -0.5


def test_dim_date_has_war_phases(con):
    n = con.execute("select count(distinct war_phase_code) from core.dim_date").fetchone()[0]
    assert n >= 3
