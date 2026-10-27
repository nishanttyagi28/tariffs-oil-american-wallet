"""Tariff pass-through to US consumer prices.

1. Difference-in-differences on a category-month panel of BLS CPI (NSA, de-seasonalised by removing each
   category's 2017-2024 calendar-month mean): tariff-exposed goods (treated) vs domestic goods/services
   (control), post = Feb 2025+. Category and month fixed effects; SE clustered by category (and by month
   as a robustness check). Energy, food and airline fares are excluded from the control group because the
   2026 oil shock would contaminate them.
2. Event study: treated x relative-quarter dummies (reference = quarter before Feb 2025).
3. Robustness: alt. control incl. food, Liberation-Day timing, 2019 start excl. Covid, placebo (fake 2023 post).
4. Intensity regression: category YoY inflation on the 12-month change in the effective tariff rate
   (customs duties / imports, lagged 3 months) and import-price inflation ex food & fuel.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

from ml.common import FIG_DIR, log_experiment, read, setup_matplotlib, write

TREAT = {"tariff_exposed_goods"}
CONTROL = {"domestic_services", "domestic_goods"}
POST = pd.Timestamp("2025-02-01")


def load_panel() -> pd.DataFrame:
    p = read("""select f.series_id, f.month_date, f.index_value, f.yoy_pct, c.category, c.exposure_group
                from core.fct_cpi_monthly f join core.dim_cpi_category c using (series_id)
                where not c.is_headline and c.exposure_group <> 'aggregate'""")
    p["month_date"] = pd.to_datetime(p["month_date"])
    p = p.sort_values(["series_id", "month_date"])
    p["dm"] = 100 * p.groupby("series_id")["index_value"].transform(lambda s: np.log(s).diff())
    p["cal_month"] = p["month_date"].dt.month
    base = p[(p.month_date >= "2017-01-01") & (p.month_date <= "2024-12-01")]
    seas = base.groupby(["series_id", "cal_month"])["dm"].mean().rename("seas")
    p = p.join(seas, on=["series_id", "cal_month"])
    p["dm_sa"] = p["dm"] - p["seas"] + base["dm"].mean()
    p["yoy"] = 100 * p["yoy_pct"]
    p["ym"] = p["month_date"].dt.strftime("%Y-%m")
    return p.dropna(subset=["dm_sa"])


def _fit(formula, d, cluster):
    return smf.ols(formula, d).fit(cov_type="cluster", cov_kwds={"groups": pd.factorize(d[cluster])[0]})


def _row(spec, res, term, d, cov, note="", **kw):
    ci = res.conf_int().loc[term]
    return {"spec": spec, "term": term, "coef": res.params[term], "se": res.bse[term], "ci_lo": ci[0], "ci_hi": ci[1],
            "p_value": res.pvalues[term], "n_obs": int(res.nobs), "n_categories": d["series_id"].nunique(),
            "cov_type": cov, "sample_start": d.month_date.min().date(), "sample_end": d.month_date.max().date(),
            "notes": note, **kw}


def did(p, treat=TREAT, control=CONTROL, post=POST, start="2022-01-01", end=None, excl=None, cluster="series_id", spec="did_main", note=""):
    d = p[p.exposure_group.isin(treat | control) & (p.month_date >= start)].copy()
    if end:
        d = d[d.month_date <= end]
    if excl:
        d = d[~d.month_date.between(*excl)]
    d["treated"] = d.exposure_group.isin(treat).astype(int)
    d["post"] = (d.month_date >= post).astype(int)
    d["treat_post"] = d.treated * d.post
    res = _fit("dm_sa ~ treat_post + C(series_id) + C(ym)", d, cluster)
    return _row(spec, res, "treat_post", d, f"cluster:{cluster}", note, unit="pp per month (x12 = annualised)")


def event_study(p, start="2022-01-01"):
    d = p[p.exposure_group.isin(TREAT | CONTROL) & (p.month_date >= start)].copy()
    d["treated"] = d.exposure_group.isin(TREAT).astype(int)
    rel = ((d.month_date.dt.year - POST.year) * 12 + d.month_date.dt.month - POST.month) // 3
    d["rq"] = rel.clip(lower=-8)
    qs = sorted(d["rq"].unique())
    terms = []
    for q in qs:
        if q == -1:
            continue
        name = f"tq_m{abs(q)}" if q < 0 else f"tq_p{q}"
        d[name] = ((d.rq == q) & (d.treated == 1)).astype(int)
        terms.append((q, name))
    res = _fit("dm_sa ~ " + " + ".join(n for _, n in terms) + " + C(series_id) + C(ym)", d, "series_id")
    rows = [_row("event_study", res, n, d, "cluster:series_id", "treated x relative quarter (ref = -1)", rel_quarter=int(q)) for q, n in terms]
    rows.append({"spec": "event_study", "term": "tq_m1", "coef": 0.0, "se": 0.0, "ci_lo": 0.0, "ci_hi": 0.0, "p_value": np.nan,
                 "n_obs": int(res.nobs), "n_categories": d.series_id.nunique(), "cov_type": "reference", "rel_quarter": -1,
                 "sample_start": d.month_date.min().date(), "sample_end": d.month_date.max().date(), "notes": "reference quarter",
                 "unit": "pp per month"})
    return rows


def intensity(p):
    cr = read("select month_date, effective_rate_gross_pct from core.fct_customs_revenue_monthly")
    mm = read("select month_date, import_price_ex_food_fuel from core.fct_macro_monthly")
    for x in (cr, mm):
        x["month_date"] = pd.to_datetime(x["month_date"])
    x = cr.merge(mm, on="month_date", how="outer").sort_values("month_date").set_index("month_date")
    x["d12_tariff_l3"] = (x.effective_rate_gross_pct - x.effective_rate_gross_pct.shift(12)).shift(3)
    x["imp_px_yoy"] = 100 * (x.import_price_ex_food_fuel / x.import_price_ex_food_fuel.shift(12) - 1)
    d = p.join(x[["d12_tariff_l3", "imp_px_yoy"]], on="month_date").dropna(subset=["yoy", "d12_tariff_l3", "imp_px_yoy"])
    d = d[d.month_date >= "2017-01-01"]
    rows = []
    for grp, name in ((TREAT, "intensity_treated"), (CONTROL, "intensity_control_falsification")):
        dd = d[d.exposure_group.isin(grp)]
        res = _fit("yoy ~ d12_tariff_l3 + imp_px_yoy + C(series_id)", dd, "ym")
        for t in ("d12_tariff_l3", "imp_px_yoy"):
            rows.append(_row(name, res, t, dd, "cluster:month", "YoY inflation (pp) on 12m change in effective tariff rate (pp, lag 3) and import-price YoY",
                             unit="pp YoY per 1pp"))
    return rows


def run() -> dict:
    p = load_panel()
    rows = [did(p),
            did(p, cluster="ym", spec="did_cluster_month"),
            did(p, control=CONTROL | {"food"}, spec="did_control_incl_food"),
            did(p, post=pd.Timestamp("2025-04-01"), spec="did_post_liberation_day"),
            did(p, start="2019-01-01", excl=("2020-03-01", "2021-12-01"), spec="did_2019_start_ex_covid"),
            did(p, post=pd.Timestamp("2023-02-01"), start="2021-01-01", end="2024-12-01", spec="placebo_post_feb2023",
                note="placebo: should be ~0")]
    rows += event_study(p)
    rows += intensity(p)
    out = pd.DataFrame(rows)
    out["annualised_coef"] = np.where(out["spec"].str.startswith(("did", "placebo", "event")), out["coef"] * 12, np.nan)
    write(out, "ml_cpi_passthrough")
    _plot(out)
    main = out[out.spec == "did_main"].iloc[0]
    log_experiment("cpi_passthrough", {"treated": sorted(TREAT), "control": sorted(CONTROL), "post": str(POST.date())},
                   {r.spec + ":" + r.term: {"coef": round(r.coef, 4), "ci": [round(r.ci_lo, 4), round(r.ci_hi, 4)], "p": round(r.p_value, 4) if pd.notna(r.p_value) else None}
                    for r in out.itertuples()}, ["docs/figures/cpi_event_study.png"])
    return {"table": out, "main": main}


def _plot(out):
    plt = setup_matplotlib()
    e = out[out.spec == "event_study"].sort_values("rel_quarter")
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.errorbar(e.rel_quarter, e.coef * 12, yerr=[(e.coef - e.ci_lo) * 12, (e.ci_hi - e.coef) * 12], fmt="o-", color="#1f3b73", capsize=3)
    ax.axhline(0, color="grey", lw=0.8)
    ax.axvline(-0.5, color="#c0392b", ls="--", lw=1)
    ax.text(-0.4, ax.get_ylim()[1] * 0.85, "Feb 2025 tariffs", color="#c0392b", fontsize=8)
    ax.set_xlabel("Quarters relative to Feb 2025 (ref = -1)")
    ax.set_ylabel("Extra inflation, tariff-exposed goods\nvs domestic (pp, annualised)")
    ax.set_title("CPI pass-through event study (category & month FE, 95% CI clustered by category)")
    fig.tight_layout()
    fig.savefig(FIG_DIR / "cpi_event_study.png")
    plt.close(fig)


if __name__ == "__main__":
    r = run()
    t = r["table"]
    print(t[["spec", "term", "rel_quarter", "coef", "ci_lo", "ci_hi", "p_value", "annualised_coef", "n_obs"]].round(4).to_string())
