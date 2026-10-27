"""Forward forecasts with prediction intervals.

- Brent (monthly average, $/bbl): ARIMA(1,1,0) on log price (2015+), Nov 2026 - Mar 2027; compared with
  EIA STEO (6 Oct 2026): 4Q26 $105/b, 2Q27 $87/b, 2027 average $84/b.
- Gasoline CPI (NSA): SARIMAX(1,1,0)(1,0,0,12) on log index with log-Brent exogenous (Brent path = point
  forecast above; intervals are conditional on that path).
- Headline CPI (SA, CPIAUCSL): SARIMAX(1,1,1) on log index with log-Brent exogenous; next 6 months, as
  level and YoY.
"""
from __future__ import annotations

import warnings

import numpy as np
import pandas as pd
from statsmodels.tsa.statespace.sarimax import SARIMAX

from ml.common import FIG_DIR, log_experiment, read, setup_matplotlib, write

warnings.filterwarnings("ignore")
END = pd.Timestamp("2027-03-01")
EIA = [("2026-10-01", 105.0, "EIA STEO Oct-2026: 4Q26 avg"), ("2026-11-01", 105.0, "EIA STEO Oct-2026: 4Q26 avg"),
       ("2026-12-01", 105.0, "EIA STEO Oct-2026: 4Q26 avg"), ("2027-04-01", 87.0, "EIA STEO Oct-2026: 2Q27 avg"),
       ("2027-05-01", 87.0, "EIA STEO Oct-2026: 2Q27 avg"), ("2027-06-01", 87.0, "EIA STEO Oct-2026: 2Q27 avg")]


def _frame(target, label, unit, model, idx, mean, ci80, ci95, transform=np.exp):
    return pd.DataFrame({"target": target, "target_label": label, "unit": unit, "model": model, "kind": "forecast",
                         "month_date": idx, "value": transform(mean), "lo80": transform(ci80[:, 0]), "hi80": transform(ci80[:, 1]),
                         "lo95": transform(ci95[:, 0]), "hi95": transform(ci95[:, 1])})


def _fc(res, steps, exog=None):
    f = res.get_forecast(steps, exog=exog)
    return np.asarray(f.predicted_mean), np.asarray(f.conf_int(alpha=0.2)), np.asarray(f.conf_int(alpha=0.05))


