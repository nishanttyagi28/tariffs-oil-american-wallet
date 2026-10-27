"""DAX measures for the TradeWar semantic model: (name, display folder, format string, DAX expression).

All "%" measures return fractions (0.05 = 5%). "$bn" measures divide the $M warehouse columns by 1,000.
"""
from __future__ import annotations

PCT = "0.0%"
SPCT = "+0.0%;-0.0%;0.0%"
BN = "$#,0.0;-$#,0.0;$0.0"
BN0 = "$#,0;-$#,0;$0"
USD = "$#,0.00"
USD0 = "$#,0"
NUM1 = "#,0.0"
NUM0 = "#,0"
PP = "+0.0;-0.0;0.0"
MONTH = "mmm yyyy"

PREWAR = "DATE(2026, 2, 27)"
WAR = "DATE(2026, 2, 28)"


def latest(table: str, date_col: str, value_expr: str, value_col: str | None = None) -> str:
    """Value of value_expr in the last month/day where value_col is non-blank (ignores the Date filter)."""
    vc = value_col or date_col
    return (f"VAR _last = CALCULATE ( MAX ( {table}[{date_col}] ), REMOVEFILTERS ( 'Date' ), "
            f"FILTER ( ALL ( {table}[{vc}] ), NOT ISBLANK ( {table}[{vc}] ) ) )\n"
            f"RETURN CALCULATE ( {value_expr}, REMOVEFILTERS ( 'Date' ), {table}[{date_col}] = _last )")


M: list[tuple[str, str, str, str]] = []


def m(name: str, folder: str, fmt: str, expr: str) -> None:
    M.append((name, folder, fmt, expr.strip()))


# ---------------------------------------------------------------- Trade
F = "Trade"
m("Imports ($bn)", F, BN, "DIVIDE ( SUM ( Trade[Imports $M] ), 1000 )")
m("Exports ($bn)", F, BN, "DIVIDE ( SUM ( Trade[Exports $M] ), 1000 )")
m("Trade Balance ($bn)", F, BN, "DIVIDE ( SUM ( Trade[Balance $M] ), 1000 )")
m("Total Trade ($bn)", F, BN, "DIVIDE ( SUM ( Trade[Total Trade $M] ), 1000 )")
m("Imports LY ($bn)", F, BN, "CALCULATE ( [Imports ($bn)], DATEADD ( 'Date'[Date], -1, YEAR ) )")
m("Exports LY ($bn)", F, BN, "CALCULATE ( [Exports ($bn)], DATEADD ( 'Date'[Date], -1, YEAR ) )")
m("Imports YoY %", F, SPCT, "VAR _cy = [Imports ($bn)]\nVAR _ly = [Imports LY ($bn)]\nRETURN IF ( NOT ISBLANK ( _cy ) && NOT ISBLANK ( _ly ), DIVIDE ( _cy - _ly, _ly ) )")
m("Exports YoY %", F, SPCT, "VAR _cy = [Exports ($bn)]\nVAR _ly = [Exports LY ($bn)]\nRETURN IF ( NOT ISBLANK ( _cy ) && NOT ISBLANK ( _ly ), DIVIDE ( _cy - _ly, _ly ) )")
m("Imports YTD ($bn)", F, BN, "TOTALYTD ( [Imports ($bn)], 'Date'[Date] )")
m("Last Trade Month", F, MONTH, "CALCULATE ( MAX ( Trade[Month] ), REMOVEFILTERS ( 'Date' ) )")
m("Imports Last 12M ($bn)", F, BN, "VAR _m = [Last Trade Month]\nRETURN CALCULATE ( [Imports ($bn)], REMOVEFILTERS ( 'Date' ), 'Date'[Date] > EDATE ( _m, -12 ), 'Date'[Date] <= _m )")
m("Share of US Imports %", F, PCT, "DIVIDE ( [Imports ($bn)], CALCULATE ( [Imports ($bn)], REMOVEFILTERS ( Country ) ) )")
m("Import Rank", F, NUM0, "IF ( HASONEVALUE ( Country[Country] ) && NOT ISBLANK ( [Imports ($bn)] ), RANKX ( ALLSELECTED ( Country[Country] ), [Imports ($bn)], , DESC, DENSE ) )")
m("Avg Monthly Imports 2024 ($bn)", F, BN, "DIVIDE ( CALCULATE ( SUM ( Trade[Imports $M] ), REMOVEFILTERS ( 'Date' ), 'Date'[Year] = 2024 ), 12000 )")
m("Avg Monthly Imports After ($bn)", F, BN,
  "VAR _v = CALCULATE ( SUM ( Trade[Imports $M] ), KEEPFILTERS ( 'Date'[Date] >= DATE ( 2025, 4, 1 ) ) )\n"
  "VAR _n = CALCULATE ( DISTINCTCOUNT ( Trade[Month] ), KEEPFILTERS ( 'Date'[Date] >= DATE ( 2025, 4, 1 ) ), REMOVEFILTERS ( Country ) )\n"
  "RETURN DIVIDE ( _v, _n * 1000 )")
