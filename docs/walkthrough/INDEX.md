# VS Code walkthrough: every project file

Screen recordings of VS Code opening every source and config file in the repo, in pipeline order
(data blobs, the warehouse, screenshots, per-visual PBIR JSON and ML run logs are skipped).
Use the timestamps below to write the voice-over. Recorded at 1600x856, 15 fps, H.264, no audio.

| Part | Video | Duration | Size | Files | What it covers |
|---|---|---|---|---|---|
| 1 | [part1_overview_config_ingest_staging.mp4](part1_overview_config_ingest_staging.mp4) | 04:09 | 11.4 MB | 55 | Overview, config & CI, ingest/*, dbt project, macros, staging and intermediate models |
| 2 | [part2_dbt_marts_tests_seeds.mp4](part2_dbt_marts_tests_seeds.mp4) | 03:47 | 10.1 MB | 41 | dbt marts (core + Power BI), ml sources, dbt tests, seeds |
| 3 | [part3_sql_analyses_ml.mp4](part3_sql_analyses_ml.mp4) | 03:24 | 10.5 MB | 44 | 35 SQL analyses + runner, the ML layer |
| 4 | [part4_powerbi_generator_semantic_model.mp4](part4_powerbi_generator_semantic_model.mp4) | 05:35 | 14.6 MB | 48 | Power BI export/generator scripts, GUI helper scripts, PBIP and the TMDL semantic model |
| 5 | [part5_report_tests_tools_docs.mp4](part5_report_tests_tools_docs.mp4) | 02:07 | 5.8 MB | 23 | PBIR report definition, Python tests, tools, docs |

## Part 1: Overview, config & CI, ingest/*, dbt project, macros, staging and intermediate models

Video: [part1_overview_config_ingest_staging.mp4](part1_overview_config_ingest_staging.mp4) (04:09)

| Time | File | Note |
|---|---|---|
| 00:00 | `README.md` | Project overview: problem, key findings, dashboard pages, architecture, sources, SQL/ML highlights, how to reproduce. |
| 00:07 | `SETUP.md` | Fresh-laptop setup: venv, committed data vs re-ingest, dbt, ML, Power BI export and troubleshooting. |
| 00:13 | `LICENSE` | MIT licence for the code (third-party data keeps each provider's terms). |
| 00:16 | `.env.example` | Optional settings template: CENSUS_API_KEY plus TRADEWAR_DB / TRADEWAR_RAW overrides. |
| 00:20 | `.gitattributes` | LF line endings for text; binary for duckdb/parquet/xlsx/media; raw snapshots kept byte-exact. |
| 00:23 | `.gitignore` | What stays out of git: secrets, venv, caches, dbt target/logs, Power BI local cache, scratch. |
| 00:28 | `pyproject.toml` | Project metadata, ruff lint rules and pytest configuration. |
| 00:32 | `requirements-ci.txt` | Smaller dependency set used by GitHub Actions. |
| 00:36 | `requirements.in` | Top-level Python dependencies (unpinned intent). |
| 00:39 | `requirements.txt` | Fully pinned Python environment for the whole pipeline (Python 3.12). |
| 00:46 | `.github/workflows/ci.yml` | CI: secret scan, ruff, PBIP rebuild check, PBIR schema validation, dbt build on committed data, pytest. |
| 00:50 | `ingest/common.py` | Shared helpers for all ingest modules: HTTP with retry/backoff, raw paths, manifest. |
| 00:57 | `ingest/run_all.py` | Run every ingest module in sequence (one process, low memory). Usage: python -m ingest.run_all [module ...]. |
| 01:01 | `ingest/bls.py` | BLS CPI-U by category via public API v1 (no key; 25 queries/day, <=25 series, <=10 years per query). |
| 01:08 | `ingest/census_country.py` | US Census Bureau - U.S. trade in goods by country (monthly totals, no key). |
| 01:13 | `ingest/census_hs.py` | OPTIONAL: US Census International Trade API (HS chapter x country x calculated duty). |
| 01:18 | `ingest/comtrade.py` | UN Comtrade public preview (no key, one period per call): partner-reported exports TO the USA. |
| 01:23 | `ingest/crosswalk.py` | Census Schedule C country codes -> ISO2 -> ISO3 (via pycountry), joined to Natural Earth label points. |
| 01:27 | `ingest/eia.py` | EIA spot prices (daily): Brent RBRTE and WTI RWTC history workbooks. No key. |
| 01:31 | `ingest/eurostat.py` | Eurostat - EU27 trade with partners by SITC (monthly, EUR millions). JSON-stat API, no key. |
| 01:36 | `ingest/fred.py` | FRED via fredgraph.csv (no key). NOTE: use a plain user agent - browser UAs time out. |
| 01:41 | `ingest/gscpi.py` | NY Fed Global Supply Chain Pressure Index (monthly, no key). |
| 01:46 | `ingest/naturalearth.py` | Natural Earth 1:110m admin-0 countries: ISO codes, region, label point (map lat/long). |
| 01:50 | `ingest/portwatch.py` | IMF PortWatch daily chokepoint transits (no key). |
| 01:55 | `ingest/portwatch_ref.py` | IMF PortWatch chokepoint reference layer (name, lat/lon, industry share) via ArcGIS FeatureServer (no key). |
| 01:59 | `ingest/statcan.py` | Statistics Canada table 12-10-0011-01: merchandise trade by principal partners (monthly, CAD). |
| 02:04 | `ingest/treasury.py` | US Treasury Monthly Treasury Statement table 4: Customs Duties receipts (gross, refunds, net). No key. |
| 02:09 | `ingest/worldbank.py` | World Bank WDI API (annual, no key). |
| 02:14 | `ingest/yahoo.py` | Yahoo Finance chart API (daily OHLC, no key) for global indices, commodities, FX, rates, volatility. |
| 02:19 | `dbt/dbt_project.yml` | dbt project: model folders, schemas per layer, seed column types, analysis window vars, raw-path check hook. |
| 02:23 | `dbt/profiles.yml` | DuckDB connection: warehouse path (TRADEWAR_DB override), 1 thread, 3 GB memory limit. |
| 02:27 | `dbt/macros/check_raw_root.sql` | on-run-start guard: fails fast with a clear message if data/raw is not reachable. |
| 02:31 | `dbt/macros/generate_schema_name.sql` | Clean schema names (staging, core, powerbi) instead of main_staging. |
| 02:35 | `dbt/macros/raw.sql` | raw(source, dataset) macro: reads a data/raw parquet snapshot via read_parquet. |
| 02:39 | `dbt/models/staging/stg_bls__cpi.sql` | Staging view over the raw bls/cpi_categories_monthly snapshot: renames and casts columns. |
| 02:44 | `dbt/models/staging/stg_census__trade_monthly.sql` | US goods trade by Census partner code, monthly, millions USD (NSA). |
| 02:48 | `dbt/models/staging/stg_comtrade__mirror_exports.sql` | Staging view over the raw comtrade/mirror_exports_to_us_monthly snapshot: renames and casts columns. |
| 02:52 | `dbt/models/staging/stg_crosswalk__census_country.sql` | Staging view over the raw crosswalk/census_country_iso snapshot: renames and casts columns. |
| 02:57 | `dbt/models/staging/stg_eia__crude_spot.sql` | Staging view over the raw eia/crude_spot_daily snapshot: renames and casts columns. |
| 03:01 | `dbt/models/staging/stg_eurostat__eu_trade_monthly.sql` | Staging view over the raw eurostat/eu27_trade_partner_monthly snapshot: renames and casts columns. |
| 03:05 | `dbt/models/staging/stg_fred__series.sql` | Staging view over the raw fred/fred_series snapshot: renames and casts columns. |
| 03:09 | `dbt/models/staging/stg_gscpi__monthly.sql` | Staging view over the raw gscpi/gscpi_monthly snapshot: renames and casts columns. |
| 03:14 | `dbt/models/staging/stg_naturalearth__countries.sql` | Staging view over the raw naturalearth/countries snapshot: renames and casts columns. |
| 03:18 | `dbt/models/staging/stg_portwatch__chokepoints_daily.sql` | IMF PortWatch: daily vessel transits through 28 maritime chokepoints (AIS satellite signals). |
| 03:22 | `dbt/models/staging/stg_portwatch__chokepoints_ref.sql` | Staging view over the raw portwatch/chokepoints_ref snapshot: renames and casts columns. |
| 03:27 | `dbt/models/staging/stg_statcan__trade_monthly.sql` | Statistics Canada 12-10-0011-01: Canada's merchandise trade with principal partners (customs basis, NSA, C$ millions). |
| 03:31 | `dbt/models/staging/stg_treasury__customs.sql` | MTS reports amounts in dollars; convert to $ millions. Refunds surge after the Feb-2026 IEEPA ruling. |
| 03:35 | `dbt/models/staging/stg_worldbank__wdi.sql` | Staging view over the raw worldbank/wdi_annual snapshot: renames and casts columns. |
| 03:39 | `dbt/models/staging/stg_yahoo__instruments.sql` | Staging view over the raw yahoo/instruments snapshot: renames and casts columns. |
| 03:44 | `dbt/models/staging/stg_yahoo__prices.sql` | Staging view over the raw yahoo/market_prices_daily snapshot: renames and casts columns. |
| 03:48 | `dbt/models/intermediate/int_fred__monthly.sql` | FRED series collapsed to monthly averages (daily/weekly series) or the monthly value itself. |
| 03:52 | `dbt/models/intermediate/int_market__returns.sql` | Daily returns per instrument with a trading-day index (used for event windows and rolling stats). |
| 03:56 | `dbt/models/intermediate/int_tariff__headline_daily.sql` | Daily statutory *additional* headline tariff (pct points on top of MFN) per schedule key. |
| 04:01 | `dbt/models/intermediate/int_trade__partner_monthly.sql` | US goods trade by partner (ISO3), monthly, $ millions NSA. Census aggregates (codes < 1000) are excluded. |
| 04:05 | `dbt/models/intermediate/int_trade__world_monthly.sql` | Census published totals: World NSA (0015) and European Union (0003), used for reconciliation tests. |

## Part 2: dbt marts (core + Power BI), ml sources, dbt tests, seeds

Video: [part2_dbt_marts_tests_seeds.mp4](part2_dbt_marts_tests_seeds.mp4) (03:47)

| Time | File | Note |
|---|---|---|
| 00:00 | `dbt/models/marts/core/_core.yml` | Docs and tests for 13 models (dim_date, dim_country, dim_cpi_category...). |
| 00:08 | `dbt/models/marts/core/dim_chokepoint.sql` | 28 maritime chokepoints (IMF PortWatch) with location and traffic baselines. |
| 00:14 | `dbt/models/marts/core/dim_country.sql` | One row per partner (ISO3) plus bloc rows (EUU = EU-27, ALL = all partners / US total). |
| 00:21 | `dbt/models/marts/core/dim_cpi_category.sql` | CPI-U categories (BLS, NSA) with tariff-exposure grouping used for pass-through comparisons. |
| 00:26 | `dbt/models/marts/core/dim_date.sql` | Daily calendar 2015-2026 with trade-war and Iran-war phase labels and before/after flags. |
| 00:32 | `dbt/models/marts/core/dim_market_instrument.sql` | Market instruments (Yahoo Finance) with region for the global-markets pages. |
| 00:38 | `dbt/models/marts/core/fct_chokepoint_daily.sql` | Daily chokepoint transits with 7-day averages and comparisons to 2024 and pre-war (Jan 1 - Feb 27 2026) baselines. |
| 00:43 | `dbt/models/marts/core/fct_cpi_monthly.sql` | CPI-U by category (BLS, NSA): YoY, MoM, and index rebased to Jan 2025 = 100 (tariff-era start). |
| 00:48 | `dbt/models/marts/core/fct_customs_revenue_monthly.sql` | US customs duties (Treasury Monthly Treasury Statement, $M): gross, refunds, net; effective tariff rate proxy. |
| 00:54 | `dbt/models/marts/core/fct_macro_monthly.sql` | Wide monthly US macro panel (FRED monthly averages + NY Fed GSCPI) with derived YoY and real-wage metrics. |
| 01:00 | `dbt/models/marts/core/fct_market_daily.sql` | Daily market panel: returns, 21-day annualised volatility, drawdowns, rebased indices (2025 start and pre-war). |
| 01:06 | `dbt/models/marts/core/fct_oil_daily.sql` | Daily crude oil: EIA spot (Brent, WTI) plus Yahoo front-month futures (extends past the EIA publication lag). |
| 01:12 | `dbt/models/marts/core/fct_tariff_rate_monthly.sql` | Monthly statutory additional headline tariff per partner (avg of daily seed schedule via dim_country.tariff_schedule_key). |
| 01:18 | `dbt/models/marts/core/fct_trade_monthly.sql` | US goods trade with each partner (Census, $M NSA), monthly, with YoY, share and rolling-12m metrics. |
| 01:24 | `dbt/models/marts/powerbi/_powerbi.yml` | Docs and tests for 5 models (mart_country_before_after, mart_trade_diversion, mart_household_impact...). |
| 01:30 | `dbt/models/marts/powerbi/mart_country_before_after.sql` | Before vs after per partner (+ EU-27 bloc): average monthly trade in 2024 vs Apr 2025 onward, like-for-like. |
| 01:38 | `dbt/models/marts/powerbi/mart_household_impact.sql` | What the trade war and the oil shock cost US households: prices by tariff exposure, wages, sentiment. |
| 01:44 | `dbt/models/marts/powerbi/mart_market_event_window.sql` | Event study: cumulative returns of every instrument around each tariff and war event. |
| 01:50 | `dbt/models/marts/powerbi/mart_oil_shock.sql` | Iran-war oil shock, daily from Oct 2025: crude prices, Strait of Hormuz transits, gasoline, VIX, S&P 500. |
| 01:56 | `dbt/models/marts/powerbi/mart_trade_diversion.sql` | Trade diversion: monthly share of US goods imports by partner group vs the 2024 average share. |
| 02:02 | `dbt/models/ml/_ml_sources.yml` | Declares the ml schema tables written by Python (counterfactuals, IRFs, forecasts...) as dbt sources. |
| 02:08 | `dbt/tests/generic/unique_combination.sql` | Fails for every key combination that appears more than once. |
| 02:12 | `dbt/tests/generic/value_between.sql` | Fails for non-null values outside [min_value, max_value]. |
| 02:17 | `dbt/tests/singular/assert_before_window_is_2024.sql` | The "Before" label must be exactly calendar 2024. |
| 02:23 | `dbt/tests/singular/assert_customs_net_equals_gross_minus_refunds.sql` | Net customs receipts must equal gross minus refunds (within $1m rounding). |
| 02:28 | `dbt/tests/singular/assert_data_is_fresh.sql` | Guard against a silently stale ingest: key facts must reach recent periods. |
| 02:33 | `dbt/tests/singular/assert_dim_date_contiguous.sql` | The calendar must have no gaps. |
| 02:38 | `dbt/tests/singular/assert_event_window_dates_ordered.sql` | Event-window base date must precede the window end date, and base close must be positive. |
| 02:43 | `dbt/tests/singular/assert_ml_intervals_ordered.sql` | ML prediction intervals must nest: lo95 <= lo80 <= point <= hi80 <= hi95. |
| 02:48 | `dbt/tests/singular/assert_ml_one_best_model_per_series.sql` | Exactly one best model per trade series and metric. |
| 02:53 | `dbt/tests/singular/assert_no_war_phase_before_war_start.sql` | Iran-war phases may only start on/after the war start date (28 Feb 2026). |
| 02:58 | `dbt/tests/singular/assert_rolling_vol_non_negative.sql` | Annualised volatility can never be negative. |
| 03:03 | `dbt/tests/singular/assert_tariff_schedule_no_overlap.sql` | A country's headline tariff schedule rows must not overlap in time. |
| 03:08 | `dbt/tests/singular/assert_trade_balance_identity.sql` | Balance = exports - imports; total trade = exports + imports. |
| 03:14 | `dbt/tests/singular/assert_trade_diversion_shares_sum_to_one.sql` | Partner-group import shares (excluding the all-partners total) sum to ~100% each month. |
| 03:18 | `seeds/cpi_category_map.csv` | Seed with 25 rows: series_id, category, exposure_group, is_headline. |
| 03:24 | `seeds/eu27_members.csv` | Seed with 27 rows: iso3. |
| 03:29 | `seeds/event_phases.csv` | Seed with 11 rows: phase_type, phase_code, phase_order, phase_name, start_date, end_date, description. |
| 03:34 | `seeds/tariff_events.csv` | Seed with 22 rows: event_id, event_date, effective_date, country_iso3, measure, authority, rate_pct, description, source_url, verified. |
| 03:38 | `seeds/tariff_headline_schedule.csv` | Seed with 50 rows: country_iso3, start_date, end_date, headline_rate_pct, basis, verified, source_url. |
| 03:44 | `seeds/war_events.csv` | Seed with 18 rows: event_id, event_date, event, category, brent_usd, source_url, verified. |

## Part 3: 35 SQL analyses + runner, the ML layer

Video: [part3_sql_analyses_ml.mp4](part3_sql_analyses_ml.mp4) (03:24)

| Time | File | Note |
|---|---|---|
| 00:00 | `sql/analysis/01_dq_freshness_row_counts.sql` | DQ: row counts and coverage window of every fact table (is the warehouse fresh?). |
| 00:05 | `sql/analysis/02_dq_null_profile.sql` | DQ: null-rate profile of key measures since 2024 (gaps that the dashboard must handle). |
| 00:09 | `sql/analysis/03_dq_partner_sum_vs_us_total.sql` | DQ: do Census partner-level imports add up to the US total goods imports used for the customs effective rate?. |
| 00:13 | `sql/analysis/04_dq_customs_reconciliation.sql` | DQ: recompute effective tariff rate (gross duties / goods imports) and compare with the stored column. |
| 00:18 | `sql/analysis/05_top_import_partners_2024_vs_latest_12m.sql` | Top 15 US import partners: calendar-2024 total vs the latest rolling 12 months, with RANK() shift. |
| 00:22 | `sql/analysis/06_partner_rank_shift_before_after.sql` | Biggest winners/losers in US import share: 2024 baseline vs Apr-2025+ (mart_country_before_after). |
| 00:27 | `sql/analysis/07_focus_partner_imports_yoy.sql` | Year-over-year import growth for focus partners over the last 8 reported months (LAG-based YoY). |
| 00:31 | `sql/analysis/08_china_imports_mom_3m_avg.sql` | China: monthly imports with MoM change (LAG) and a 3-month moving average, 2024 onward. |
| 00:35 | `sql/analysis/09_bilateral_deficit_before_after.sql` | US bilateral goods balance with each partner: avg monthly 2024 vs Apr-2025+, largest deficits. |
| 00:40 | `sql/analysis/10_us_total_deficit_rolling_12m.sql` | US total goods trade (sum over partners): monthly balance, rolling 12-month sum (window frame) and YoY change, 2023+. |
| 00:44 | `sql/analysis/11_trade_diversion_share_shift.sql` | Trade diversion: each partner group's share of US imports, 2024 vs the latest 6 months, and implied diverted $. |
| 00:48 | `sql/analysis/12_china_substitution_pivot.sql` | "China+1": monthly import share of China vs Vietnam, Taiwan, Mexico, India (PIVOT), 2024 onward. |
| 00:52 | `sql/analysis/13_front_loading_q1_2025.sql` | Front-loading ahead of tariffs: Jan-Mar 2025 imports vs Jan-Mar 2024, then Apr-Jun 2025 hangover. |
| 00:57 | `sql/analysis/14_statutory_vs_effective_tariff.sql` | Statutory (2024-import-weighted headline) tariff vs the effective rate actually collected (customs gross & net / imports). |
| 01:01 | `sql/analysis/15_customs_revenue_trend.sql` | Customs duties: gross, refunds (post-SCOTUS IEEPA refunds), net, YoY and the US-wide effective tariff rate. |
| 01:05 | `sql/analysis/16_incremental_duties_per_household.sql` | Incremental tariff revenue vs the 2024 run-rate, converted to $ per US household (132.2m), cumulative. |
| 01:10 | `sql/analysis/17_trade_by_tariff_phase.sql` | US total imports/exports by tariff-war phase (dim_date phases from seeds/event_phases.csv), 2024 onward. |
| 01:14 | `sql/analysis/18_cpi_tariff_goods_vs_services.sql` | Household prices: tariff-exposed goods vs domestic services inflation (YoY) and the gap, by month. |
| 01:19 | `sql/analysis/19_cpi_category_passthrough_ranking.sql` | Pass-through ranking: annualised inflation per CPI category before (Dec-2022 -> Dec-2024) vs after (Dec-2024 -> latest). |
| 01:23 | `sql/analysis/20_cpi_by_exposure_group_phase.sql` | Average YoY inflation by CPI exposure group and tariff/war phase (household lens). |
| 01:27 | `sql/analysis/21_real_wages_sentiment_jobs.sql` | Household squeeze: wages vs prices (real wage YoY), sentiment, saving rate, unemployment, 2024 onward. |
| 01:32 | `sql/analysis/22_import_price_to_core_goods_lag_corr.sql` | Lead-lag: correlation of import-price (ex fuel) YoY with core-goods CPI YoY k months later (k = 0..9), 2017+. |
| 01:36 | `sql/analysis/23_oil_by_war_phase.sql` | Brent & WTI by Iran-war phase: average, peak and change vs the pre-war close (27 Feb 2026). |
| 01:40 | `sql/analysis/24_brent_running_peak_drawdown.sql` | Brent since 2025: running peak (window max), drawdown from peak, and the 10 biggest single-day moves. |
| 01:45 | `sql/analysis/25_hormuz_transits_by_phase.sql` | Strait of Hormuz daily transits (all ships / tankers) by war phase vs the 2024 average (IMF PortWatch). |
| 01:49 | `sql/analysis/26_chokepoint_disruption_ranking.sql` | Which global chokepoints changed most: last 30 days vs pre-war average transits (RANK by disruption). |
| 01:53 | `sql/analysis/27_gasoline_brent_passthrough.sql` | Pump-price pass-through: regression slope of US gasoline ($/gal) on Brent ($/bbl), monthly, by period. |
| 01:57 | `sql/analysis/28_event_window_iran_war_start.sql` | Event study: cumulative returns of each instrument after the Iran-war start (W02), D0..D+20. |
| 02:02 | `sql/analysis/29_event_window_liberation_day.sql` | Event study: Liberation Day (T05, 2 Apr 2025) and the 90-day pause (T07): equity index returns by window. |
| 02:06 | `sql/analysis/30_max_drawdown_by_index.sql` | Maximum drawdown since 1 Jan 2025 per equity index, with trough date, and recovery to latest. |
| 02:10 | `sql/analysis/31_rolling_corr_sp500_brent.sql` | Rolling 63-trading-day correlation of S&P 500 and Brent daily log returns (window aggregate), month-end values. |
| 02:14 | `sql/analysis/32_volatility_regimes_vix.sql` | Fear gauge by phase: VIX average/peak and share of days in stress (>25) or panic (>30) regimes. |
| 02:19 | `sql/analysis/33_cross_asset_returns_by_war_phase.sql` | Cross-asset scorecard: compounded return of each instrument within each Iran-war phase (exp(sum(log_ret))). |
| 02:23 | `sql/analysis/34_india_deep_dive.sql` | India lens: US-India trade, tariff rate, INR and Nifty by month (2024 onward). |
| 02:27 | `sql/analysis/35_fx_vs_usd_since_2025.sql` | Dollar story: FX moves since 1 Jan 2025 (USD-base pairs: >100 = USD stronger) and since the pre-war close. |
| 02:31 | `sql/run_all.py` | Run every numbered DuckDB analysis in sql/analysis/ against the warehouse and save small outputs. |
| 02:35 | `ml/common.py` | Shared helpers: warehouse I/O, experiment tracking, metrics, plotting defaults. |
| 02:41 | `ml/run_all.py` | Run the full ML layer sequentially (one heavy process at a time) and write ml.* tables + docs. |
| 02:48 | `ml/cpi_passthrough.py` | Tariff pass-through to US consumer prices. |
| 02:54 | `ml/forecasts.py` | Forward forecasts with prediction intervals. |
| 03:00 | `ml/oil_shock.py` | Oil-shock analytics. |
| 03:06 | `ml/report.py` | Builds docs/ml_report.md from the ml.* tables so every number in the report comes from the warehouse. |
| 03:12 | `ml/trade_counterfactual.py` | Counterfactual 'no-tariff' US trade forecasts per major partner. |
| 03:18 | `ml/vol_regimes.py` | Volatility regimes: 2-state Markov-switching variance model (statsmodels) + GARCH(1,1)-t (arch). |

## Part 4: Power BI export/generator scripts, GUI helper scripts, PBIP and the TMDL semantic model

Video: [part4_powerbi_generator_semantic_model.mp4](part4_powerbi_generator_semantic_model.mp4) (05:35)

| Time | File | Note |
|---|---|---|
| 00:00 | `powerbi/export_for_pbi.py` | Export the warehouse tables the Power BI model needs to Parquet in powerbi/data/. |
| 00:08 | `powerbi/build_pbip.py` | Build the Power BI project (PBIP: TMDL semantic model + PBIR report) from the exported Parquet schema. |
| 00:14 | `powerbi/pbi_measures.py` | DAX measures for the TradeWar semantic model: (name, display folder, format string, DAX expression). |
| 00:21 | `powerbi/pbi_common.py` | Shared helpers for the PBIP builder: TMDL writer (semantic model) and PBIR JSON helpers (report). |
| 00:28 | `powerbi/pbi_model.py` | Write the TMDL semantic model (powerbi/TradeWar.SemanticModel) from powerbi/data/_schema.json + pbi_measures. |
| 00:35 | `powerbi/pbi_report.py` | Write the PBIR report (powerbi/TradeWar.Report): theme, 7 story pages + 1 tooltip page. |
| 00:42 | `powerbi/pbi_theme.py` | Custom report theme: deep navy + amber/teal ('TradeWar Navy Amber'). Written to StaticResources/RegisteredResources. |
| 00:47 | `powerbi/validate_pbir.py` | Validate the PBIR JSON files against Microsoft's published schemas (downloaded once to $PBIR_SCHEMA_CACHE or the temp dir). |
| 00:53 | `powerbi/tools/crop_screenshots.py` | Crop raw 1600x900 Power BI Desktop captures to the report canvas + page tabs (drops title bar, ribbon, side rail. |
| 00:59 | `powerbi/tools/pbi_gui.ps1` | PowerShell helpers that drive Power BI Desktop (open, page navigation, panes, screenshots, close). |
| 01:06 | `powerbi/tools/record_demo.ps1` | Record the demo: VS Code tour of the repo, then a walk through the 7 Power BI pages. |
| 01:12 | `powerbi/tools/snap_pages.ps1` | Captures all 7 report pages from Power BI Desktop for docs/screenshots. |
| 01:17 | `powerbi/TradeWar.pbip` | Power BI project entry point: open this in Power BI Desktop. |
| 01:22 | `powerbi/TradeWar.SemanticModel/definition/tables/_Measures.tmdl` | All 171 DAX measures, grouped in display folders (generated from pbi_measures.py). |
| 01:30 | `powerbi/TradeWar.SemanticModel/.platform` | Fabric/PBIP item metadata for the semantic model. |
| 01:35 | `powerbi/TradeWar.SemanticModel/definition.pbism` | Semantic model definition settings. |
| 01:40 | `powerbi/TradeWar.SemanticModel/definition/database.tmdl` | TMDL database header (compatibility level). |
| 01:45 | `powerbi/TradeWar.SemanticModel/definition/expressions.tmdl` | DataRoot M parameter: folder the Parquet tables are imported from. |
| 01:50 | `powerbi/TradeWar.SemanticModel/definition/model.tmdl` | TMDL model: culture, table order, query groups. |
| 01:57 | `powerbi/TradeWar.SemanticModel/definition/relationships.tmdl` | Star-schema relationships between dimensions (Date, Country...) and fact tables. |
| 02:04 | `powerbi/TradeWar.SemanticModel/definition/tables/Chokepoint Daily.tmdl` | Table 'Chokepoint Daily': 14 columns imported from powerbi/data/Chokepoint Daily.parquet. |
| 02:12 | `powerbi/TradeWar.SemanticModel/definition/tables/Chokepoint.tmdl` | Table 'Chokepoint': 11 columns imported from powerbi/data/Chokepoint.parquet. |
| 02:20 | `powerbi/TradeWar.SemanticModel/definition/tables/Counterfactual.tmdl` | Table 'Counterfactual': 24 columns imported from powerbi/data/Counterfactual.parquet. |
| 02:28 | `powerbi/TradeWar.SemanticModel/definition/tables/Country Before After.tmdl` | Table 'Country Before After': 33 columns imported from powerbi/data/Country Before After.parquet. |
| 02:36 | `powerbi/TradeWar.SemanticModel/definition/tables/Country.tmdl` | Table 'Country': 17 columns imported from powerbi/data/Country.parquet. |
| 02:43 | `powerbi/TradeWar.SemanticModel/definition/tables/CPI Category.tmdl` | Table 'CPI Category': 5 columns imported from powerbi/data/CPI Category.parquet. |
| 02:50 | `powerbi/TradeWar.SemanticModel/definition/tables/CPI.tmdl` | Table 'CPI': 8 columns imported from powerbi/data/CPI.parquet. |
| 02:57 | `powerbi/TradeWar.SemanticModel/definition/tables/Customs.tmdl` | Table 'Customs': 13 columns imported from powerbi/data/Customs.parquet. |
| 03:05 | `powerbi/TradeWar.SemanticModel/definition/tables/Date.tmdl` | Table 'Date': 18 columns imported from powerbi/data/Date.parquet. |
| 03:13 | `powerbi/TradeWar.SemanticModel/definition/tables/Event Study.tmdl` | Table 'Event Study': 18 columns imported from powerbi/data/Event Study.parquet. |
| 03:20 | `powerbi/TradeWar.SemanticModel/definition/tables/Events.tmdl` | Table 'Events': 8 columns imported from powerbi/data/Events.parquet. |
| 03:28 | `powerbi/TradeWar.SemanticModel/definition/tables/Forecasts.tmdl` | Table 'Forecasts': 16 columns imported from powerbi/data/Forecasts.parquet. |
| 03:36 | `powerbi/TradeWar.SemanticModel/definition/tables/Household.tmdl` | Table 'Household': 33 columns imported from powerbi/data/Household.parquet. |
| 03:44 | `powerbi/TradeWar.SemanticModel/definition/tables/Instrument.tmdl` | Table 'Instrument': 11 columns imported from powerbi/data/Instrument.parquet. |
| 03:51 | `powerbi/TradeWar.SemanticModel/definition/tables/IRF.tmdl` | Table 'IRF': 13 columns imported from powerbi/data/IRF.parquet. |
| 03:59 | `powerbi/TradeWar.SemanticModel/definition/tables/Macro.tmdl` | Table 'Macro': 37 columns imported from powerbi/data/Macro.parquet. |
| 04:07 | `powerbi/TradeWar.SemanticModel/definition/tables/Market.tmdl` | Table 'Market': 16 columns imported from powerbi/data/Market.parquet. |
| 04:14 | `powerbi/TradeWar.SemanticModel/definition/tables/Model Metrics.tmdl` | Table 'Model Metrics': 8 columns imported from powerbi/data/Model Metrics.parquet. |
| 04:22 | `powerbi/TradeWar.SemanticModel/definition/tables/Oil Shock.tmdl` | Table 'Oil Shock': 24 columns imported from powerbi/data/Oil Shock.parquet. |
| 04:30 | `powerbi/TradeWar.SemanticModel/definition/tables/Oil.tmdl` | Table 'Oil': 15 columns imported from powerbi/data/Oil.parquet. |
| 04:38 | `powerbi/TradeWar.SemanticModel/definition/tables/Partner.tmdl` | Table 'Partner': 4 columns imported from powerbi/data/Partner.parquet. |
| 04:44 | `powerbi/TradeWar.SemanticModel/definition/tables/Pass-through.tmdl` | Table 'Pass-through': 16 columns imported from powerbi/data/Pass-through.parquet. |
| 04:52 | `powerbi/TradeWar.SemanticModel/definition/tables/Tariff Effect.tmdl` | Table 'Tariff Effect': 20 columns imported from powerbi/data/Tariff Effect.parquet. |
| 05:00 | `powerbi/TradeWar.SemanticModel/definition/tables/Tariff Rate.tmdl` | Table 'Tariff Rate': 8 columns imported from powerbi/data/Tariff Rate.parquet. |
| 05:08 | `powerbi/TradeWar.SemanticModel/definition/tables/Trade Diversion.tmdl` | Table 'Trade Diversion': 12 columns imported from powerbi/data/Trade Diversion.parquet. |
| 05:16 | `powerbi/TradeWar.SemanticModel/definition/tables/Trade Metric.tmdl` | Table 'Trade Metric': 2 columns imported from powerbi/data/Trade Metric.parquet. |
| 05:22 | `powerbi/TradeWar.SemanticModel/definition/tables/Trade.tmdl` | Table 'Trade': 16 columns imported from powerbi/data/Trade.parquet. |
| 05:30 | `powerbi/TradeWar.SemanticModel/definition/tables/Vol Regimes.tmdl` | Table 'Vol Regimes': 9 columns imported from powerbi/data/Vol Regimes.parquet. |

## Part 5: PBIR report definition, Python tests, tools, docs

Video: [part5_report_tests_tools_docs.mp4](part5_report_tests_tools_docs.mp4) (02:07)

| Time | File | Note |
|---|---|---|
| 00:00 | `powerbi/TradeWar.Report/.platform` | Fabric/PBIP item metadata for the report. |
| 00:05 | `powerbi/TradeWar.Report/definition.pbir` | Report definition: binds the report to the semantic model by relative path. |
| 00:10 | `powerbi/TradeWar.Report/definition/pages/p01_exec/page.json` | Page 'Executive Summary': canvas size, visibility and display settings. |
| 00:15 | `powerbi/TradeWar.Report/definition/pages/p02_map/page.json` | Page 'Global Trade Map': canvas size, visibility and display settings. |
| 00:21 | `powerbi/TradeWar.Report/definition/pages/p03_deepdive/page.json` | Page 'Country Deep-Dive': canvas size, visibility and display settings. |
| 00:28 | `powerbi/TradeWar.Report/definition/pages/p04_household/page.json` | Page 'Household Economy': canvas size, visibility and display settings. |
| 00:34 | `powerbi/TradeWar.Report/definition/pages/p05_oil/page.json` | Page 'Iran War & Oil Shock': canvas size, visibility and display settings. |
| 00:40 | `powerbi/TradeWar.Report/definition/pages/p06_markets/page.json` | Page 'Global Markets Reaction': canvas size, visibility and display settings. |
| 00:46 | `powerbi/TradeWar.Report/definition/pages/p07_forecast/page.json` | Page 'Forecast & Scenarios': canvas size, visibility and display settings. |
| 00:52 | `powerbi/TradeWar.Report/definition/pages/p08_tooltip/page.json` | Page 'Country Tooltip': canvas size, visibility and display settings. |
| 00:58 | `powerbi/TradeWar.Report/definition/pages/pages.json` | Page order and the default (first) page. |
| 01:02 | `powerbi/TradeWar.Report/definition/report.json` | Report-level settings: custom theme, collapsed panes, page settings. |
| 01:07 | `powerbi/TradeWar.Report/definition/version.json` | PBIR format version. |
| 01:13 | `powerbi/TradeWar.Report/StaticResources/RegisteredResources/TradeWarNavyAmber.json` | Custom navy/amber report theme (colours, fonts, visual defaults). |
| 01:19 | `tests/conftest.py` | Shared fixtures. Warehouse-dependent tests skip cleanly when the DuckDB file is absent (e.g. in CI). |
| 01:23 | `tests/test_ml_outputs.py` | Smoke tests on the ML outputs written to the ml schema by `python -m ml.run_all`. |
| 01:29 | `tests/test_seeds.py` | Seeds are the hand-verified event timeline: they must parse and carry sources. |
| 01:34 | `tests/test_sql_analyses.py` | Every numbered analysis in sql/analysis must run and return rows. |
| 01:38 | `tests/test_warehouse.py` | Smoke tests on the built DuckDB warehouse (star schema + Power BI marts). |
| 01:43 | `tools/gen_data_dictionary.py` | Generate docs/data_dictionary.md from the built warehouse (column names/types) and dbt YAML descriptions. |
| 01:49 | `tools/secret_scan.py` | Light secret scanner: working tree (tracked + to-be-committed data) and full git history. |
| 01:55 | `docs/data_dictionary.md` | Data dictionary: every warehouse table and column with types and descriptions. |
| 02:01 | `docs/ml_report.md` | Generated ML report: methods, tables and figures for every model, with caveats. |

Regenerate: `python tools/walkthrough/plan.py`, then `powershell -File tools/walkthrough/record.ps1`, then `python tools/walkthrough/index.py` (writes the MP4s and this file).