def run() -> dict:
    o = read("select obs_date, brent_usd from core.fct_oil_daily where brent_usd is not null and obs_date >= date '2015-01-01'")
    o["month_date"] = pd.to_datetime(o.obs_date).dt.to_period("M").dt.to_timestamp()
    brent = o.groupby("month_date")["brent_usd"].mean().asfreq("MS")
    last_b = brent.index[-1]
    hb = (END.year - last_b.year) * 12 + END.month - last_b.month
    rb = SARIMAX(np.log(brent.values), order=(1, 1, 0)).fit(disp=False)
    bidx = pd.date_range(last_b + pd.DateOffset(months=1), periods=hb, freq="MS")
    m, c80, c95 = _fc(rb, hb)
    fb = _frame("brent", "Brent crude, monthly avg", "USD/bbl", "ARIMA(1,1,0) log", bidx, m, c80, c95)
    brent_path = pd.concat([brent, pd.Series(np.exp(m), index=bidx)])
    # alternative: mean-reverting AR(1) on log level (2015+), shown for comparison only
    ra = SARIMAX(np.log(brent.values), order=(1, 0, 0), trend="c").fit(disp=False)
    m2, c80b, c95b = _fc(ra, hb)
    fb2 = _frame("brent", "Brent crude, monthly avg", "USD/bbl", "AR(1) mean-reverting log", bidx, m2, c80b, c95b)
    fb2["kind"] = "forecast_alt"

    cpi = read("""select f.month_date, f.index_value as gas, m.cpi_sa from core.fct_cpi_monthly f
                  left join core.fct_macro_monthly m using (month_date) where f.series_id = 'CUUR0000SETB01'""")
    cpi["month_date"] = pd.to_datetime(cpi.month_date)
    cpi = cpi.set_index("month_date").sort_index().asfreq("MS")
    cpi = cpi[cpi.index >= "2015-01-01"]
    outs = [fb, fb2]
    models = {}
    for col, label, order, sorder in (("gas", "Gasoline CPI (NSA index)", (1, 1, 0), (1, 0, 0, 12)),
                                      ("cpi_sa", "Headline CPI (SA index)", (1, 1, 1), (0, 0, 0, 0))):
        y = cpi[col].dropna()
        last = y.index[-1]
        h = (END.year - last.year) * 12 + END.month - last.month if col == "gas" else 6
        x = np.log(brent_path.reindex(y.index))
        res = SARIMAX(np.log(y.values), exog=x.values, order=order, seasonal_order=sorder).fit(disp=False)
        idx = pd.date_range(last + pd.DateOffset(months=1), periods=h, freq="MS")
        xf = np.log(brent_path.reindex(idx).ffill()).values.reshape(-1, 1)
        m, c80, c95 = _fc(res, h, xf)
        f = _frame(col if col == "gas" else "headline_cpi", label, "index", f"SARIMAX{order}{sorder[:3] if sorder[3] else ''} + log Brent", idx, m, c80, c95)
        yi = y.asfreq("MS").interpolate()  # Oct-2025 CPI was not published (federal shutdown); interpolate the YoY base only
        base = yi.reindex(idx - pd.DateOffset(months=12)).values
        for k in ("value", "lo80", "hi80", "lo95", "hi95"):
            f[f"yoy_{k}"] = f[k] / base - 1
        outs.append(f)
        models[col] = {"aic": float(res.aic), "brent_coef": float(res.params[1]) if len(res.params) > 1 else None}
        hist = y[y.index >= "2023-01-01"]
        hy = (hist / yi.shift(12).reindex(hist.index) - 1)
        outs.append(pd.DataFrame({"target": f.target.iloc[0], "target_label": label, "unit": "index", "model": "actual", "kind": "actual",
                                  "month_date": hist.index, "value": hist.values, "yoy_value": hy.values}))
    hb_ = brent[brent.index >= "2023-01-01"]
    outs.append(pd.DataFrame({"target": "brent", "target_label": "Brent crude, monthly avg", "unit": "USD/bbl", "model": "actual",
                              "kind": "actual", "month_date": hb_.index, "value": hb_.values}))
    outs.append(pd.DataFrame([{"target": "brent", "target_label": "Brent crude, monthly avg", "unit": "USD/bbl", "model": n,
                               "kind": "reference_eia", "month_date": pd.Timestamp(d), "value": v} for d, v, n in EIA]))
    df = pd.concat(outs, ignore_index=True)
    df["month_date"] = pd.to_datetime(df.month_date).dt.date
    write(df, "ml_forecasts")
    q4 = brent_path[(brent_path.index >= "2026-10-01") & (brent_path.index <= "2026-12-01")].mean()
    q4_alt = float(np.mean(np.r_[brent[brent.index >= "2026-10-01"].values, np.exp(m2[:2])]))
    q1 = brent_path[(brent_path.index >= "2027-01-01") & (brent_path.index <= "2027-03-01")].mean()
    _plot(df)
    summary = {"brent_q4_2026_model": round(float(q4), 2), "brent_q4_2026_eia": 105.0, "brent_q4_2026_ar1_alt": round(q4_alt, 2), "brent_mar2027_ar1_alt": round(float(np.exp(m2[-1])), 2), "brent_q1_2027_model": round(float(q1), 2),
               "brent_last_actual_month": str(last_b.date()), "models": models}
    log_experiment("forecasts", {"end": str(END.date())}, summary, ["docs/figures/forecasts.png"])
    return {"df": df, "summary": summary}


def _plot(df):
    plt = setup_matplotlib()
    fig, axes = plt.subplots(1, 3, figsize=(14, 4))
    for ax, (t, ylab, yoy) in zip(axes, (("brent", "$/bbl", False), ("gas", "Gasoline CPI YoY %", True), ("headline_cpi", "Headline CPI YoY %", True))):
        d = df[df.target == t].copy()
        d["month_date"] = pd.to_datetime(d.month_date)
        a, f = d[d.kind == "actual"], d[d.kind == "forecast"]
        k = "yoy_value" if yoy else "value"
        s = 100 if yoy else 1
        ax.plot(a.month_date, a[k] * s, color="#1f3b73", label="Actual")
        ax.plot(f.month_date, f[k] * s, color="#d9822b", ls="--", label="Forecast")
        lo, hi = ("yoy_lo95", "yoy_hi95") if yoy else ("lo95", "hi95")
        ax.fill_between(f.month_date, f[lo] * s, f[hi] * s, color="#d9822b", alpha=0.15, label="95% PI")
        lo, hi = ("yoy_lo80", "yoy_hi80") if yoy else ("lo80", "hi80")
        ax.fill_between(f.month_date, f[lo] * s, f[hi] * s, color="#d9822b", alpha=0.25)
        if t == "brent":
            e = d[d.kind == "reference_eia"]
            ax.scatter(e.month_date, e.value, color="#c0392b", marker="s", s=14, label="EIA STEO (Oct-26)")
        ax.set_title(d.target_label.iloc[0])
        ax.set_ylabel(ylab)
        ax.legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "forecasts.png")
    plt.close(fig)


if __name__ == "__main__":
    r = run()
    print(r["summary"])
    d = r["df"]
    print(d[d.kind == "forecast"][["target", "month_date", "value", "lo95", "hi95", "yoy_value", "yoy_lo95", "yoy_hi95"]].round(3).to_string())
