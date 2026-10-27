"""Build the ordered file plan for the VS Code walkthrough recording (tools/walkthrough/plan.json).

Every tracked source/config file is listed once, grouped into parts of roughly 4-5 minutes, with a one-line
note taken from the file itself (module docstring, first SQL comment, YAML/TMDL summary) or a short fallback.
Data blobs (parquet, raw snapshots, warehouse, screenshots, videos), generated per-visual JSON and ML run logs are skipped.
Usage: python tools/walkthrough/plan.py
"""

from __future__ import annotations

import ast
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SKIP = re.compile(
    r"^(data/raw|warehouse|powerbi/data|docs/sql_outputs|docs/screenshots|docs/figures|docs/demo|docs/walkthrough|ml/experiments)/"
    r"|\.(png|gif|mp4|parquet|duckdb)$|/visuals/|__init__\.py$|^tools/walkthrough/"
)

MANUAL = {
    "README.md": "Project overview: problem, key findings, dashboard pages, architecture, sources, SQL/ML highlights, how to reproduce.",
    "SETUP.md": "Fresh-laptop setup: venv, committed data vs re-ingest, dbt, ML, Power BI export and troubleshooting.",
    "LICENSE": "MIT licence for the code (third-party data keeps each provider's terms).",
    ".gitignore": "What stays out of git: secrets, venv, caches, dbt target/logs, Power BI local cache, scratch.",
    ".gitattributes": "LF line endings for text; binary for duckdb/parquet/xlsx/media; raw snapshots kept byte-exact.",
    ".env.example": "Optional settings template: CENSUS_API_KEY plus TRADEWAR_DB / TRADEWAR_RAW overrides.",
    "pyproject.toml": "Project metadata, ruff lint rules and pytest configuration.",
    "requirements.in": "Top-level Python dependencies (unpinned intent).",
    "requirements.txt": "Fully pinned Python environment for the whole pipeline (Python 3.12).",
    "requirements-ci.txt": "Smaller dependency set used by GitHub Actions.",
    ".github/workflows/ci.yml": "CI: secret scan, ruff, PBIP rebuild check, PBIR schema validation, dbt build on committed data, pytest.",
    "dbt/dbt_project.yml": "dbt project: model folders, schemas per layer, seed column types, analysis window vars, raw-path check hook.",
    "dbt/profiles.yml": "DuckDB connection: warehouse path (TRADEWAR_DB override), 1 thread, 3 GB memory limit.",
    "dbt/macros/raw.sql": "raw(source, dataset) macro: reads a data/raw parquet snapshot via read_parquet.",
    "dbt/macros/generate_schema_name.sql": "Clean schema names (staging, core, powerbi) instead of main_staging.",
    "dbt/macros/check_raw_root.sql": "on-run-start guard: fails fast with a clear message if data/raw is not reachable.",
    "dbt/models/ml/_ml_sources.yml": "Declares the ml schema tables written by Python (counterfactuals, IRFs, forecasts...) as dbt sources.",
    "powerbi/TradeWar.pbip": "Power BI project entry point: open this in Power BI Desktop.",
    "powerbi/TradeWar.Report/.platform": "Fabric/PBIP item metadata for the report.",
    "powerbi/TradeWar.SemanticModel/.platform": "Fabric/PBIP item metadata for the semantic model.",
    "powerbi/TradeWar.Report/definition.pbir": "Report definition: binds the report to the semantic model by relative path.",
    "powerbi/TradeWar.SemanticModel/definition.pbism": "Semantic model definition settings.",
    "powerbi/TradeWar.Report/definition/report.json": "Report-level settings: custom theme, collapsed panes, page settings.",
    "powerbi/TradeWar.Report/definition/version.json": "PBIR format version.",
    "powerbi/TradeWar.Report/definition/pages/pages.json": "Page order and the default (first) page.",
    "powerbi/TradeWar.Report/StaticResources/RegisteredResources/TradeWarNavyAmber.json": "Custom navy/amber report theme (colours, fonts, visual defaults).",
    "powerbi/TradeWar.SemanticModel/definition/database.tmdl": "TMDL database header (compatibility level).",
    "powerbi/TradeWar.SemanticModel/definition/model.tmdl": "TMDL model: culture, table order, query groups.",
    "powerbi/TradeWar.SemanticModel/definition/expressions.tmdl": "DataRoot M parameter: folder the Parquet tables are imported from.",
    "powerbi/TradeWar.SemanticModel/definition/relationships.tmdl": "Star-schema relationships between dimensions (Date, Country...) and fact tables.",
    "powerbi/TradeWar.SemanticModel/definition/tables/_Measures.tmdl": "All 171 DAX measures, grouped in display folders (generated from pbi_measures.py).",
    "powerbi/tools/pbi_gui.ps1": "PowerShell helpers that drive Power BI Desktop (open, page navigation, panes, screenshots, close).",
    "powerbi/tools/snap_pages.ps1": "Captures all 7 report pages from Power BI Desktop for docs/screenshots.",
    "docs/ml_report.md": "Generated ML report: methods, tables and figures for every model, with caveats.",
    "docs/data_dictionary.md": "Data dictionary: every warehouse table and column with types and descriptions.",
}