m("Import Change vs 2024 %", F, SPCT,
  "VAR _a = [Avg Monthly Imports After ($bn)]\nVAR _b = [Avg Monthly Imports 2024 ($bn)]\nRETURN IF ( _a > 0 && _b > 0, _a / _b - 1 )")
m("Import Change Top 20 %", F, SPCT,
  "IF ( SELECTEDVALUE ( Country[Entity Type] ) = \"country\" && MIN ( 'Country Before After'[Import Rank Before] ) <= 20, [Import Change vs 2024 %] )")
m("Map Colour Imports", F, "",
  "VAR _x = [Import Change vs 2024 %]\nRETURN SWITCH ( TRUE (), ISBLANK ( _x ) || SELECTEDVALUE ( Country[Entity Type] ) <> \"country\", BLANK (),\n"
  "    _x <= -0.30, \"#B23A1E\", _x <= -0.10, \"#E4572E\", _x < 0, \"#F4A582\", _x < 0.10, \"#A6DBD5\", _x < 0.30, \"#1AA39A\", \"#0E6B64\" )")
m("Selected Trade Metric ($bn)", F, BN,
  "SWITCH ( SELECTEDVALUE ( 'Trade Metric'[Metric], \"Imports\" ),\n    \"Imports\", [Imports ($bn)],\n    \"Exports\", [Exports ($bn)],\n"
  "    \"Trade balance\", [Trade Balance ($bn)],\n    \"Total trade\", [Total Trade ($bn)] )")
m("Selected Trade Metric LY ($bn)", F, BN, "CALCULATE ( [Selected Trade Metric ($bn)], DATEADD ( 'Date'[Date], -1, YEAR ) )")
m("Selected Trade Metric YoY %", F, SPCT,
  "VAR _cy = [Selected Trade Metric ($bn)]\nVAR _ly = [Selected Trade Metric LY ($bn)]\nRETURN IF ( NOT ISBLANK ( _ly ), DIVIDE ( _cy - _ly, ABS ( _ly ) ) )")
m("Trade Trend Title", F, "",
  "SELECTEDVALUE ( 'Trade Metric'[Metric], \"Imports\" ) & \" by month ($bn), \" &\n"
  "IF ( HASONEVALUE ( Country[Map Name] ), VALUES ( Country[Map Name] ), \"all partners\" ) & \" (with same month last year)\"")
m("Diverted Imports ($bn)", F, BN, "DIVIDE ( SUM ( 'Trade Diversion'[Diverted Imports $M] ), 1000 )")
m("Import Share of Group %", F, PCT, "AVERAGE ( 'Trade Diversion'[Import Share] )")
m("Share Change vs 2024 (pp)", F, PP, "AVERAGE ( 'Trade Diversion'[Share Change pp] )")

# ---------------------------------------------------------------- Tariffs
F = "Tariffs"
m("Statutory Tariff Rate %", F, PCT, "AVERAGE ( 'Tariff Rate'[Statutory Rate %] )")
m("Peak Statutory Rate %", F, PCT, "MAX ( 'Tariff Rate'[Max Rate in Month %] )")
m("Statutory Tariff Latest %", F, PCT,
  "VAR _m = DATE ( YEAR ( TODAY () ), MONTH ( TODAY () ), 1 )\nRETURN CALCULATE ( AVERAGE ( 'Tariff Rate'[Statutory Rate %] ), REMOVEFILTERS ( 'Date' ), 'Tariff Rate'[Month] = _m )")
m("Map Colour Tariff", F, "",
  "VAR _x = [Peak Statutory Rate %]\nRETURN SWITCH ( TRUE (), ISBLANK ( _x ) || SELECTEDVALUE ( Country[Entity Type] ) <> \"country\", BLANK (),\n"
  "    _x >= 0.5, \"#7A2E0E\", _x >= 0.3, \"#C8553D\", _x >= 0.2, \"#F2A541\", _x >= 0.15, \"#F6C985\", _x >= 0.1, \"#FBE6C2\", \"#DCE3EE\" )")
