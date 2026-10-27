"""Counterfactual 'no-tariff' US trade forecasts per major partner.

Each series (partner x imports/exports, $M NSA) is forecast from data through Jan 2025 (before the first
IEEPA tariffs) with four candidate models. Candidates are compared in a rolling-origin backtest on
pre-2025 data (5 origins, 12-month horizon); the best model by mean WAPE is refit through Jan 2025 and
projected to the latest month. Tariff effect = actual - counterfactual. Prediction intervals are
empirical: quantiles of the best model's backtest log-errors, scaled by sqrt(horizon).
"""
from __future__ import annotations

import warnings

import lightgbm as lgb
import numpy as np
import pandas as pd
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from statsmodels.tsa.statespace.sarimax import SARIMAX

from ml.common import FIG_DIR, TARIFF_START, log_experiment, mape, read, setup_matplotlib, smape, wape, write

warnings.filterwarnings("ignore")

PARTNERS = {"CHN": "China", "CAN": "Canada", "MEX": "Mexico", "EU27": "European Union", "IND": "India",
            "JPN": "Japan", "VNM": "Vietnam", "TWN": "Taiwan", "KOR": "South Korea", "TOTAL": "US total"}
TRAIN_END = pd.Timestamp("2025-01-01")
ORIGINS = [pd.Timestamp(x) for x in ("2021-12-01", "2022-06-01", "2022-12-01", "2023-06-01", "2023-12-01")]
H_BT = 12
MODELS = ["seasonal_naive", "ets", "sarima", "lightgbm"]


def load_series() -> tuple[dict[str, pd.Series], pd.DataFrame]:
    t = read("""select t.month_date, t.country_iso3, t.imports_musd, t.exports_musd, d.is_eu27
                from core.fct_trade_monthly t join core.dim_country d using (country_iso3)""")
    t["month_date"] = pd.to_datetime(t["month_date"])
    out = {}
    for flow in ("imports", "exports"):
        col = f"{flow}_musd"
        for code in PARTNERS:
            if code == "TOTAL":
                s = t.groupby("month_date")[col].sum()
            elif code == "EU27":
                s = t[t["is_eu27"]].groupby("month_date")[col].sum()
            else:
                s = t[t["country_iso3"] == code].set_index("month_date")[col]
            s = s.sort_index().asfreq("MS")
            out[f"{code}|{flow}"] = s[s.index >= "2015-01-01"].astype(float)
    m = read("select month_date, gscpi, usd_broad_index from core.fct_macro_monthly")
    m["month_date"] = pd.to_datetime(m["month_date"])
    exog = m.set_index("month_date").sort_index().asfreq("MS").ffill()
    return out, exog


# ---------------- candidate models (all on log levels) ----------------
def f_snaive(y: pd.Series, idx: pd.DatetimeIndex) -> np.ndarray:
    last = y.index[-1]
    vals = []
    for d in idx:
        k = int(np.ceil(((d.year - last.year) * 12 + d.month - last.month) / 12))
        vals.append(y.loc[d - pd.DateOffset(months=12 * k)])
    return np.asarray(vals)


def f_ets(y: pd.Series, idx) -> np.ndarray:
    m = ExponentialSmoothing(np.log(y.values), trend="add", damped_trend=True, seasonal="add", seasonal_periods=12)
    return np.exp(m.fit(optimized=True).forecast(len(idx)))


def f_sarima(y: pd.Series, idx) -> np.ndarray:
    m = SARIMAX(np.log(y.values), order=(1, 1, 1), seasonal_order=(0, 1, 1, 12))
    return np.exp(m.fit(disp=False, maxiter=200).forecast(len(idx)))


def _features(ly: pd.Series, exog: pd.DataFrame, code: int) -> pd.DataFrame:
    sd = ly - ly.shift(12)
    df = pd.DataFrame({"sd": sd})
    for k in (1, 2, 3, 6):
        df[f"sd_l{k}"] = sd.shift(k)
    df["sd_l12"] = sd.shift(12)
    df["month"] = ly.index.month
    df["series"] = code
    df["covid"] = ((ly.index >= "2020-03-01") & (ly.index <= "2021-12-01")).astype(int)
    df["gscpi"] = exog["gscpi"].reindex(ly.index).values
    usd = np.log(exog["usd_broad_index"])
    df["usd_yoy_l12"] = (usd - usd.shift(12)).shift(12).reindex(ly.index).values
    return df


FEATS = ["sd_l1", "sd_l2", "sd_l3", "sd_l6", "sd_l12", "month", "series", "covid", "gscpi", "usd_yoy_l12"]


