"""Shared helpers: warehouse I/O, experiment tracking, metrics, plotting defaults."""
from __future__ import annotations

import json
import os
import time
from datetime import datetime
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DB = Path(os.environ.get("TRADEWAR_DB", ROOT / "warehouse" / "tradewar.duckdb"))
EXP_DIR = ROOT / "ml" / "experiments"
FIG_DIR = ROOT / "docs" / "figures"
EXP_DIR.mkdir(parents=True, exist_ok=True)
FIG_DIR.mkdir(parents=True, exist_ok=True)

WAR_START = pd.Timestamp("2026-02-28")
TARIFF_START = pd.Timestamp("2025-02-01")  # first IEEPA tariffs (China, 4 Feb 2025)


def read(sql: str) -> pd.DataFrame:
    with duckdb.connect(str(DB), read_only=True) as con:
        return con.execute(sql).df()


def write(df: pd.DataFrame, table: str) -> None:
    """Replace ml.<table> in the warehouse with df."""
    with duckdb.connect(str(DB)) as con:
        con.execute("create schema if not exists ml")
        con.register("_df", df)
        con.execute(f"create or replace table ml.{table} as select * from _df")
        con.unregister("_df")
    print(f"  -> ml.{table}: {len(df):,} rows")


def log_experiment(task: str, params: dict, metrics: dict, artifacts: list[str] | None = None) -> Path:
    """Minimal experiment tracker: one JSON file per run in ml/experiments/."""
    ts = datetime.now().strftime("%Y%m%dT%H%M%S")
    rec = {"task": task, "run_at": ts, "params": params, "metrics": metrics, "artifacts": artifacts or []}
    p = EXP_DIR / f"{ts}_{task}.json"
    p.write_text(json.dumps(rec, indent=2, default=_jsonable), encoding="utf-8", newline="\n")
    return p


def _jsonable(o):
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        return None if np.isnan(o) else float(o)
    if isinstance(o, (pd.Timestamp, datetime)):
        return o.isoformat()
    return str(o)


def mape(y, f):
    y, f = np.asarray(y, float), np.asarray(f, float)
    return float(np.mean(np.abs((y - f) / y)) * 100)


def wape(y, f):
    y, f = np.asarray(y, float), np.asarray(f, float)
    return float(np.sum(np.abs(y - f)) / np.sum(np.abs(y)) * 100)


def smape(y, f):
    y, f = np.asarray(y, float), np.asarray(f, float)
    return float(np.mean(2 * np.abs(y - f) / (np.abs(y) + np.abs(f))) * 100)


class Timer:
    def __enter__(self):
        self.t0 = time.perf_counter()
        return self

    def __exit__(self, *a):
        self.s = time.perf_counter() - self.t0


def setup_matplotlib():
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plt.rcParams.update({"figure.dpi": 110, "axes.spines.top": False, "axes.spines.right": False,
                         "axes.grid": True, "grid.alpha": 0.25, "font.size": 9})
    return plt