m("Customs Gross ($bn)", F, BN, "DIVIDE ( SUM ( Customs[Gross Receipts $M] ), 1000 )")
m("Customs Refunds ($bn)", F, BN, "DIVIDE ( SUM ( Customs[Refunds $M] ), 1000 )")
m("Customs Net ($bn)", F, BN, "DIVIDE ( SUM ( Customs[Net Receipts $M] ), 1000 )")
m("Effective Tariff Rate %", F, PCT, "DIVIDE ( SUM ( Customs[Gross Receipts $M] ), SUM ( Customs[US Imports $M] ) )")
m("Effective Tariff Rate Net %", F, PCT, "DIVIDE ( SUM ( Customs[Net Receipts $M] ), SUM ( Customs[US Imports $M] ) )")
m("Effective Tariff Latest %", F, PCT, latest("Customs", "Month", "[Effective Tariff Rate %]", "Effective Rate Gross %"))
m("Effective Tariff 2024 %", F, PCT, "CALCULATE ( [Effective Tariff Rate %], REMOVEFILTERS ( 'Date' ), 'Date'[Year] = 2024 )")
m("Effective Tariff Change (pp)", F, PP, "( [Effective Tariff Latest %] - [Effective Tariff 2024 %] ) * 100")
m("Incremental Customs vs 2024 ($bn)", F, BN, "DIVIDE ( SUM ( Customs[Incremental Net vs 2024 $M] ), 1000 )")
m("Cumulative Incremental Customs ($bn)", F, BN,
  "VAR _d = MAX ( 'Date'[Date] )\nRETURN IF ( _d >= DATE ( 2025, 2, 1 ), DIVIDE ( CALCULATE ( SUM ( Customs[Incremental Net vs 2024 $M] ), REMOVEFILTERS ( 'Date' ),\n"
  "    Customs[Month] >= DATE ( 2025, 2, 1 ), Customs[Month] <= _d ), 1000 ) )")
m("Customs Windfall to Date ($bn)", F, BN,
  "DIVIDE ( CALCULATE ( SUM ( Customs[Incremental Net vs 2024 $M] ), REMOVEFILTERS ( 'Date' ), Customs[Month] >= DATE ( 2025, 2, 1 ) ), 1000 )")
m("Tariff Events (#)", F, NUM0, "CALCULATE ( COUNTROWS ( Events ), Events[Event Family] = \"Tariff\" )")
m("War Events (#)", F, NUM0, "CALCULATE ( COUNTROWS ( Events ), Events[Event Family] = \"Iran war\" )")

# ---------------------------------------------------------------- Household
F = "Household"
m("Tariff Cost per Household ($/mo)", F, USD0, "SUM ( Customs[Incremental Gross per Household USD] )")
m("Household Tariff Cost to Date ($)", F, USD0,
  "CALCULATE ( SUM ( Customs[Incremental Gross per Household USD] ), REMOVEFILTERS ( 'Date' ), Customs[Month] >= DATE ( 2025, 2, 1 ) )")
m("Cumulative Tariff Cost per Household ($)", F, USD0,
  "VAR _d = MAX ( 'Date'[Date] )\nRETURN IF ( _d >= DATE ( 2025, 2, 1 ), CALCULATE ( SUM ( Customs[Incremental Gross per Household USD] ), REMOVEFILTERS ( 'Date' ),\n"
  "    Customs[Month] >= DATE ( 2025, 2, 1 ), Customs[Month] <= _d ) )")
m("CPI YoY %", F, PCT, "AVERAGE ( CPI[YoY %] )")
m("CPI YoY Latest %", F, PCT, latest("CPI", "Month", "AVERAGE ( CPI[YoY %] )", "YoY %"))
m("CPI Change since Jan 2025 %", F, SPCT, latest("CPI", "Month", "AVERAGE ( CPI[Change since Jan2025 %] )", "Change since Jan2025 %"))
m("Exposure Colour", F, "",
  "SWITCH ( SELECTEDVALUE ( 'CPI Category'[Exposure Group] ), \"tariff_exposed_goods\", \"#F2A541\", \"domestic_services\", \"#1AA39A\",\n"
  "    \"energy\", \"#E4572E\", \"energy_sensitive_services\", \"#E4572E\", \"food\", \"#3A86FF\", \"aggregate\", \"#0B1F3A\", \"#5B6B82\" )")
