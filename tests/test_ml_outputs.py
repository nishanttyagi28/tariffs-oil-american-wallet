"""Smoke tests on the ML outputs written to the ml schema by `python -m ml.run_all`."""
import pytest

ML_TABLES = ["ml_trade_counterfactual", "ml_trade_effect_summary", "ml_model_metrics", "ml_cpi_passthrough",
             "ml_event_study", "ml_irf", "ml_vol_regimes", "ml_forecasts"]


@pytest.fixture(scope="module")
def ml(con):
    have = {r[0] for r in con.execute("select table_name from information_schema.tables where table_schema='ml'").fetchall()}
    if not set(ML_TABLES) <= have:
        pytest.skip("ml tables not built (run python -m ml.run_all)")
    return con


@pytest.mark.parametrize("t", ML_TABLES)
def test_ml_table_non_empty(ml, t):
    assert ml.execute(f"select count(*) from ml.{t}").fetchone()[0] > 0


def test_every_trade_series_has_a_best_model(ml):
    n = ml.execute("select count(distinct series_id) from ml.ml_model_metrics where task='trade_counterfactual' and is_best").fetchone()[0]
    assert n == 20


def test_backtest_wape_reasonable(ml):
    w = ml.execute("select max(value) from ml.ml_model_metrics where task='trade_counterfactual' and is_best and metric='wape'").fetchone()[0]
    assert w < 25


def test_counterfactual_starts_feb_2025(ml):
    d = ml.execute("select min(month_date) from ml.ml_trade_counterfactual where is_post").fetchone()[0]
    assert str(d) == "2025-02-01"


def test_placebo_not_significant(ml):
    p = ml.execute("select p_value from ml.ml_cpi_passthrough where spec='placebo_post_feb2023'").fetchone()[0]
    assert p > 0.05


def test_brent_jumps_on_war_start(ml):
    car = ml.execute("select car_pct from ml.ml_event_study where event_id='W02' and symbol='BZ=F' and window_label='D+5'").fetchone()[0]
    assert car > 10


def test_irf_gasoline_positive(ml):
    v = ml.execute("select irf from ml.ml_irf where outcome='gasoline_cpi' and horizon_months=1").fetchone()[0]
    assert v > 0


def test_forecast_horizon_reaches_mar_2027(ml):
    d = ml.execute("select max(month_date) from ml.ml_forecasts where target='brent' and kind='forecast'").fetchone()[0]
    assert str(d) == "2027-03-01"


def test_report_exists():
    from pathlib import Path
    p = Path(__file__).resolve().parents[1] / "docs" / "ml_report.md"
    assert p.exists() and "Limitations" in p.read_text(encoding="utf-8")
