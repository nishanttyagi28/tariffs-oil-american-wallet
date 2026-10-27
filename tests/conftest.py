"""Shared fixtures. Warehouse-dependent tests skip cleanly when the DuckDB file is absent (e.g. in CI)."""
from pathlib import Path

import duckdb
import pytest

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "warehouse" / "tradewar.duckdb"


@pytest.fixture(scope="session")
def con():
    if not DB.exists():
        pytest.skip("warehouse/tradewar.duckdb not built (run ingest + dbt build)")
    c = duckdb.connect(str(DB), read_only=True)
    yield c
    c.close()