m("Headline CPI YoY %", F, PCT, "AVERAGE ( Household[CPI Headline YoY %] )")
m("Core CPI YoY %", F, PCT, "AVERAGE ( Household[CPI Core YoY %] )")
m("Core Goods CPI YoY %", F, PCT, "AVERAGE ( Household[CPI Core Goods YoY %] )")
m("Core Services CPI YoY %", F, PCT, "AVERAGE ( Household[CPI Core Services YoY %] )")
m("Gasoline CPI YoY %", F, PCT, "AVERAGE ( Household[CPI Gasoline YoY %] )")
m("Tariff-exposed Goods YoY %", F, PCT, "AVERAGE ( Household[Tariff Exposed Goods YoY %] )")
m("Domestic Services YoY %", F, PCT, "AVERAGE ( Household[Domestic Services YoY %] )")
m("Goods minus Services Gap %", F, SPCT, "AVERAGE ( Household[Tariff Goods Minus Services pp] )")
m("Headline CPI Latest YoY %", F, PCT, latest("Household", "Month", "[Headline CPI YoY %]", "CPI Headline YoY %"))
m("Core Goods Latest YoY %", F, PCT, latest("Household", "Month", "[Core Goods CPI YoY %]", "CPI Core Goods YoY %"))
m("Real Wage YoY %", F, SPCT, "AVERAGE ( Household[Real Wage YoY %] )")
m("Real Wage Latest YoY %", F, SPCT, latest("Household", "Month", "[Real Wage YoY %]", "Real Wage YoY %"))
m("Consumer Sentiment", F, NUM1, "AVERAGE ( Household[Consumer Sentiment] )")
m("Gasoline Price ($/gal)", F, USD, "AVERAGE ( Household[Gasoline USD Gal] )")
m("Gasoline Latest ($/gal)", F, USD, latest("Household", "Month", "[Gasoline Price ($/gal)]", "Gasoline USD Gal"))
m("Pass-through DiD (pp/yr)", F, PP,
  "CALCULATE ( SUM ( 'Pass-through'[Annualised Coef] ), 'Pass-through'[Spec] = \"did_main\", 'Pass-through'[Term] = \"treat_post\" )")
m("Pass-through DiD Text", F, "",
  "VAR _lo = CALCULATE ( SUM ( 'Pass-through'[CI Lo] ), 'Pass-through'[Spec] = \"did_main\", 'Pass-through'[Term] = \"treat_post\" ) * 12\n"
  "VAR _hi = CALCULATE ( SUM ( 'Pass-through'[CI Hi] ), 'Pass-through'[Spec] = \"did_main\", 'Pass-through'[Term] = \"treat_post\" ) * 12\n"
  "VAR _p = CALCULATE ( SUM ( 'Pass-through'[P Value] ), 'Pass-through'[Spec] = \"did_main\", 'Pass-through'[Term] = \"treat_post\" )\n"
  "RETURN \"95% CI \" & FORMAT ( _lo, \"0.0\" ) & \" to \" & FORMAT ( _hi, \"0.0\" ) & \" pp/yr, p = \" & FORMAT ( _p, \"0.000\" )")
m("Event-study Coef (pp/mo)", F, "0.00", "CALCULATE ( SUM ( 'Pass-through'[Coef] ), 'Pass-through'[Spec] = \"event_study\" )")
m("Event-study CI Lo", F, "0.00", "CALCULATE ( SUM ( 'Pass-through'[CI Lo] ), 'Pass-through'[Spec] = \"event_study\" )")
m("Event-study CI Hi", F, "0.00", "CALCULATE ( SUM ( 'Pass-through'[CI Hi] ), 'Pass-through'[Spec] = \"event_study\" )")
m("CPI Category Title", F, "",
  "\"CPI YoY by category, latest month (\" & FORMAT ( CALCULATE ( MAX ( CPI[Month] ), REMOVEFILTERS ( 'Date' ), FILTER ( ALL ( CPI[YoY %] ), NOT ISBLANK ( CPI[YoY %] ) ) ), \"mmm yyyy\" ) & \"), amber = tariff-exposed goods\"")

# ---------------------------------------------------------------- Oil
F = "Oil"
m("Brent ($/bbl)", F, USD, "AVERAGE ( Oil[Brent USD] )")
m("WTI ($/bbl)", F, USD, "AVERAGE ( Oil[WTI USD] )")
m("Brent Latest ($/bbl)", F, USD, latest("Oil", "Date", "[Brent ($/bbl)]", "Brent USD"))
m("Brent Pre-war ($/bbl)", F, USD, f"CALCULATE ( [Brent ($/bbl)], REMOVEFILTERS ( 'Date' ), Oil[Date] = {PREWAR} )")
m("Brent vs Pre-war %", F, SPCT, "DIVIDE ( [Brent Latest ($/bbl)], [Brent Pre-war ($/bbl)] ) - 1")
m("Brent War Peak ($/bbl)", F, USD, f"CALCULATE ( MAX ( Oil[Brent USD] ), REMOVEFILTERS ( 'Date' ), Oil[Date] >= {WAR} )")
m("Brent Drawdown from War Peak %", F, SPCT, "DIVIDE ( [Brent Latest ($/bbl)], [Brent War Peak ($/bbl)] ) - 1")
m("Brent 52w Drawdown %", F, SPCT, "AVERAGE ( Oil[Brent Drawdown 52w %] )")
m("Brent-WTI Spread ($)", F, USD, "AVERAGE ( Oil[Brent WTI Spread USD] )")
m("Brent vs Pre-war (daily) %", F, SPCT, "AVERAGE ( 'Oil Shock'[Brent vs Prewar %] )")
m("Hormuz Transits (7d avg)", F, NUM1, "AVERAGE ( 'Oil Shock'[Hormuz Transits 7d] )")
m("Hormuz Tankers (7d avg)", F, NUM1, "AVERAGE ( 'Oil Shock'[Hormuz Tankers 7d] )")
m("Hormuz Pre-war Baseline", F, NUM1,
  f"CALCULATE ( AVERAGE ( 'Oil Shock'[Hormuz Transits 7d] ), REMOVEFILTERS ( 'Date' ), 'Oil Shock'[Date] = {PREWAR} )")
