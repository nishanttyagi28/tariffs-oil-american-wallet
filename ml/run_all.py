"""Run the full ML layer sequentially (one heavy process at a time) and write ml.* tables + docs.

    python -m ml.run_all            # everything (~6 min on 2 cores)
    python -m ml.run_all --skip-trade   # reuse existing ml.ml_trade_* tables
"""
from __future__ import annotations

import argparse
import time

import pandas as pd

from ml import cpi_passthrough, forecasts, oil_shock, report, trade_counterfactual, vol_regimes
from ml.common import log_experiment, read, write


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--skip-trade", action="store_true")
    a = ap.parse_args()
    t0 = time.perf_counter()
    timings = {}
    mets = []
    if not a.skip_trade:
        print("[1/5] trade counterfactuals")
        t = time.perf_counter()
        r = trade_counterfactual.run()
        timings["trade_counterfactual"] = time.perf_counter() - t
        m = r["metrics"].melt(id_vars=["task", "series_id", "model", "is_best", "n_folds", "horizon_months"],
                              value_vars=["mape", "wape", "smape"], var_name="metric", value_name="value")
        mets.append(m)
    else:
        old = read("select * from ml.ml_model_metrics where task = 'trade_counterfactual'")
        mets.append(old)
    for i, (name, mod) in enumerate((("cpi_passthrough", cpi_passthrough), ("oil_shock", oil_shock),
                                     ("vol_regimes", vol_regimes), ("forecasts", forecasts)), start=2):
        print(f"[{i}/5] {name}")
        t = time.perf_counter()
        r = mod.run()
        timings[name] = time.perf_counter() - t
        if name == "vol_regimes":
            mets.append(r["params"].melt(id_vars=["task", "series_id", "model"], var_name="metric", value_name="value").assign(is_best=True))
        if name == "forecasts":
            rows = [{"task": "forecasts", "series_id": k, "model": "SARIMAX", "metric": "aic", "value": v["aic"], "is_best": True}
                    for k, v in r["summary"]["models"].items()]
            mets.append(pd.DataFrame(rows))
    mm = pd.concat(mets, ignore_index=True)
    for c in ("n_folds", "horizon_months"):
        if c not in mm:
            mm[c] = pd.NA
    mm = mm[["task", "series_id", "model", "metric", "value", "is_best", "n_folds", "horizon_months"]]
    mm["value"] = mm["value"].astype(float)
    mm["is_best"] = mm["is_best"].fillna(False).astype(bool)
    write(mm, "ml_model_metrics")
    timings["total"] = time.perf_counter() - t0
    log_experiment("run_all", {"skip_trade": a.skip_trade}, {"seconds": {k: round(v, 1) for k, v in timings.items()}})
    report.build(timings)
    print(f"done in {time.perf_counter() - t0:.0f}s: " + ", ".join(f"{k} {v:.0f}s" for k, v in timings.items()))


if __name__ == "__main__":
    main()