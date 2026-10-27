# Setup: reproduce the project on a fresh Windows laptop

Everything needed is in this repo: code, seeds, the raw data snapshots (`data/raw`, about 21 MB),
the built DuckDB warehouse (`warehouse/tradewar.duckdb`, about 41 MB), ML experiment logs and figures,
the Power BI tables (`powerbi/data`) and the PBIP project. Nothing needs an API key.
Git LFS is **not** used (every file is under GitHub's 50 MB soft limit), so a plain `git clone` gets it all.

Only secrets (`.env`), virtual environments and caches are excluded.

## 0. Prerequisites

| Tool | Version | Notes |
|---|---|---|
| Git for Windows | any recent | `winget install Git.Git` |
| Python | **3.12** (64-bit) | `winget install Python.Python.3.12`. Do not use 3.13/3.14: several pinned wheels (duckdb, lightgbm, arch, shap, statsmodels) may not exist for newer versions and pip will try to compile them. |
| Power BI Desktop | Microsoft Store version | Only for the dashboard (step 6). |
| VS Code | optional | `code .` from the repo folder. |

Hardware: the whole pipeline runs on a 2-core / 8-12 GB laptop. dbt is configured with `threads: 1` and a 3 GB DuckDB memory limit.

## 1. Clone and create the environment

```powershell
git clone https://github.com/nishanttyagi28/tariffs-oil-american-wallet.git
cd tariffs-oil-american-wallet
git lfs pull            # optional: harmless no-op today (no LFS files), kept for future large assets

py -3.12 -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt          # pinned versions; ~5 minutes
```

If PowerShell refuses to run `activate`, run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once,
or call the tools directly (`.venv\Scripts\python.exe`, `.venv\Scripts\dbt.exe`).

Optional: `copy .env.example .env` and fill in `CENSUS_API_KEY` (only used by the optional HS-chapter ingest).
`.env` is gitignored, so never commit it.

## 2. Choose a data path

**A. Use the committed data (fastest, exactly the published numbers).** Skip to step 3 or even step 5:
`data/raw`, `warehouse/tradewar.duckdb` and `powerbi/data` are already in the repo.

**B. Re-ingest fresh data from the public sources** (numbers will move as sources publish new months):

```powershell
python -m ingest.run_all                 # ~3-6 min; writes data/raw/<source>/*.parquet + manifest.json
python -m ingest.run_all fred bls        # re-run only some sources if one failed
```

Re-ingesting overwrites the committed snapshots, so `git status` will show changes. Commit them only if you mean to update the project.

## 3. Build the warehouse with dbt

dbt must run **from the `dbt/` folder** because the profile and the raw-data path are relative to it
(`../warehouse/tradewar.duckdb`, `../data/raw`). A start-up check (`on-run-start`) stops with a clear message if `data/raw` is not reachable.
To run from elsewhere, set `TRADEWAR_RAW` (absolute path to `data/raw`) and `TRADEWAR_DB` (absolute path to the `.duckdb` file).

```powershell
cd dbt
dbt deps --profiles-dir .                # no packages today; harmless
dbt build --profiles-dir .               # seeds + staging/intermediate/marts + tests, ~2-4 min
cd ..
```

## 4. ML models, then rebuild the marts that read their outputs

```powershell
python -m ml.run_all                     # ~3-8 min; writes the ml schema, ml/experiments/*.json, docs/figures, docs/ml_report.md
cd dbt; dbt build --profiles-dir .; cd ..
python sql/run_all.py                    # optional: 35 analysis queries -> docs/sql_outputs
pytest -q                                # data-quality + model tests (needs the warehouse)
ruff check .
```

Only one heavy step at a time: close Power BI Desktop while dbt or the ML models run (they all use the same DuckDB file, and the laptop has 2 cores).

## 5. Export the Power BI tables and generate the PBIP

```powershell
python powerbi/export_for_pbi.py         # warehouse -> powerbi/data/*.parquet (~10 s)
python powerbi/build_pbip.py             # TMDL + PBIR; sets the DataRoot parameter to THIS clone's powerbi/data
python powerbi/validate_pbir.py          # optional: validates against Microsoft's PBIR JSON schemas (downloads them once)
```

## 6. Open the dashboard

1. Open `powerbi/TradeWar.pbip` in Power BI Desktop.
2. Click **Home > Refresh**. The import cache (`.pbi/cache.abf`) is not committed, so the first open shows empty visuals until you refresh (~1 min).
3. **DataRoot**: `build_pbip.py` writes the absolute path of your clone's `powerbi/data` folder into the `DataRoot` parameter.
   If you skipped step 5 or moved the folder, set it in *Transform data > Edit parameters*, or just re-run `python powerbi/build_pbip.py` with Desktop closed.
4. **Maps**: the two filled maps need *File > Options and settings > Options > Security > "Use Map and Filled Map visuals"* switched on.
   They take 30-45 s to geocode on first view.
5. Desktop will offer to upgrade or save the project. Saving rewrites many files (CRLF line endings, `cultures/`, `diagramLayout.json`).
   Those extra files are gitignored. To get back to the canonical files, close Desktop and run `python powerbi/build_pbip.py`.

## Expected runtimes (2-core laptop)

| Step | Time |
|---|---|
| `pip install -r requirements.txt` | 3-6 min |
| `python -m ingest.run_all` (option B only) | 3-6 min |
| `dbt build` | 2-4 min |
| `python -m ml.run_all` | 3-8 min |
| export + build_pbip | < 1 min |
| Power BI refresh | about 1 min |

## Troubleshooting

| Symptom | Fix |
|---|---|
| FRED download returns 403 or an HTML page | FRED blocks browser-like user agents from some networks. The ingest already sends a plain `tradewar-analytics/1.0` UA (`ingest/common.py`). Retry later or re-run only `python -m ingest.run_all fred`. |
| BLS returns `REQUEST_NOT_PROCESSED` / daily threshold | The unregistered BLS v2 API allows a small number of requests per day. The ingest makes one POST per run and caches the response for the day (`data/raw/bls/cpi_raw_<date>.json`). Wait until tomorrow or keep the committed snapshot. |
| `pip` tries to build duckdb/lightgbm/arch from source | You are on Python 3.13/3.14. Install 3.12 and recreate `.venv` with `py -3.12 -m venv .venv`. |
| dbt: `data/raw not found ...` | Run dbt from the `dbt/` folder, or set `TRADEWAR_RAW` to the absolute `data/raw` path. |
| dbt / ML: `IO Error: Could not set lock on file ... tradewar.duckdb` | Another process has the warehouse open (Power BI, a Python shell, DBeaver). Close it. |
| `git diff` shows every line changed / CRLF warnings | The repo stores text as LF (`.gitattributes`). Leave `core.autocrlf` at the default, and re-run `python powerbi/build_pbip.py` after saving in Power BI Desktop. |
| `git status` shows `warehouse/tradewar.duckdb` modified | Any dbt/ML run rewrites the warehouse. Commit it if you intend to publish new numbers; otherwise `git checkout -- warehouse/tradewar.duckdb`. |
| Power BI visuals are blank after opening | Click Refresh. If it errors, check the DataRoot parameter (step 6.3). Maps need the security option above. |
| `tests` are skipped | Tests that need the warehouse skip when `warehouse/tradewar.duckdb` is missing; it is committed, so check you are in the repo root. |

## What is in git, and what is not

| Path | In git | Size |
|---|---|---|
| `data/raw/` (source snapshots: parquet + original xlsx/xls/zip/csv/json) | yes | ~21 MB |
| `warehouse/tradewar.duckdb` | yes (plain git, < 50 MB) | ~41 MB |
| `seeds/`, `dbt/`, `sql/`, `ingest/`, `ml/` (incl. `ml/experiments/*.json`) | yes | small |
| `docs/figures`, `docs/screenshots`, `docs/sql_outputs`, `docs/demo/` | yes | ~6 MB |
| `powerbi/data/*.parquet` + PBIP project | yes | ~6 MB |
| `.env`, `.venv/`, `__pycache__/`, `.pytest_cache/`, `.ruff_cache/`, `dbt/target/`, `dbt/logs/`, `.pbi/cache.abf`, `.pbi/localSettings.json`, `.scratch/`, `data/_probe/` (exploratory source probes) | no | |

Secret hygiene: `python tools/secret_scan.py --history` scans the working tree and the whole git history for tokens, keys and passwords
(it prints only file/line/rule, never the value).