m("Hormuz vs Pre-war %", F, SPCT, "AVERAGE ( 'Oil Shock'[Hormuz 7d vs Prewar %] )")
m("Hormuz Latest vs Pre-war %", F, SPCT, latest("'Oil Shock'", "Date", "[Hormuz vs Pre-war %]", "Hormuz 7d vs Prewar %"))
m("IRF (%)", F, "0.00", "AVERAGE ( IRF[IRF] )")
m("IRF Lo 95", F, "0.00", "AVERAGE ( IRF[CI Lo 95] )")
m("IRF Hi 95", F, "0.00", "AVERAGE ( IRF[CI Hi 95] )")
m("Gasoline IRF 1m (%)", F, "+0.0;-0.0", "CALCULATE ( [IRF (%)], IRF[Outcome] = \"gasoline_cpi\", IRF[Horizon Months] = 1 )")
m("Days Since War Began", F, NUM0, f"DATEDIFF ( {WAR}, TODAY (), DAY )")
m("Oil Title", F, "",
  "\"Brent & WTI ($/bbl) with Iran-war events, Brent latest \" & FORMAT ( [Brent Latest ($/bbl)], \"$0.0\" ) & \" (\" &\n"
  "FORMAT ( [Brent vs Pre-war %], \"+0%;-0%\" ) & \" vs pre-war)\"")

# ---------------------------------------------------------------- Markets
F = "Markets"
m("CAR %", F, SPCT, "AVERAGE ( 'Event Study'[CAR %] )")
m("CAR D+5 %", F, SPCT, "CALCULATE ( [CAR %], 'Event Study'[Window Label] = \"D+5\" )")
m("CAR D+20 %", F, SPCT, "CALCULATE ( [CAR %], 'Event Study'[Window Label] = \"D+20\" )")
m("Brent War CAR D+5 %", F, SPCT,
  "CALCULATE ( [CAR %], REMOVEFILTERS ( 'Event Study' ), 'Event Study'[Symbol] = \"BZ=F\", 'Event Study'[Event ID] = \"W02\", 'Event Study'[Window Label] = \"D+5\" )")
m("S&P 500 War CAR D+20 %", F, SPCT,
  "CALCULATE ( [CAR %], REMOVEFILTERS ( 'Event Study' ), 'Event Study'[Symbol] = \"^GSPC\", 'Event Study'[Event ID] = \"W02\", 'Event Study'[Window Label] = \"D+20\" )")
m("Significant CARs %", F, PCT,
  "DIVIDE ( CALCULATE ( COUNTROWS ( 'Event Study' ), 'Event Study'[Significant 5%] = TRUE () ), COUNTROWS ( 'Event Study' ) )")
m("CAR Colour", F, "",
  "VAR _x = [CAR D+5 %]\nRETURN SWITCH ( TRUE (), ISBLANK ( _x ), BLANK (), _x <= -0.05, \"#E4572E\", _x <= -0.01, \"#F4A582\", _x < 0.01, \"#EEF2F7\", _x < 0.05, \"#A6DBD5\", \"#1AA39A\" )")
m("Index (pre-war = 100)", F, NUM1, "AVERAGE ( Market[Index Prewar 100] )")
m("Index (2025 = 100)", F, NUM1, "AVERAGE ( Market[Index 2025 100] )")
m("Realised Vol 21d", F, PCT, "AVERAGE ( Market[Vol 21d Ann.] )")
m("High-vol Probability", F, PCT, "AVERAGE ( 'Vol Regimes'[Prob High Vol] )")
m("High-vol Days %", F, PCT,
  "DIVIDE ( CALCULATE ( COUNTROWS ( 'Vol Regimes' ), 'Vol Regimes'[Regime] = \"high-vol\" ), COUNTROWS ( 'Vol Regimes' ) )")