def f_lgbm_all(series: dict[str, pd.Series], exog: pd.DataFrame, origin: pd.Timestamp, h: int) -> dict[str, np.ndarray]:
    """Global LightGBM on seasonal log-differences, recursive multi-step forecast for every series."""
    keys = list(series)
    frames = []
    for i, k in enumerate(keys):
        ly = np.log(series[k][series[k].index <= origin])
        frames.append(_features(ly, exog, i).dropna(subset=["sd", "sd_l1", "sd_l12"]))
    tr = pd.concat(frames)
    model = lgb.LGBMRegressor(n_estimators=400, learning_rate=0.03, num_leaves=15, min_child_samples=15,
                              subsample=0.8, subsample_freq=1, colsample_bytree=0.8, n_jobs=2, verbose=-1)
    model.fit(tr[FEATS], tr["sd"], categorical_feature=["series"])
    idx = pd.date_range(origin + pd.DateOffset(months=1), periods=h, freq="MS")
    out = {}
    for i, k in enumerate(keys):
        ly = np.log(series[k][series[k].index <= origin]).copy()
        for d in idx:
            ext = pd.concat([ly, pd.Series([np.nan], index=[d])])
            row = _features(ext, exog, i).iloc[[-1]].copy()
            row["covid"] = 0
            sd_hat = float(model.predict(row[FEATS])[0])
            ly.loc[d] = ext.loc[d - pd.DateOffset(months=12)] + sd_hat
        out[k] = np.exp(ly.loc[idx].values)
    return out


def forecast_all(series, exog, origin, h) -> dict[str, dict[str, np.ndarray]]:
    idx = pd.date_range(origin + pd.DateOffset(months=1), periods=h, freq="MS")
    res = {k: {} for k in series}
    for k, s in series.items():
        y = s[s.index <= origin]
        res[k]["seasonal_naive"] = f_snaive(y, idx)
        res[k]["ets"] = f_ets(y, idx)
        res[k]["sarima"] = f_sarima(y, idx)
    for k, f in f_lgbm_all(series, exog, origin, h).items():
        res[k]["lightgbm"] = f
    return res


