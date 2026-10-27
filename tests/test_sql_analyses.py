"""Every numbered analysis in sql/analysis must run and return rows."""
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
FILES = sorted((ROOT / "sql" / "analysis").glob("[0-9][0-9]_*.sql"))


def test_at_least_30_analyses():
    assert len(FILES) >= 30


def test_every_analysis_has_a_comment_header():
    for f in FILES:
        assert f.read_text(encoding="utf-8").lstrip().startswith("--"), f.name


@pytest.mark.parametrize("path", FILES, ids=[f.stem for f in FILES])
def test_analysis_runs(con, path):
    df = con.execute(path.read_text(encoding="utf-8")).df()
    assert len(df) > 0, path.name
