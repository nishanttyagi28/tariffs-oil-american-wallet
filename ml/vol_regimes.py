"""Volatility regimes: 2-state Markov-switching variance model (statsmodels) + GARCH(1,1)-t (arch)
on daily returns of the S&P 500, Nifty 50 and Brent, 2018 onward. Output: smoothed probability of the
high-volatility regime and GARCH conditional volatility per day."""
from __future__ import annotations

import warnings

import numpy as np
import pandas as pd
from arch import arch_model
from statsmodels.tsa.regime_switching.markov_regression import MarkovRegression

from ml.common import FIG_DIR, WAR_START, log_experiment, read, setup_matplotlib, write

warnings.filterwarnings("ignore")
SYMBOLS = {"^GSPC": "S&P 500", "^NSEI": "Nifty 50", "BZ=F": "Brent crude"}


def run() -> dict:
    px = read("""select m.trade_date, m.symbol, m.log_ret, d.trade_phase, d.war_phase from core.fct_market_daily m
                 join core.dim_date d on d.date_day = m.trade_date
                 where m.symbol in ('^GSPC', '^NSEI', 'BZ=F') and m.trade_date >= date '2018-01-01' and m.log_ret is not null""")
    px["trade_date"] = pd.to_datetime(px["trade_date"])
    out, params = [], []
    for sym, name in SYMBOLS.items():
        d = px[px.symbol == sym].sort_values("trade_date").reset_index(drop=True)
        r = 100 * d.log_ret.clip(-0.35, 0.35)  # guard against the Apr-2020 negative-WTI-style outliers
        ms = MarkovRegression(r.values, k_regimes=2, trend="c", switching_variance=True).fit(disp=False, search_reps=5)
        prm = pd.Series(np.asarray(ms.params), index=ms.model.param_names)
        sig = np.sqrt([prm[f"sigma2[{i}]"] for i in range(2)])
        hi = int(np.argmax(sig))
        p_hi = np.clip(ms.smoothed_marginal_probabilities[:, hi], 0.0, 1.0)  # remove float noise (e.g. 1+1e-16)
        P = ms.regime_transition
        stay_hi = float(P[hi, hi, 0]) if P.ndim == 3 else float(P[hi, hi])
        g = arch_model(r.values, mean="Constant", vol="GARCH", p=1, q=1, dist="t").fit(disp="off")
        d = d.assign(ret_pct=r.values, prob_high_vol=p_hi, regime=np.where(p_hi > 0.5, "high-vol", "calm"),
                     garch_vol_ann_pct=g.conditional_volatility * np.sqrt(252), instrument_name=name)
        out.append(d[["trade_date", "symbol", "instrument_name", "ret_pct", "prob_high_vol", "regime", "garch_vol_ann_pct", "trade_phase", "war_phase"]])
        params.append({"task": "vol_regimes", "series_id": sym, "model": "markov_switching_2state",
                       "calm_vol_ann_pct": float(sig[1 - hi] * np.sqrt(252)), "high_vol_ann_pct": float(sig[hi] * np.sqrt(252)),
                       "expected_high_regime_days": 1 / (1 - stay_hi), "aic": float(ms.aic),
                       "garch_alpha": float(pd.Series(g.params).iloc[2]), "garch_beta": float(pd.Series(g.params).iloc[3]), "garch_aic": float(g.aic)})
    df = pd.concat(out)
    df["trade_date"] = df.trade_date.dt.date
    write(df, "ml_vol_regimes")
    t = pd.DataFrame(params)
    share = (df.assign(hi=df.prob_high_vol > 0.5).groupby(["symbol", "war_phase"])["hi"].mean().unstack().round(3))
    _plot(df)
    log_experiment("vol_regimes", {"symbols": list(SYMBOLS), "start": "2018-01-01"},
                   {"params": t.round(3).to_dict("records"), "share_high_vol_by_war_phase": share.to_dict()}, ["docs/figures/vol_regimes.png"])
    return {"params": t, "share": share, "df": df}


def _plot(df):
    plt = setup_matplotlib()
    fig, axes = plt.subplots(3, 1, figsize=(11, 7), sharex=True)
    for ax, (sym, name) in zip(axes, SYMBOLS.items()):
        d = df[(df.symbol == sym)].copy()
        d["trade_date"] = pd.to_datetime(d.trade_date)
        d = d[d.trade_date >= "2024-07-01"]
        ax.fill_between(d.trade_date, 0, d.prob_high_vol, color="#c0392b", alpha=0.3, step="mid", label="P(high-vol regime)")
        ax2 = ax.twinx()
        ax2.plot(d.trade_date, d.garch_vol_ann_pct, color="#1f3b73", lw=1, label="GARCH vol (ann. %)")
        ax.axvline(WAR_START, color="k", ls="--", lw=0.8)
        ax.axvline(pd.Timestamp("2025-04-02"), color="grey", ls=":", lw=0.8)
        ax.set_ylim(0, 1)
        ax.set_title(f"{name}: regime probability & GARCH volatility (dotted = Liberation Day, dashed = Iran war)")
    fig.tight_layout()
    fig.savefig(FIG_DIR / "vol_regimes.png")
    plt.close(fig)


if __name__ == "__main__":
    r = run()
    print(r["params"].round(3).to_string())
    print(r["share"].to_string())