def run() -> dict:
    series, exog = load_series()
    # ---------- rolling-origin backtest ----------
    rows, errs = [], []
    for o in ORIGINS:
        print(f"  backtest origin {o:%Y-%m}")
        fc = forecast_all(series, exog, o, H_BT)
        idx = pd.date_range(o + pd.DateOffset(months=1), periods=H_BT, freq="MS")
        for k, models in fc.items():
            y = series[k].reindex(idx).values
            for m, f in models.items():
                rows.append({"series_id": k, "model": m, "origin": o, "mape": mape(y, f), "wape": wape(y, f), "smape": smape(y, f)})
                for h, (yy, ff) in enumerate(zip(y, f), start=1):
                    errs.append({"series_id": k, "model": m, "h": h, "log_err": np.log(yy) - np.log(ff)})
    bt = pd.DataFrame(rows)
    er = pd.DataFrame(errs)
    agg = bt.groupby(["series_id", "model"], as_index=False)[["mape", "wape", "smape"]].mean()
    agg["rank"] = agg.groupby("series_id")["wape"].rank(method="first")
    best = agg[agg["rank"] == 1].set_index("series_id")["model"].to_dict()

    # ---------- final counterfactual from Jan 2025 ----------
    last = max(s.last_valid_index() for s in series.values())
    h = (last.year - TRAIN_END.year) * 12 + last.month - TRAIN_END.month
    print(f"  counterfactual {TRAIN_END:%Y-%m} -> {last:%Y-%m} ({h} months)")
    fc = forecast_all(series, exog, TRAIN_END, h)
    idx = pd.date_range(TRAIN_END + pd.DateOffset(months=1), periods=h, freq="MS")
    out = []
    for k, s in series.items():
        m = best[k]
        e = er[(er.series_id == k) & (er.model == m)]
        z = e["log_err"] / np.sqrt(e["h"])
        q = {p: float(np.quantile(z, p)) for p in (0.025, 0.10, 0.90, 0.975)}
        code, flow = k.split("|")
        for d in s.index[s.index >= "2023-01-01"]:
            out.append({"series_id": k, "partner_code": code, "partner": PARTNERS[code], "flow": flow, "month_date": d,
                        "actual_musd": s.loc[d], "is_post": False})
        for i, d in enumerate(idx):
            f = fc[k][m][i]
            sh = np.sqrt(i + 1)
            r = {"series_id": k, "partner_code": code, "partner": PARTNERS[code], "flow": flow, "month_date": d,
                 "actual_musd": s.get(d, np.nan), "is_post": True, "best_model": m, "horizon": i + 1,
                 "counterfactual_musd": f,
                 "cf_lo80": f * np.exp(q[0.10] * sh), "cf_hi80": f * np.exp(q[0.90] * sh),
                 "cf_lo95": f * np.exp(q[0.025] * sh), "cf_hi95": f * np.exp(q[0.975] * sh)}
            for mm in MODELS:
                r[f"cf_{mm}"] = fc[k][mm][i]
            out.append(r)
    df = pd.DataFrame(out)
    df = df[~((df.is_post == False) & (df.month_date >= idx[0]))]  # noqa: E712  (post rows replace actual-only rows)
    df["effect_musd"] = df["actual_musd"] - df["counterfactual_musd"]
    df["effect_lo95"] = df["actual_musd"] - df["cf_hi95"]
    df["effect_hi95"] = df["actual_musd"] - df["cf_lo95"]
    df["effect_lo80"] = df["actual_musd"] - df["cf_hi80"]
    df["effect_hi80"] = df["actual_musd"] - df["cf_lo80"]
    df["effect_pct"] = df["effect_musd"] / df["counterfactual_musd"]
    df["month_date"] = pd.to_datetime(df["month_date"]).dt.date
    df = df.sort_values(["series_id", "month_date"]).reset_index(drop=True)

    # ---------- cumulative effect summary ----------
    summ = []
    p = df[df.is_post & df.actual_musd.notna()].copy()
    p["month_date"] = pd.to_datetime(p["month_date"])
    for window, start in (("Feb 2025-latest", "2025-02-01"), ("Apr 2025-latest", "2025-04-01")):
        g = p[p.month_date >= start].groupby(["series_id", "partner", "flow", "best_model"], as_index=False).agg(
            months=("month_date", "count"), actual_musd=("actual_musd", "sum"), counterfactual_musd=("counterfactual_musd", "sum"),
            cf_lo95=("cf_lo95", "sum"), cf_hi95=("cf_hi95", "sum"), cf_lo80=("cf_lo80", "sum"), cf_hi80=("cf_hi80", "sum"))
        g["window"] = window
        summ.append(g)
    s = pd.concat(summ)
    s["effect_musd"] = s.actual_musd - s.counterfactual_musd
    s["effect_pct"] = s.effect_musd / s.counterfactual_musd
    # comonotonic (conservative) interval: sum of monthly bounds
    s["effect_lo95"], s["effect_hi95"] = s.actual_musd - s.cf_hi95, s.actual_musd - s.cf_lo95
    s["effect_lo80"], s["effect_hi80"] = s.actual_musd - s.cf_hi80, s.actual_musd - s.cf_lo80
    s["significant_95"] = (s.effect_lo95 > 0) | (s.effect_hi95 < 0)

    metrics = agg.rename(columns={"rank": "rank_wape"})
    metrics["is_best"] = metrics["rank_wape"] == 1
    metrics["task"] = "trade_counterfactual"
    metrics["n_folds"] = len(ORIGINS)
    metrics["horizon_months"] = H_BT
    write(df, "ml_trade_counterfactual")
    write(s.reset_index(drop=True), "ml_trade_effect_summary")
    _plot(df)
    best_tbl = metrics[metrics.is_best][["series_id", "model", "mape", "wape", "smape"]]
    log_experiment("trade_counterfactual", {"train_end": str(TRAIN_END.date()), "origins": [str(o.date()) for o in ORIGINS],
                   "horizon_bt": H_BT, "models": MODELS, "lgbm": "global, seasonal log-diff, recursive"},
                   {"best": best_tbl.to_dict("records"),
                    "mean_wape_by_model": agg.groupby("model")["wape"].mean().round(2).to_dict()},
                   ["docs/figures/trade_counterfactual.png"])
    return {"metrics": metrics, "summary": s, "best": best_tbl}


def _plot(df: pd.DataFrame) -> None:
    plt = setup_matplotlib()
    keys = ["CHN|imports", "IND|imports", "CAN|imports", "EU27|imports", "VNM|imports", "TOTAL|imports"]
    fig, axes = plt.subplots(2, 3, figsize=(13, 6.5))
    for ax, k in zip(axes.flat, keys):
        d = df[df.series_id == k].copy()
        d["month_date"] = pd.to_datetime(d["month_date"])
        p = d[d.is_post]
        ax.plot(d.month_date, d.actual_musd / 1e3, color="#1f3b73", lw=1.6, label="Actual")
        ax.plot(p.month_date, p.counterfactual_musd / 1e3, color="#d9822b", lw=1.4, ls="--", label=f"No-tariff counterfactual ({p.best_model.iloc[0]})")
        ax.fill_between(p.month_date, p.cf_lo95 / 1e3, p.cf_hi95 / 1e3, color="#d9822b", alpha=0.15, label="95% interval")
        ax.fill_between(p.month_date, p.cf_lo80 / 1e3, p.cf_hi80 / 1e3, color="#d9822b", alpha=0.25)
        ax.axvline(TARIFF_START, color="grey", lw=0.8, ls=":")
        ax.set_title(f"{d.partner.iloc[0]} - US imports ($bn/month)")
        ax.legend(fontsize=7, loc="lower left")
    fig.suptitle("Actual vs 'no-tariff' counterfactual (trained through Jan 2025)", fontsize=11)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "trade_counterfactual.png")
    plt.close(fig)


if __name__ == "__main__":
    r = run()
    print(r["best"].round(2).to_string())