def first_comment(text: str) -> str | None:
    for line in text.splitlines()[:6]:
        s = line.strip()
        if s.startswith("--"):
            return s.lstrip("-").strip()
        if s.startswith("#") and not s.startswith("#!"):
            return s.lstrip("#").strip()
    return None


def note_for(path: str, text: str) -> str:
    if path in MANUAL:
        return MANUAL[path]
    p = Path(path)
    if p.suffix == ".py":
        try:
            doc = ast.get_docstring(ast.parse(text))
        except SyntaxError:
            doc = None
        if doc:
            return doc.strip().splitlines()[0].rstrip(".,;: ") + "."
    if p.suffix in (".sql", ".ps1", ".yml"):
        c = first_comment(text)
        if c:
            return c.rstrip(".,;: ") + "."
    if p.suffix == ".sql":
        m = re.search(r"raw\('(\w+)',\s*'(\w+)'\)", text)
        if m:
            return f"Staging view over the raw {m.group(1)}/{m.group(2)} snapshot: renames and casts columns."
        if "/tests/generic/" in path:
            return f"Generic dbt test `{p.stem}` reused across models."
        refs = sorted(set(re.findall(r"ref\('(\w+)'\)", text)))
        return f"dbt model {p.stem} built from {', '.join(refs) or 'sources'}."
    if p.suffix == ".yml":
        models = re.findall(r"^  - name: (\w+)", text, re.M)
        return f"Docs and tests for {len(models)} models ({', '.join(models[:3])}...)."
    if p.suffix == ".csv":
        rows = max(0, len(text.strip().splitlines()) - 1)
        header = text.splitlines()[0]
        return f"Seed with {rows} rows: {header.replace(',', ', ')}."
    if p.suffix == ".tmdl":
        cols = len(re.findall(r"^\tcolumn ", text, re.M))
        meas = len(re.findall(r"^\tmeasure ", text, re.M))
        return f"Table '{p.stem}': {cols} columns imported from powerbi/data/{p.stem}.parquet" + (f", {meas} measures." if meas else ".")
    if p.name == "page.json":
        name = json.loads(text).get("displayName", p.parent.name)
        return f"Page '{name}': canvas size, visibility and display settings."
    return f"{p.name}."


def section(path: str) -> int:
    order = [
        (r"^(README\.md|SETUP\.md|LICENSE)$", 0),
        (r"^(\.gitignore|\.gitattributes|\.env\.example|pyproject\.toml|requirements.*)$", 1),
        (r"^\.github/", 2),
        (r"^ingest/", 3),
        (r"^dbt/(dbt_project|profiles)\.yml$", 4),
        (r"^dbt/macros/", 5),
        (r"^dbt/models/staging/", 6),
        (r"^dbt/models/intermediate/", 7),
        (r"^dbt/models/marts/core/", 8),
        (r"^dbt/models/marts/powerbi/", 9),
        (r"^dbt/models/ml/", 10),
        (r"^dbt/tests/", 11),
        (r"^seeds/", 12),
        (r"^sql/", 13),
        (r"^ml/", 14),
        (r"^powerbi/[^/]+\.py$", 15),
        (r"^powerbi/tools/", 16),
        (r"^powerbi/TradeWar\.pbip$", 17),
        (r"^powerbi/TradeWar\.SemanticModel/", 18),
        (r"^powerbi/TradeWar\.Report/", 19),
        (r"^tests/", 20),
        (r"^tools/", 21),
        (r"^docs/", 22),
    ]
    for rx, k in order:
        if re.search(rx, path):
            return k
    return 99


FIRST = {
    "README.md": 0,
    "SETUP.md": 1,
    "LICENSE": 2,
    "ingest/common.py": -2,
    "ingest/run_all.py": -1,
    "ml/common.py": -2,
    "ml/run_all.py": -1,
    "powerbi/export_for_pbi.py": -3,
    "powerbi/build_pbip.py": -2,
    "powerbi/pbi_measures.py": -1,
    "powerbi/TradeWar.SemanticModel/definition/tables/_Measures.tmdl": -1,
    "sql/run_all.py": 99,
}
# part boundaries (section index where a new part starts)
PART_STARTS = {0: 1, 8: 2, 13: 3, 15: 4, 19: 5}


def main() -> None:
    files = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.splitlines()
    files = [f for f in files if not SKIP.search(f)]
    files.sort(key=lambda f: (section(f), FIRST.get(f, 0) if section(f) not in (0,) else FIRST.get(f, 9), f.lower()))
    plan, part = [], 1
    for f in files:
        sec = section(f)
        part = max(part, max([v for k, v in PART_STARTS.items() if sec >= k], default=1))
        text = (ROOT / f).read_text(encoding="utf-8", errors="ignore")
        n = len(text.splitlines())
        pgdn = 0 if n <= 24 else 1 if n <= 60 else 2
        plan.append({"part": part, "path": f, "lines": n, "pgdn": pgdn, "note": note_for(f, text)})
    out = ROOT / "tools" / "walkthrough" / "plan.json"
    out.write_text(json.dumps(plan, indent=1), encoding="utf-8", newline="\n")
    for p in sorted({x["part"] for x in plan}):
        items = [x for x in plan if x["part"] == p]
        est = sum(3.0 + 1.1 * x["pgdn"] for x in items)
        print(f"part {p}: {len(items)} files, ~{est / 60:.1f} min")


if __name__ == "__main__":
    main()