m("GARCH Vol (ann.)", F, PCT, "AVERAGE ( 'Vol Regimes'[Garch Vol Ann. %] )")
m("VIX Latest", F, NUM1, latest("'Oil Shock'", "Date", "AVERAGE ( 'Oil Shock'[VIX] )", "VIX"))
m("S&P 500 vs Pre-war %", F, SPCT,
  "VAR _last = CALCULATE ( MAX ( Market[Date] ), REMOVEFILTERS ( 'Date' ), Market[Symbol] = \"^GSPC\" )\n"
  "RETURN CALCULATE ( AVERAGE ( Market[Index Prewar 100] ), REMOVEFILTERS ( 'Date' ), Market[Symbol] = \"^GSPC\", Market[Date] = _last ) / 100 - 1")

# ---------------------------------------------------------------- Forecast / ML
F = "Forecast & ML"
m("Selected Target", F, "", "SELECTEDVALUE ( Forecasts[Target], \"brent\" )")
for nm, col, kind in [("Actual (series)", "Value", "actual"), ("Forecast (central)", "Value", "forecast"),
                      ("Forecast Lo 80", "Lo 80", "forecast"), ("Forecast Hi 80", "Hi 80", "forecast"),
                      ("Forecast Lo 95", "Lo 95", "forecast"), ("Forecast Hi 95", "Hi 95", "forecast"),
                      ("AR(1) Alternative", "Value", "forecast_alt"), ("EIA Reference", "Value", "reference_eia")]:
    m(nm, F, "#,0.0", f"VAR _t = [Selected Target]\nRETURN CALCULATE ( AVERAGE ( Forecasts[{col}] ), Forecasts[Kind] = \"{kind}\", Forecasts[Target] = _t )")
m("Actual YoY %", F, PCT, "VAR _t = [Selected Target]\nRETURN CALCULATE ( AVERAGE ( Forecasts[YoY Value] ), Forecasts[Kind] = \"actual\", Forecasts[Target] = _t )")
m("Forecast YoY %", F, PCT, "VAR _t = [Selected Target]\nRETURN CALCULATE ( AVERAGE ( Forecasts[YoY Value] ), Forecasts[Kind] = \"forecast\", Forecasts[Target] = _t )")
m("Forecast YoY Lo 80", F, PCT, "VAR _t = [Selected Target]\nRETURN CALCULATE ( AVERAGE ( Forecasts[YoY Lo 80] ), Forecasts[Kind] = \"forecast\", Forecasts[Target] = _t )")
m("Forecast YoY Hi 80", F, PCT, "VAR _t = [Selected Target]\nRETURN CALCULATE ( AVERAGE ( Forecasts[YoY Hi 80] ), Forecasts[Kind] = \"forecast\", Forecasts[Target] = _t )")


def _fc(target: str, kind: str, d0: str, d1: str, col: str = "Value", extra: str = "") -> str:
    return (f"CALCULATE ( AVERAGE ( Forecasts[{col}] ), REMOVEFILTERS ( Forecasts ), REMOVEFILTERS ( 'Date' ), Forecasts[Target] = \"{target}\",\n"
            f"    Forecasts[Kind] = \"{kind}\", Forecasts[Month] >= {d0}, Forecasts[Month] <= {d1}{extra} )")


Q4 = ("DATE ( 2026, 10, 1 )", "DATE ( 2026, 12, 1 )")
m("Brent Forecast Q4 2026 ($)", F, USD, _fc("brent", "forecast", *Q4))
m("Brent AR(1) Q4 2026 ($)", F, USD, _fc("brent", "forecast_alt", *Q4))
m("EIA Brent 4Q26 ($)", F, USD,
  "CALCULATE ( AVERAGE ( Forecasts[Value] ), REMOVEFILTERS ( Forecasts ), REMOVEFILTERS ( 'Date' ), Forecasts[Kind] = \"reference_eia\",\n"
  "    Forecasts[Target] = \"brent\", CONTAINSSTRING ( Forecasts[Model], \"4Q26\" ) )")
m("Brent Forecast minus EIA ($)", F, "+$0.0;-$0.0", "[Brent Forecast Q4 2026 ($)] - [EIA Brent 4Q26 ($)]")
m("Headline CPI Forecast Oct-26 %", F, PCT, _fc("headline_cpi", "forecast", "DATE ( 2026, 10, 1 )", "DATE ( 2026, 10, 1 )", "YoY Value"))
m("Headline CPI Forecast Mar-27 %", F, PCT, _fc("headline_cpi", "forecast", "DATE ( 2027, 3, 1 )", "DATE ( 2027, 3, 1 )", "YoY Value"))
m("Forecast Title", F, "",
  "\"Forecast: \" & SELECTEDVALUE ( Forecasts[Target Label], \"Brent (default, pick a target)\" ) & \", central path with 80% / 95% intervals, AR(1) alternative and EIA STEO\"")
