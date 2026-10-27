"""Builds docs/ml_report.md from the ml.* tables so every number in the report comes from the warehouse."""
from __future__ import annotations

from datetime import datetime

import pandas as pd

from ml.common import ROOT, read


def _md(df: pd.DataFrame) -> str:
    cols = list(df.columns)
    out = ["| " + " | ".join(cols) + " |", "|" + "|".join("---" for _ in cols) + "|"]
    for r in df.itertuples(index=False):
        out.append("| " + " | ".join("" if pd.isna(v) else (f"{v:,.2f}" if isinstance(v, float) else str(v).replace("|", "\\|")) for v in r) + " |")
    return "\n".join(out)


def _bn(x):
    return ("-" if x < 0 else "") + f"${abs(x) / 1e3:,.0f}bn"


def build(timings: dict | None = None) -> None:
    met = read("select * from ml.ml_model_metrics where task = 'trade_counterfactual'")
    wide = met.pivot_table(index=["series_id", "model", "is_best"], columns="metric", values="value").reset_index()
    best = wide[wide.is_best][["series_id", "model", "wape", "mape", "smape"]].sort_values("series_id")
    by_model = wide.groupby("model")[["wape", "mape", "smape"]].mean().reset_index().sort_values("wape")
    eff = read("select * from ml.ml_trade_effect_summary")
    key = ["CHN|imports", "IND|imports", "CAN|imports", "EU27|imports", "MEX|imports", "VNM|imports", "TWN|imports", "TOTAL|imports",
           "CHN|exports", "TOTAL|exports"]
    e = eff[(eff.effect_window == "Apr 2025-latest") & eff.series_id.isin(key)].copy()
    e["order"] = e.series_id.map({k: i for i, k in enumerate(key)})
    e = e.sort_values("order")
    et = pd.DataFrame({"series": e.series_id, "model": e.best_model, "months": e.months,
                       "actual": e.actual_musd.map(_bn), "counterfactual": e.counterfactual_musd.map(_bn),
                       "effect": e.effect_musd.map(_bn), "effect %": (100 * e.effect_pct).round(1),
                       "95% interval": [f"{_bn(a)} to {_bn(b)}" for a, b in zip(e.effect_lo95, e.effect_hi95)],
                       "80% interval": [f"{_bn(a)} to {_bn(b)}" for a, b in zip(e.effect_lo80, e.effect_hi80)],
                       "sig. 95%": e.significant_95})
    pt = read("select * from ml.ml_cpi_passthrough")
    did = pt[~pt.spec.isin(["event_study"])][["spec", "term", "coef", "ci_lo", "ci_hi", "p_value", "annualised_coef", "n_obs"]]
    main = pt[pt.spec == "did_main"].iloc[0]
    inten = pt[(pt.spec == "intensity_treated") & (pt.term == "d12_tariff_l3")].iloc[0]
    es = read("select * from ml.ml_event_study")
    w = es[(es.event_id == "W02") & es.window_label.isin(["D+5", "D+20"])].pivot_table(index=["symbol", "instrument_name"], columns="window_label",
                                                                                        values=["car_pct", "t_stat"]).round(2)
    w.columns = [f"{a} {b}" for a, b in w.columns]
    w = w.reset_index()
    lib = es[(es.event_id == "T05") & (es.window_label == "D+5") & (es.asset_class == "equity_index")][["instrument_name", "car_pct", "t_stat"]].round(2)
    irf = read("select * from ml.ml_irf")
    irft = irf[irf.horizon_months.isin([0, 3, 6, 12])][["outcome_label", "horizon_months", "irf", "ci_lo95", "ci_hi95"]].round(3)
    vr = read("select * from ml.ml_model_metrics where task = 'vol_regimes'").pivot_table(index="series_id", columns="metric", values="value").reset_index().round(2)
    vs = read("select symbol, war_phase, avg(case when prob_high_vol > 0.5 then 1.0 else 0 end) as share_high from ml.ml_vol_regimes where trade_date >= date '2025-06-01' group by all")
    vs = vs.pivot(index="symbol", columns="war_phase", values="share_high").round(2).reset_index()
    fc = read("select * from ml.ml_forecasts")
    f = fc[fc.kind.isin(["forecast", "forecast_alt"])][["target", "model", "month_date", "value", "lo80", "hi80", "lo95", "hi95", "yoy_value"]].round(3)
    q4 = fc[(fc.target == "brent") & (fc.kind.isin(["actual", "forecast"])) & (pd.to_datetime(fc.month_date) >= "2026-10-01") & (pd.to_datetime(fc.month_date) <= "2026-12-01")]
    q4m = q4.groupby("month_date")["value"].mean().mean() if len(q4) else float("nan")  # Oct-Dec: actual where known, else forecast
    hc = fc[(fc.target == "headline_cpi") & (fc.kind == "forecast")]

    def g(sid):
        return eff[(eff.effect_window == "Apr 2025-latest") & (eff.series_id == sid)].iloc[0]
    chn, tot, twn, vnm = g("CHN|imports"), g("TOTAL|imports"), g("TWN|imports"), g("VNM|imports")
    gas = irf[(irf.outcome == "gasoline_cpi")].set_index("horizon_months")
    hcp = irf[(irf.outcome == "headline_cpi")].set_index("horizon_months")
    brent_car = es[(es.event_id == "W02") & (es.symbol == "BZ=F") & (es.window_label == "D+5")].iloc[0]
    spx_car = es[(es.event_id == "W02") & (es.symbol == "^GSPC") & (es.window_label == "D+20")].iloc[0]

    md = f"""# ML & forecasting report - Tariffs, Oil & the American Wallet

_Generated {datetime.now():%Y-%m-%d %H:%M} IST by `python -m ml.run_all`. All numbers are read from the `ml` schema of `warehouse/tradewar.duckdb`._

## Plain-English findings

1. **China lost about {abs(chn.effect_pct) * 100:.0f}% of its expected US sales.** From Apr 2025 to the latest month, US imports from China were
   {_bn(chn.actual_musd)}, against a no-tariff counterfactual of {_bn(chn.counterfactual_musd)}. That is an effect of {_bn(chn.effect_musd)}
   (95% interval {_bn(chn.effect_lo95)} to {_bn(chn.effect_hi95)}).
2. **Trade was diverted, not just destroyed.** Taiwan ({_bn(twn.effect_musd)}, {twn.effect_pct * 100:+.0f}%) and Vietnam
   ({_bn(vnm.effect_musd)}, {vnm.effect_pct * 100:+.0f}%) sit well above their counterfactuals. Total US imports came in {_bn(tot.effect_musd)} ({tot.effect_pct * 100:+.1f}%)
   below the counterfactual, but the 95% interval ({_bn(tot.effect_lo95)} to {_bn(tot.effect_hi95)}) includes zero, so the net effect on total imports is not clearly different from zero.
3. **Tariffs showed up in shelf prices.** After Feb 2025, tariff-exposed CPI goods inflated {main.annualised_coef:.1f} pp a year faster than domestic goods and services
   (DiD, 95% CI {main.ci_lo * 12:.1f} to {main.ci_hi * 12:.1f} pp, p = {main.p_value:.3f}). A placebo test with a fake Feb 2023 start finds no effect.
   A 1 pp rise in the effective tariff rate goes with roughly {inten.coef:.2f} pp higher YoY inflation in exposed categories (95% CI {inten.ci_lo:.2f} to {inten.ci_hi:.2f}).
4. **The Iran war was a classic oil shock.** Over D0..D+5 Brent's abnormal return was {brent_car.car_pct:+.1f}% (t = {brent_car.t_stat:.1f}).
   Over D0..D+20 the S&P 500's was {spx_car.car_pct:+.1f}% (t = {spx_car.t_stat:.1f}). Historically, a +10% Brent month lifts gasoline CPI by {gas.loc[3, 'irf']:.1f}% after 3 months (95% CI {gas.loc[3, 'ci_lo95']:.1f}-{gas.loc[3, 'ci_hi95']:.1f}%)
   and headline CPI by {hcp.loc[6, 'irf']:.1f}% after 6 months.
5. **Outlook.** A random-walk-type ARIMA keeps Brent near current levels, about ${q4m:,.1f}/bbl on average in Q4 2026 (Oct actual + Nov-Dec forecast), while EIA's Oct-2026 STEO has $105.
   A mean-reverting AR(1) alternative sits between the two. Headline CPI is projected at {hc.yoy_value.iloc[0] * 100:.1f}% YoY in {pd.to_datetime(hc.month_date.iloc[0]):%b %Y}
   and {hc.yoy_value.iloc[-1] * 100:.1f}% in {pd.to_datetime(hc.month_date.iloc[-1]):%b %Y} (95% PI {hc.yoy_lo95.iloc[-1] * 100:.1f}-{hc.yoy_hi95.iloc[-1] * 100:.1f}%).

## 1. Counterfactual 'no-tariff' trade (ml_trade_counterfactual, ml_trade_effect_summary)

**Method.** There are 20 series: imports and exports for China, Canada, Mexico, EU-27, India, Japan, Vietnam, Taiwan, South Korea and the US total.
Four candidates are compared:
- seasonal naive
- damped additive ETS on log levels
- SARIMA(1,1,1)(0,1,1)12 on log levels
- a global LightGBM on seasonal log-differences, with lags 1-3, 6 and 12, month, series id, a Covid flag, GSCPI and the lagged USD YoY, forecast recursively

Selection uses a rolling-origin backtest: 5 origins (Dec-2021 to Dec-2023) with a 12-month horizon, all pre-2025. The best model per series by mean WAPE
is refit on data through **Jan 2025** and projected forward. Prediction intervals come from the empirical quantiles of that model's backtest log-errors, scaled by sqrt(h).
Cumulative intervals add up the monthly bounds, which is conservative.

**Backtest, best model per series**

{_md(best.round(2))}

**Mean backtest error by model (all series)**

{_md(by_model.round(2))}

**Tariff effect, Apr 2025 to latest month (actual - counterfactual)**

{_md(et)}

![trade](figures/trade_counterfactual.png)

## 2. CPI pass-through (ml_cpi_passthrough)

**Method.** The panel is BLS CPI categories (NSA). Each category is de-seasonalised by removing its 2017-2024 calendar-month mean, and the outcome is the monthly log change (pp).
- Treated: 13 tariff-exposed goods (apparel, footwear, furniture, appliances, new vehicles, computers, toys, coffee and others).
- Control: domestic services and used cars.
- Excluded: energy, food and airline fares, because the 2026 oil shock would contaminate them.

The regression has category and month fixed effects, with SEs clustered by category (or by month as a check).

{_md(did.round(4))}

![cpi](figures/cpi_event_study.png)

**Reading.** Before Feb 2025 the event-study coefficients bounce around zero and none is significant, so there is no clear pre-trend. The largest effect is in the
second quarter after the tariffs began, which is Liberation Day and the 145% China peak. In the falsification test, domestic categories show a *negative* tariff
coefficient. That points to common shocks, such as services disinflation, loading onto the tariff-rate variable, so read the intensity coefficient as an association, not a causal elasticity.

## 3. Oil shock: event study (ml_event_study) and local projections (ml_irf)

**Method.**
- Equity indices: market model vs the S&P 500.
- The S&P 500, FX, commodities, VIX and ^TNX: constant-mean model.
- War events share one pre-war estimation window (2 Jun 2025 to 30 Jan 2026). Tariff events use [t0-280, t0-30] trading days.
- CAR t = CAR / (sigma * sqrt(L)).

**Iran war start (W02, t0 = first trading day on or after 28 Feb 2026)**

{_md(w)}

**Liberation Day (T05) - equity indices, D0..D+5 CAR %**

{_md(lib)}

**Local projections (2015-2026, monthly, HAC SEs): response to a +10% Brent month**

{_md(irft)}

![war](figures/event_study_war.png)
![irf](figures/irf_brent.png)

## 4. Volatility regimes (ml_vol_regimes)

The models are a 2-state Markov-switching mean/variance model on daily % returns (2018 onward) and a GARCH(1,1) with Student-t errors.

{_md(vr)}

**Share of trading days in the high-vol regime, by war phase (Jun 2025 onward)**

{_md(vs)}

![regimes](figures/vol_regimes.png)

## 5. Forward forecasts (ml_forecasts)

- **Brent:** ARIMA(1,1,0) on log monthly average (primary), with a mean-reverting AR(1) alternative. EIA STEO (6 Oct 2026) reference: 4Q26 $105/b, 2Q27 $87/b, 2027 average $84/b.
- **Gasoline CPI and headline CPI:** SARIMAX with log Brent as an exogenous variable. Their intervals are *conditional* on the Brent point path, so they understate the true uncertainty.

{_md(f)}

![fc](figures/forecasts.png)

## Limitations (read before quoting)

- **Short post-period:** 17-19 months of tariffs and 8 months of war. Counterfactuals 12-19 months out sit at the edge of what the backtest covers.
- **Confounders:**
  - Front-loading in Q1 2025.
  - The AI and semiconductor import boom, which drives Taiwan and is not a tariff effect.
  - The USD decline and Section 232 sector tariffs.
  - The Oct-2025 federal shutdown gap in CPI data.
  - From Mar 2026, the war overlaps the tariff period, so CPI effects after that date mix both shocks.
- **Headline tariff rates** are statutory. Exemptions (USMCA, Annex II, Section 232 stacking) mean the effective rate is lower; see SQL query 14.
- The DiD assumes parallel trends between exposed goods and domestic categories. Pre-period coefficients support this but are noisy (13 vs 7 categories).
- Event-study t-stats assume i.i.d. abnormal returns. Overlapping war events (Hormuz closure, IEA release) blur the windows.
- Forecasts are statistical baselines, not structural oil-market models.

## Reproducibility

`python -m ml.run_all` runs after `dbt build`. Experiment logs are in `ml/experiments/*.json`. Runtime on a 2-core laptop: {", ".join(f"{k} {v:.0f}s" for k, v in (timings or {}).items()) or "n/a"}.
"""
    (ROOT / "docs" / "ml_report.md").write_text(md, encoding="utf-8", newline="\n")
    print("  -> docs/ml_report.md")


if __name__ == "__main__":
    build()
