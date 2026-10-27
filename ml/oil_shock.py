"""Oil-shock analytics.

A. Event study of abnormal returns around Iran-war and key tariff events. Equity indices use a market
   model vs the S&P 500; the S&P 500, FX, commodities, VIX and the 10Y yield use a constant-mean model.
   War events share one pre-war estimation window (2 Jun 2025 - 30 Jan 2026, after the Liberation-Day
   crash and before the war); tariff events use [t0-280, t0-30] trading days. CAR t-stat = CAR / (sigma*sqrt(L)).
B. Local projections (Jorda 2005): response of gasoline CPI, headline CPI, 10Y Treasury yield and the
   broad dollar index to a +10% monthly Brent move, h = 0..12, Newey-West SEs.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats

from ml.common import FIG_DIR, log_experiment, read, setup_matplotlib, write

EVENTS = {"W02": "war", "W08": "war", "W09": "war", "W14": "war", "W16": "war", "T05": "tariff", "T07": "tariff", "T19": "tariff"}
WINDOWS = {"[-5,-1]": (-5, -1), "D0": (0, 0), "D+1": (0, 1), "D+5": (0, 5), "D+10": (0, 10), "D+20": (0, 20)}
WAR_EST = (pd.Timestamp("2025-06-02"), pd.Timestamp("2026-01-30"))


def event_study() -> pd.DataFrame:
    px = read("""select m.trade_date, m.symbol, m.log_ret, i.instrument_name, i.asset_class
                 from core.fct_market_daily m join core.dim_market_instrument i using (symbol)
                 where m.log_ret is not null and m.trade_date >= date '2023-06-01'""")
    px["trade_date"] = pd.to_datetime(px["trade_date"])
    meta = px.drop_duplicates("symbol").set_index("symbol")[["instrument_name", "asset_class"]]
    R = px.pivot(index="trade_date", columns="symbol", values="log_ret").sort_index()
    ev = read("""select event_id, event_date, measure as event_name from seeds.tariff_events
                 union all select event_id, event_date, event from seeds.war_events""")
    ev = ev[ev.event_id.isin(EVENTS)]
    ev["event_date"] = pd.to_datetime(ev["event_date"])
    rows = []
    for e in ev.itertuples():
        for sym in R.columns:
            r = R[sym].dropna()
            post = r.index[r.index >= e.event_date]
            if len(post) < 21:
                continue
            t0 = r.index.get_loc(post[0])
            if EVENTS[e.event_id] == "war":
                est = r[(r.index >= WAR_EST[0]) & (r.index <= WAR_EST[1])]
            else:
                est = r.iloc[max(0, t0 - 280): t0 - 30]
            use_mkt = meta.loc[sym, "asset_class"] == "equity_index" and sym != "^GSPC"
            if use_mkt:
                m = R["^GSPC"].reindex(est.index)
                ok = m.notna()
                X = sm.add_constant(m[ok])
                fit = sm.OLS(est[ok], X).fit()
                alpha, beta, sig = fit.params["const"], fit.params["^GSPC"], np.sqrt(fit.scale)
            else:
                alpha, beta, sig = est.mean(), 0.0, est.std(ddof=1)
            for wl, (a, b) in WINDOWS.items():
                seg = r.iloc[t0 + a: t0 + b + 1]
                if len(seg) < (b - a + 1):
                    continue
                mk = R["^GSPC"].reindex(seg.index).fillna(0) if use_mkt else 0
                ar = seg - (alpha + beta * mk)
                L = len(seg)
                car = float(ar.sum())
                t = car / (sig * np.sqrt(L))
                rows.append({"event_id": e.event_id, "event_date": e.event_date.date(), "event_name": e.event_name,
                             "event_family": EVENTS[e.event_id], "symbol": sym, "instrument_name": meta.loc[sym, "instrument_name"],
                             "asset_class": meta.loc[sym, "asset_class"], "model_type": "market_model" if use_mkt else "constant_mean",
                             "beta": beta, "est_n_days": len(est), "window_label": wl, "window_days": L,
                             "t0_date": r.index[t0].date(), "raw_return_pct": 100 * (np.exp(seg.sum()) - 1),
                             "car_pct": 100 * car, "t_stat": t, "p_value": 2 * (1 - stats.norm.cdf(abs(t))),
                             "significant_5pct": abs(t) > 1.96})
    return pd.DataFrame(rows)


OUTCOMES = {"gasoline_cpi": ("100*log index", "Gasoline CPI (%)"), "headline_cpi": ("100*log index", "Headline CPI (%)"),
            "ust_10y": ("level, pp", "10Y Treasury yield (pp)"), "usd_broad": ("100*log index", "Broad USD index (%)")}


def local_projections(H: int = 12, scale: float = 10.0) -> pd.DataFrame:
    m = read("select month_date, brent_usd, cpi_sa, ust_10y_pct, usd_broad_index from core.fct_macro_monthly")
    g = read("select month_date, index_value from core.fct_cpi_monthly where series_id = 'CUUR0000SETB01'")
    for x in (m, g):
        x["month_date"] = pd.to_datetime(x["month_date"])
    d = m.merge(g.rename(columns={"index_value": "gas_idx"}), on="month_date").sort_values("month_date").set_index("month_date")
    d = d[d.index >= "2015-01-01"].dropna(subset=["brent_usd", "cpi_sa", "gas_idx"])
    d["shock"] = 100 * np.log(d.brent_usd).diff()
    Y = {"gasoline_cpi": 100 * np.log(d.gas_idx), "headline_cpi": 100 * np.log(d.cpi_sa),
         "ust_10y": d.ust_10y_pct, "usd_broad": 100 * np.log(d.usd_broad_index)}
    months = pd.get_dummies(d.index.month, prefix="m", drop_first=True).set_index(d.index).astype(float)
    rows = []
    for name, y in Y.items():
        dy = y.diff()
        for h in range(H + 1):
            lhs = y.shift(-h) - y.shift(1)
            X = pd.concat({"shock": d.shock, "shock_l1": d.shock.shift(1), "shock_l2": d.shock.shift(2),
                           "dy_l1": dy.shift(1), "dy_l2": dy.shift(2)}, axis=1)
            if name == "gasoline_cpi":
                X = X.join(months)
            Z = pd.concat([lhs.rename("lhs"), X], axis=1).dropna()
            fit = sm.OLS(Z["lhs"], sm.add_constant(Z.drop(columns="lhs"))).fit(cov_type="HAC", cov_kwds={"maxlags": h + 1})
            b, se = fit.params["shock"] * scale, fit.bse["shock"] * scale
            rows.append({"shock": "Brent +10% (monthly)", "outcome": name, "outcome_label": OUTCOMES[name][1], "units": OUTCOMES[name][0],
                         "horizon_months": h, "irf": b, "se": se, "ci_lo90": b - 1.645 * se, "ci_hi90": b + 1.645 * se,
                         "ci_lo95": b - 1.96 * se, "ci_hi95": b + 1.96 * se, "n_obs": int(fit.nobs), "method": "local projection, HAC"})
    return pd.DataFrame(rows)


def run() -> dict:
    es = event_study()
    irf = local_projections()
    write(es, "ml_event_study")
    write(irf, "ml_irf")
    _plot(es, irf)
    w = es[(es.event_id == "W02") & (es.window_label == "D+5")].set_index("symbol")
    peak = irf.loc[irf.groupby("outcome")["irf"].apply(lambda s: s.abs().idxmax())]
    log_experiment("oil_shock", {"events": EVENTS, "war_est_window": [str(x.date()) for x in WAR_EST], "lp_horizon": 12},
                   {"W02_D+5_car_pct": w["car_pct"].round(2).to_dict(), "irf_peaks": peak[["outcome", "horizon_months", "irf", "ci_lo95", "ci_hi95"]].round(3).to_dict("records")},
                   ["docs/figures/event_study_war.png", "docs/figures/irf_brent.png"])
    return {"event_study": es, "irf": irf}


def _plot(es, irf):
    plt = setup_matplotlib()
    w = es[(es.event_id == "W02") & (es.window_label == "D+5")].sort_values("car_pct")
    fig, ax = plt.subplots(figsize=(8, 6))
    col = [("#c0392b" if v < 0 else "#1e8449") + ("ff" if s else "70") for v, s in zip(w.car_pct, w.significant_5pct)]
    ax.barh(w.instrument_name, w.car_pct, color=col)
    ax.set_xlabel("Cumulative abnormal return, D0..D+5 (%)  (faded = not significant at 5%)")
    ax.set_title("Iran war start (28 Feb 2026): 6-day abnormal returns")
    fig.tight_layout()
    fig.savefig(FIG_DIR / "event_study_war.png")
    plt.close(fig)
    fig, axes = plt.subplots(2, 2, figsize=(10, 6))
    for ax, (k, g) in zip(axes.flat, irf.groupby("outcome")):
        ax.plot(g.horizon_months, g.irf, color="#1f3b73", marker="o", ms=3)
        ax.fill_between(g.horizon_months, g.ci_lo95, g.ci_hi95, alpha=0.15, color="#1f3b73")
        ax.fill_between(g.horizon_months, g.ci_lo90, g.ci_hi90, alpha=0.2, color="#1f3b73")
        ax.axhline(0, color="grey", lw=0.8)
        ax.set_title(g.outcome_label.iloc[0])
        ax.set_xlabel("Months after shock")
    fig.suptitle("Local-projection responses to a +10% Brent shock (90/95% CI, 2015-2026)")
    fig.tight_layout()
    fig.savefig(FIG_DIR / "irf_brent.png")
    plt.close(fig)


if __name__ == "__main__":
    r = run()
    es = r["event_study"]
    print(es[(es.event_id == "W02") & es.window_label.isin(["D+5", "D+20"])][["symbol", "window_label", "raw_return_pct", "car_pct", "t_stat"]].round(2).to_string())
    print(r["irf"][r["irf"].horizon_months.isin([0, 1, 3, 6, 12])][["outcome", "horizon_months", "irf", "ci_lo95", "ci_hi95"]].round(3).to_string())