m("WAPE (best model)", F, PCT,
  "CALCULATE ( AVERAGE ( 'Model Metrics'[Value] ), 'Model Metrics'[Metric] = \"wape\", 'Model Metrics'[Is Best] = TRUE () )")
m("Median WAPE (best models)", F, PCT,
  "MEDIANX ( VALUES ( 'Model Metrics'[Series ID] ), CALCULATE ( AVERAGE ( 'Model Metrics'[Value] ), 'Model Metrics'[Metric] = \"wape\", 'Model Metrics'[Is Best] = TRUE () ) )")
m("Actual ($bn)", F, BN, "DIVIDE ( SUM ( Counterfactual[Actual $M] ), 1000 )")
for nm, col in [("Counterfactual ($bn)", "Counterfactual $M"), ("CF Lo 95 ($bn)", "CF Lo 95"), ("CF Hi 95 ($bn)", "CF Hi 95"),
                ("CF Lo 80 ($bn)", "CF Lo 80"), ("CF Hi 80 ($bn)", "CF Hi 80")]:
    m(nm, F, BN, f"DIVIDE ( CALCULATE ( SUM ( Counterfactual[{col}] ), Counterfactual[Is Post-Tariff] = TRUE () ), 1000 )")
m("Monthly Tariff Effect ($bn)", F, BN, "DIVIDE ( CALCULATE ( SUM ( Counterfactual[Effect $M] ), Counterfactual[Is Post-Tariff] = TRUE () ), 1000 )")
EW = "'Tariff Effect'[Effect Window] = \"Apr 2025-latest\", 'Tariff Effect'[Partner Code] <> \"TOTAL\""
m("Effect since Apr 2025 ($bn)", F, BN, f"DIVIDE ( CALCULATE ( SUM ( 'Tariff Effect'[Effect $M] ), {EW} ), 1000 )")
m("Effect Lo 95 ($bn)", F, BN, f"DIVIDE ( CALCULATE ( SUM ( 'Tariff Effect'[Effect Lo 95] ), {EW} ), 1000 )")
m("Effect Hi 95 ($bn)", F, BN, f"DIVIDE ( CALCULATE ( SUM ( 'Tariff Effect'[Effect Hi 95] ), {EW} ), 1000 )")
m("Effect since Apr 2025 %", F, SPCT, f"CALCULATE ( AVERAGE ( 'Tariff Effect'[Effect %] ), {EW} )")
m("Effect Colour", F, "", "IF ( [Effect since Apr 2025 ($bn)] < 0, \"#E4572E\", \"#1AA39A\" )")
CHN = "'Tariff Effect'[Partner Code] = \"CHN\", 'Tariff Effect'[Flow] = \"imports\""
m("China Import Effect ($bn)", F, BN, f"CALCULATE ( [Effect since Apr 2025 ($bn)], REMOVEFILTERS ( Partner ), {CHN} )")
m("China Import Effect %", F, SPCT, f"CALCULATE ( [Effect since Apr 2025 %], REMOVEFILTERS ( Partner ), {CHN} )")

# deep-dive measures default to China when no single partner is in context
F = "Deep-dive"
m("DD Partner", F, "", "SELECTEDVALUE ( Partner[Partner], \"China\" )")
m("DD Code", F, "", "SELECTEDVALUE ( Partner[Partner Code], \"CHN\" )")
for nm, col in [("DD Actual Imports ($bn)", "Actual $M"), ("DD Counterfactual ($bn)", "Counterfactual $M"),
                ("DD CF Lo 95 ($bn)", "CF Lo 95"), ("DD CF Hi 95 ($bn)", "CF Hi 95")]:
    post = "" if nm.startswith("DD Actual") else ", Counterfactual[Is Post-Tariff] = TRUE ()"
    m(nm, F, BN, f"VAR _p = [DD Code]\nRETURN DIVIDE ( CALCULATE ( SUM ( Counterfactual[{col}] ), REMOVEFILTERS ( Partner ),\n"
                 f"    Counterfactual[Partner Code] = _p, Counterfactual[Flow] = \"imports\"{post} ), 1000 )")
m("DD Statutory Tariff %", F, PCT,
  "VAR _p = [DD Code]\nRETURN CALCULATE ( AVERAGE ( 'Tariff Rate'[Statutory Rate %] ), REMOVEFILTERS ( Partner ), Partner[Partner Code] = _p )")
m("DD Current Tariff %", F, PCT,
  "VAR _p = [DD Code]\nRETURN CALCULATE ( [Statutory Tariff Latest %], REMOVEFILTERS ( Partner ), Partner[Partner Code] = _p )")
m("DD Peak Tariff %", F, PCT,
  "VAR _p = [DD Code]\nRETURN CALCULATE ( MAX ( 'Tariff Rate'[Max Rate in Month %] ), REMOVEFILTERS ( Partner ), REMOVEFILTERS ( 'Date' ), Partner[Partner Code] = _p )")
for nm, col, flow in [("DD Import Effect ($bn)", "Effect $M", "imports"), ("DD Export Effect ($bn)", "Effect $M", "exports"),
                      ("DD Import Effect Lo 95 ($bn)", "Effect Lo 95", "imports"), ("DD Import Effect Hi 95 ($bn)", "Effect Hi 95", "imports")]:
    m(nm, F, BN, f"VAR _p = [DD Code]\nRETURN DIVIDE ( CALCULATE ( SUM ( 'Tariff Effect'[{col}] ), REMOVEFILTERS ( Partner ), 'Tariff Effect'[Partner Code] = _p,\n"
                 f"    'Tariff Effect'[Flow] = \"{flow}\", 'Tariff Effect'[Effect Window] = \"Apr 2025-latest\" ), 1000 )")
m("DD Import Effect %", F, SPCT,
  "VAR _p = [DD Code]\nRETURN CALCULATE ( AVERAGE ( 'Tariff Effect'[Effect %] ), REMOVEFILTERS ( Partner ), 'Tariff Effect'[Partner Code] = _p,\n"
  "    'Tariff Effect'[Flow] = \"imports\", 'Tariff Effect'[Effect Window] = \"Apr 2025-latest\" )")
m("DD Effect CI Text", F, "",
  "\"95% interval \" & FORMAT ( [DD Import Effect Lo 95 ($bn)], \"$#,0;-$#,0\" ) & \"bn to \" & FORMAT ( [DD Import Effect Hi 95 ($bn)], \"$#,0;-$#,0\" ) & \"bn\"")
m("DD Title", F, "",
  "\"Country deep-dive: \" & [DD Partner] & IF ( ISFILTERED ( Partner[Partner] ) || ISFILTERED ( Partner[Partner Code] ), \"\", \" (default; pick a partner or drill through from any partner chart)\" )")

# ---------------------------------------------------------------- Story
F = "Story"
m("Executive Story", F, "",
  "VAR _et = [Effective Tariff Latest %]\nVAR _e24 = [Effective Tariff 2024 %]\nVAR _cn = [China Import Effect ($bn)]\nVAR _hh = [Household Tariff Cost to Date ($)]\n"
  "VAR _b = [Brent Latest ($/bbl)]\nVAR _bw = [Brent vs Pre-war %]\nVAR _cpi = [Headline CPI Latest YoY %]\n"
  "RETURN \"Tariffs: the effective US tariff rate moved from \" & FORMAT ( _e24, \"0.0%\" ) & \" in 2024 to \" & FORMAT ( _et, \"0.0%\" ) &\n"
  "    \" in the latest month. Against a no-tariff counterfactual, imports from China are \" & FORMAT ( _cn, \"$#,0;-$#,0\" ) &\n"
  "    \"bn since Apr 2025 while Vietnam and Taiwan gained. Households: customs collections above 2024 levels add up to about \" &\n"
  "    FORMAT ( _hh, \"$#,0\" ) & \" per household. Oil: since the Iran war began on 28 Feb 2026, Brent is at \" & FORMAT ( _b, \"$0\" ) &\n"
  "    \"/bbl (\" & FORMAT ( _bw, \"+0%;-0%\" ) & \" vs pre-war) and headline CPI is \" & FORMAT ( _cpi, \"0.0%\" ) & \" YoY.\"")
m("Data Freshness", F, "",
  "\"Trade to \" & FORMAT ( [Last Trade Month], \"mmm yyyy\" ) & \"  |  markets to \" & FORMAT ( CALCULATE ( MAX ( Oil[Date] ), REMOVEFILTERS ( 'Date' ) ), \"d mmm yyyy\" )")
m("Event-study Title", "Household", "",
  "\"Pass-through event study: exposed goods minus services CPI (pp/month vs quarter -1). DiD \" & FORMAT ( [Pass-through DiD (pp/yr)], \"+0.0\" ) & \" pp/yr, \" & [Pass-through DiD Text]")
m("Tooltip Country", "Story", "", "SELECTEDVALUE ( Country[Map Name], \"Country\" )")