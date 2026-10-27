"""Write the PBIR report (powerbi/TradeWar.Report): theme, 7 story pages + 1 tooltip page."""
from __future__ import annotations

import shutil
from pathlib import Path

from pbi_common import F, color, filter_in, gid, hid, lit, meas, num, proj, write_json
from pbi_theme import AMBER, CORAL, NAVY, SKY, SLATE, TEAL, THEME

SCH = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition"
V_VIS, V_PAGE, V_REP = "2.4.0", "2.0.0", "3.0.0"
THEME_FILE = "TradeWarNavyAmber.json"

YEARS_23_26 = [2023, 2024, 2025, 2026]
YEARS_24_26 = [2024, 2025, 2026]
YEARS_25_26 = [2025, 2026]


class Page:
    def __init__(self, name: str, display: str, subtitle: str = "", width: int = 1280, height: int = 720,
                 ptype: str | None = None, header: bool = True):
        self.name, self.display, self.subtitle = name, display, subtitle
        self.width, self.height, self.ptype = width, height, ptype
        self.visuals: list[dict] = []
        self.binding = None
        self.filters: list[dict] = []
        self.hidden = False
        if header:
            self.header()

    # -------------------------------------------------------------- generic visual
    def add(self, vtype: str, x, y, w, h, roles: dict | None = None, title=None, objects: dict | None = None,
            vco: dict | None = None, filters: list | None = None, sort: list | None = None, key: str | None = None) -> dict:
        name = hid(self.name, key or f"{vtype}{len(self.visuals)}")
        visual: dict = {"visualType": vtype}
        if roles:
            qs = {}
            for role, specs in roles.items():
                ps = []
                for sp in specs:
                    if isinstance(sp, tuple):
                        ps.append(proj(F(sp[0]), sp[1]))
                    else:
                        ps.append(proj(F(sp)))
                qs[role] = {"projections": ps}
            visual["query"] = {"queryState": qs}
            if sort:
                visual["query"]["sortDefinition"] = {
                    "sort": [{"field": F(f), "direction": d} for f, d in sort], "isDefaultSort": False}
        if objects:
            visual["objects"] = objects
        vco = dict(vco or {})
        if title is not None:
            if title is False:
                vco["title"] = [{"properties": {"show": lit(False)}}]
            elif isinstance(title, str) and title.startswith("m:"):
                vco["title"] = [{"properties": {"show": lit(True), "text": {"expr": meas(title[2:])}}}]
            else:
                vco["title"] = [{"properties": {"show": lit(True), "text": lit(title)}}]
        if vco:
            visual["visualContainerObjects"] = vco
        v = {"$schema": f"{SCH}/visualContainer/{V_VIS}/schema.json", "name": name,
             "position": {"x": x, "y": y, "z": len(self.visuals) * 1000, "height": h, "width": w, "tabOrder": len(self.visuals) * 1000},
             "visual": visual}
        if filters:
            v["filterConfig"] = {"filters": filters}
        self.visuals.append(v)
        return v

    # -------------------------------------------------------------- building blocks
    def header(self):
        paras = [{"textRuns": [
            {"value": "TARIFFS, OIL & THE AMERICAN WALLET   ", "textStyle": {"fontFamily": "Segoe UI Semibold", "fontSize": "11pt", "color": AMBER}},
            {"value": self.display, "textStyle": {"fontFamily": "Segoe UI Semibold", "fontSize": "18pt", "color": "#FFFFFF"}}]}]
        if self.subtitle:
            paras.append({"textRuns": [{"value": self.subtitle, "textStyle": {"fontFamily": "Segoe UI", "fontSize": "9pt", "color": "#C9D6E8"}}]})
        self.add("textbox", 0, 0, 1280, 60, objects={"general": [{"properties": {"paragraphs": paras}}]},
                 vco={"background": [{"properties": {"show": lit(True), "color": color(NAVY), "transparency": num(0)}}],
                      "border": [{"properties": {"show": lit(False)}}], "dropShadow": [{"properties": {"show": lit(False)}}],
                      "padding": [{"properties": {"top": num(6), "left": num(18)}}]},
                 key="header")
        self.add("pageNavigator", 16, 64, 1248, 36, key="nav",
                 objects={"text": [{"properties": {"fontSize": num(10), "fontFamily": lit("Segoe UI Semibold")}}],
                          "fill": [{"properties": {"fillColor": color("#FFFFFF")}},
                                   {"properties": {"fillColor": color(NAVY)}, "selector": {"id": "selected"}}],
                          "outline": [{"properties": {"show": lit(True), "lineColor": color("#DCE3EE")}}]})

    def kpi(self, x, y, w, h, measure: str, label: str, accent: str = AMBER):
        return self.add("card", x, y, w, h, roles={"Values": [(f"m:{measure}", label)]}, key=f"kpi_{measure}",
                        objects={"labels": [{"properties": {"fontSize": num(20), "labelDisplayUnits": num(1), "color": color(NAVY)}}],
                                 "categoryLabels": [{"properties": {"show": lit(True), "fontSize": num(9)}}]},
                        vco={"border": [{"properties": {"show": lit(True), "color": color(accent), "radius": num(10)}}],
                             "title": [{"properties": {"show": lit(False)}}]})

    def kpi_row(self, items: list[tuple[str, str]], x0=16, y=108, h=84, total_w=1248, gap=12):
        n = len(items)
        w = (total_w - gap * (n - 1)) // n
        accents = [AMBER, TEAL, SKY, CORAL, AMBER, TEAL]
        for i, (msr, label) in enumerate(items):
            self.kpi(x0 + i * (w + gap), y, w, h, msr, label, accents[i % len(accents)])

    def slicer(self, x, y, w, h, field: str, mode: str = "Dropdown", title: str | None = None, single: bool = False):
        objs = {"data": [{"properties": {"mode": lit(mode)}}]}
        if single:
            objs["selection"] = [{"properties": {"strictSingleSelect": lit(True)}}]
        if title:
            objs["header"] = [{"properties": {"show": lit(True), "text": lit(title)}}]
        return self.add("slicer", x, y, w, h, roles={"Values": [field]}, objects=objs, key=f"slicer_{field}")

    def text_card(self, x, y, w, h, measure: str, title: str, size: int = 11):
        return self.add("card", x, y, w, h, roles={"Values": [f"m:{measure}"]}, title=title, key=f"text_{measure}",
                        objects={"labels": [{"properties": {"fontSize": num(size), "wordWrap": lit(True), "color": color(NAVY),
                                                            "fontFamily": lit("Segoe UI")}}],
                                 "categoryLabels": [{"properties": {"show": lit(False)}}]})

    # -------------------------------------------------------------- serialisation
    def write(self, root: Path):
        p = {"$schema": f"{SCH}/page/{V_PAGE}/schema.json", "name": self.name, "displayName": self.display,
             "displayOption": "FitToPage" if self.ptype != "Tooltip" else "ActualSize", "height": self.height, "width": self.width,
             "objects": {"background": [{"properties": {"color": color("#EEF2F7"), "transparency": num(0)}}]}}
        if self.ptype:
            p["type"] = self.ptype
        if self.binding:
            p["pageBinding"] = self.binding
        if self.filters:
            p["filterConfig"] = {"filters": self.filters}
        if self.hidden:
            p["visibility"] = "HiddenInViewMode"
        pd = root / self.name
        write_json(pd / "page.json", p)
        for v in self.visuals:
            write_json(pd / "visuals" / v["name"] / "visual.json", v)


def fill_measure(measure: str):
    return {"dataPoint": [{"properties": {"fill": {"solid": {"color": {"expr": meas(measure)}}}},
                           "selector": {"data": [{"dataViewWildcard": {"matchingOption": 1}}]}}]}


def series_style(styles: dict[str, tuple[str, str | None, float]]):
    """measure -> (hex colour, line style or None, stroke width)."""
    dp, ls = [], []
    for m_, (c, style, width) in styles.items():
        sel = {"metadata": f"_Measures.{m_}"}
        dp.append({"properties": {"fill": color(c)}, "selector": sel})
        props = {"strokeWidth": num(width)}
        if style:
            props["lineStyle"] = lit(style)
        ls.append({"properties": props, "selector": sel})
    return {"dataPoint": dp, "lineStyles": ls}


def yr(years):
    return [filter_in("Date", "Year", years)]


def tooltip_link(page_name: str):
    return {"visualTooltip": [{"properties": {"show": lit(True), "type": lit("ReportPage"), "section": lit(page_name)}}]}


# ====================================================================== pages
def build_pages() -> list[Page]:
    pages: list[Page] = []

    # 1 ---------------------------------------------------------------- Executive
    p = Page("p01_exec", "Executive Summary", "Trump trade war 2025-26, the Iran war oil shock, and what both mean for US households")
    p.kpi_row([("Effective Tariff Latest %", "Effective US tariff rate (latest month)"),
               ("Customs Windfall to Date ($bn)", "Extra customs vs 2024 since Feb 2025 ($bn)"),
               ("Household Tariff Cost to Date ($)", "Tariff cost per household to date"),
               ("China Import Effect ($bn)", "China imports vs counterfactual ($bn)"),
               ("Brent Latest ($/bbl)", "Brent crude, latest ($/bbl)"),
               ("Headline CPI Latest YoY %", "Headline CPI, YoY (latest)")])
    p.add("lineClusteredColumnComboChart", 16, 204, 820, 248,
          roles={"Category": ["Date.Month"], "Y": [("m:Tariff Events (#)", "Tariff events"), ("m:War Events (#)", "Iran-war events")],
                 "Y2": [("m:Effective Tariff Rate %", "Effective tariff rate")]},
          title="Event timeline: tariff and Iran-war events per month vs the effective US tariff rate",
          objects={"dataPoint": [{"properties": {"fill": color(AMBER)}, "selector": {"metadata": "_Measures.Tariff Events (#)"}},
                                 {"properties": {"fill": color(CORAL)}, "selector": {"metadata": "_Measures.War Events (#)"}},
                                 {"properties": {"fill": color(TEAL)}, "selector": {"metadata": "_Measures.Effective Tariff Rate %"}}]},
          filters=yr(YEARS_24_26), key="timeline")
    p.text_card(848, 204, 416, 248, "Executive Story", "The story so far")
    p.add("clusteredBarChart", 16, 464, 616, 248,
          roles={"Category": ["Partner.Partner"], "Y": [("m:Effect since Apr 2025 ($bn)", "Effect vs counterfactual ($bn)")]},
          title="Imports vs no-tariff counterfactual since Apr 2025 ($bn); right-click a bar to drill through",
          objects={**fill_measure("Effect Colour"), "labels": [{"properties": {"show": lit(True)}}]},
          filters=[filter_in("Tariff Effect", "Flow", ["imports"])], sort=[("m:Effect since Apr 2025 ($bn)", "Ascending")], key="effectbar")
    p.add("tableEx", 644, 464, 620, 248,
          roles={"Values": ["Events.Event Date", "Events.Event Family", "Events.Event"]},
          title="Key tariff and Iran-war events", sort=[("Events.Event Date", "Descending")], key="events")
    pages.append(p)

    # 2 ---------------------------------------------------------------- Global trade map
    p = Page("p02_map", "Global Trade Map", "Average monthly US imports since Apr 2025 vs the 2024 average, and the peak statutory tariff by country")
    p.slicer(16, 108, 200, 64, "Date.Year", title="Year")
    p.slicer(228, 108, 260, 64, "Country.Region WB", title="Region")
    p.slicer(500, 108, 280, 64, "Trade Metric.Metric", title="Trend metric", single=True)
    p.kpi(792, 108, 230, 64, "Import Change vs 2024 %", "All partners: imports vs 2024", TEAL)
    p.kpi(1034, 108, 230, 64, "Imports Last 12M ($bn)", "US imports, last 12 months ($bn)", AMBER)
    tip = tooltip_link("p08_tooltip")
    p.add("filledMap", 16, 184, 616, 300,
          roles={"Category": ["Country.Map Name"],
                 "Tooltips": ["m:Import Change vs 2024 %", "m:Imports ($bn)", "m:Peak Statutory Rate %"]},
          title="Import change vs 2024 (red = falling, teal = rising)", objects=fill_measure("Map Colour Imports"),
          vco=tip, filters=[filter_in("Country", "Entity Type", ["country"])], key="map_imports")
    p.add("filledMap", 648, 184, 616, 300,
          roles={"Category": ["Country.Map Name"], "Tooltips": ["m:Peak Statutory Rate %", "m:Statutory Tariff Latest %"]},
          title="Peak statutory US tariff rate in the period (darker = higher)", objects=fill_measure("Map Colour Tariff"),
          vco=tip, filters=[filter_in("Country", "Entity Type", ["country"])], key="map_tariff")
    p.add("clusteredColumnChart", 16, 496, 760, 216,
          roles={"Category": ["Country.Map Name"], "Y": [("m:Import Change Top 20 %", "Import change vs 2024")]},
          title="Partner ranking: top-20 2024 import partners, change in average monthly imports",
          objects={**fill_measure("Map Colour Imports"), "labels": [{"properties": {"show": lit(True)}}]},
          sort=[("m:Import Change Top 20 %", "Descending")], key="ranking")
    p.add("lineChart", 788, 496, 476, 216,
          roles={"Category": ["Date.Month"], "Y": [("m:Selected Trade Metric ($bn)", "This year"), ("m:Selected Trade Metric LY ($bn)", "Last year")]},
          title="m:Trade Trend Title",
          objects=series_style({"Selected Trade Metric ($bn)": (TEAL, None, 2.5), "Selected Trade Metric LY ($bn)": (SLATE, "dashed", 1.5)}),
          filters=yr(YEARS_24_26), key="trend")
    pages.append(p)

    # 3 ---------------------------------------------------------------- Country deep-dive (drill-through)
    p = Page("p03_deepdive", "Country Deep-Dive", "India, China, Canada, EU27, Mexico, Japan and more: tariff steps, counterfactual band and diversion",
             ptype="Drillthrough")
    dd_filter = filter_in("Partner", "Partner", [], name="ddPartnerFilter", how="Drillthrough")
    del dd_filter["filter"]
    p.filters = [dd_filter]
    p.binding = {"name": "ddBinding", "type": "Drillthrough",
                 "parameters": [{"name": "ddPartner", "boundFilter": "ddPartnerFilter", "fieldExpr": F("Partner.Partner")}]}
    p.slicer(16, 108, 200, 84, "Partner.Partner", title="Partner", single=True)
    p.kpi_row([("DD Import Effect ($bn)", "Imports vs counterfactual since Apr 2025 ($bn)"),
               ("DD Import Effect %", "Imports vs counterfactual (%)"),
               ("DD Effect CI Text", "95% interval"),
               ("DD Peak Tariff %", "Peak statutory tariff"),
               ("DD Current Tariff %", "Current statutory tariff")], x0=228, total_w=1036)
    p.add("lineChart", 16, 204, 820, 256,
          roles={"Category": ["Date.Month"],
                 "Y": [("m:DD Actual Imports ($bn)", "Actual"), ("m:DD Counterfactual ($bn)", "Counterfactual"),
                       ("m:DD CF Lo 95 ($bn)", "CF lower 95%"), ("m:DD CF Hi 95 ($bn)", "CF upper 95%")]},
          title="m:DD Title",
          objects=series_style({"DD Actual Imports ($bn)": (NAVY, None, 2.5), "DD Counterfactual ($bn)": (AMBER, None, 2),
                                "DD CF Lo 95 ($bn)": (AMBER, "dotted", 1), "DD CF Hi 95 ($bn)": (AMBER, "dotted", 1)}),
          filters=yr(YEARS_23_26), key="ddline")
    p.add("lineClusteredColumnComboChart", 848, 204, 416, 256,
          roles={"Category": ["Date.Month"], "Y": [("m:DD Actual Imports ($bn)", "Imports ($bn)")],
                 "Y2": [("m:DD Statutory Tariff %", "Statutory tariff")]},
          title="Tariff steps vs monthly imports",
          objects={"dataPoint": [{"properties": {"fill": color("#9FB3CC")}, "selector": {"metadata": "_Measures.DD Actual Imports ($bn)"}},
                                 {"properties": {"fill": color(CORAL)}, "selector": {"metadata": "_Measures.DD Statutory Tariff %"}}]},
          filters=yr(YEARS_24_26), key="ddcombo")
    p.add("lineChart", 16, 472, 620, 240,
          roles={"Category": ["Date.Month"], "Y": [("m:Import Share of Group %", "Share of US imports")], "Series": ["Trade Diversion.Partner Group"]},
          title="Trade diversion: share of US imports by partner",
          filters=yr(YEARS_23_26) + [filter_in("Trade Diversion", "Partner Group",
                                               ["China", "Vietnam", "Mexico", "Taiwan", "European Union", "Canada", "India", "Japan"])],
          key="diversion")
    p.add("tableEx", 648, 472, 616, 240,
          roles={"Values": ["Tariff Effect.Partner", "Tariff Effect.Flow", "Tariff Effect.Effect Window", "Tariff Effect.Effect $M",
                            "Tariff Effect.Effect %", "Tariff Effect.Effect Lo 95", "Tariff Effect.Effect Hi 95", "Tariff Effect.Significant 95"]},
          title="Counterfactual effect by flow and window ($M)", key="ddtable")
    pages.append(p)

    # 4 ---------------------------------------------------------------- Household economy
    p = Page("p04_household", "Household Economy", "Who pays? Tariff collections per household, CPI by category and the goods-vs-services pass-through test")
    p.slicer(16, 108, 200, 84, "CPI Category.Exposure Group", title="CPI exposure group")
    p.kpi_row([("Household Tariff Cost to Date ($)", "Tariff cost per household since Feb 2025"),
               ("Headline CPI Latest YoY %", "Headline CPI YoY"),
               ("Core Goods Latest YoY %", "Core goods CPI YoY"),
               ("Pass-through DiD (pp/yr)", "Pass-through DiD (pp/yr)"),
               ("Real Wage Latest YoY %", "Real wage growth YoY")], x0=228, total_w=1036)
    p.add("lineChart", 16, 204, 620, 256,
          roles={"Category": ["Date.Month"], "Y": [("m:Tariff-exposed Goods YoY %", "Tariff-exposed goods"),
                                                   ("m:Domestic Services YoY %", "Domestic services"),
                                                   ("m:Headline CPI YoY %", "Headline CPI"), ("m:Core Goods CPI YoY %", "Core goods")]},
          title="Inflation: tariff-exposed goods vs domestic services (YoY)",
          objects=series_style({"Tariff-exposed Goods YoY %": (AMBER, None, 2.5), "Domestic Services YoY %": (TEAL, None, 2.5),
                                "Headline CPI YoY %": (NAVY, "dashed", 1.5), "Core Goods CPI YoY %": (CORAL, "dotted", 1.5)}),
          filters=yr(YEARS_23_26), key="cpilines")
    p.add("clusteredBarChart", 648, 204, 616, 256,
          roles={"Category": ["CPI Category.Category"], "Y": [("m:CPI YoY Latest %", "CPI YoY")]},
          title="m:CPI Category Title", objects={**fill_measure("Exposure Colour"), "labels": [{"properties": {"show": lit(True)}}]},
          sort=[("m:CPI YoY Latest %", "Descending")], key="cpibar")
    p.add("lineClusteredColumnComboChart", 16, 472, 620, 240,
          roles={"Category": ["Date.Month"], "Y": [("m:Customs Gross ($bn)", "Gross customs ($bn)"), ("m:Customs Refunds ($bn)", "Refunds ($bn)")],
                 "Y2": [("m:Cumulative Tariff Cost per Household ($)", "Cumulative cost per household ($)")]},
          title="Customs receipts ($bn) and cumulative tariff cost per household ($)",
          objects={"dataPoint": [{"properties": {"fill": color(NAVY)}, "selector": {"metadata": "_Measures.Customs Gross ($bn)"}},
                                 {"properties": {"fill": color(CORAL)}, "selector": {"metadata": "_Measures.Customs Refunds ($bn)"}},
                                 {"properties": {"fill": color(AMBER)}, "selector": {"metadata": "_Measures.Cumulative Tariff Cost per Household ($)"}}]},
          filters=yr(YEARS_24_26), key="customs")
    p.add("lineChart", 648, 472, 616, 240,
          roles={"Category": ["Pass-through.Rel Quarter"], "Y": [("m:Event-study Coef (pp/mo)", "Coefficient"),
                                                                 ("m:Event-study CI Lo", "95% low"), ("m:Event-study CI Hi", "95% high")]},
          title="m:Event-study Title",
          objects=series_style({"Event-study Coef (pp/mo)": (NAVY, None, 2.5), "Event-study CI Lo": (SLATE, "dotted", 1),
                                "Event-study CI Hi": (SLATE, "dotted", 1)}),
          key="eventstudy")
    pages.append(p)

    # 5 ---------------------------------------------------------------- Iran war & oil shock
    p = Page("p05_oil", "Iran War & Oil Shock", "Brent and WTI through the war, the Strait of Hormuz, pump prices and impulse responses")
    p.slicer(16, 108, 200, 84, "Date.War Phase", title="War phase")
    p.kpi_row([("Brent Latest ($/bbl)", "Brent, latest ($/bbl)"),
               ("Brent vs Pre-war %", "Brent vs 27 Feb 2026"),
               ("Brent Drawdown from War Peak %", "Brent vs war-time peak"),
               ("Hormuz Latest vs Pre-war %", "Hormuz transits vs pre-war (7d)"),
               ("Gasoline IRF 1m (%)", "Gasoline CPI after +10% Brent, 1m (%)")], x0=228, total_w=1036)
    p.add("lineClusteredColumnComboChart", 16, 204, 820, 256,
          roles={"Category": ["Date.Date"], "Y": [("m:War Events (#)", "Iran-war events")],
                 "Y2": [("m:Brent ($/bbl)", "Brent"), ("m:WTI ($/bbl)", "WTI")]},
          title="m:Oil Title",
          objects={"dataPoint": [{"properties": {"fill": color(CORAL)}, "selector": {"metadata": "_Measures.War Events (#)"}},
                                 {"properties": {"fill": color(NAVY)}, "selector": {"metadata": "_Measures.Brent ($/bbl)"}},
                                 {"properties": {"fill": color(AMBER)}, "selector": {"metadata": "_Measures.WTI ($/bbl)"}}]},
          filters=yr([2026]), key="brent")
    p.add("lineChart", 848, 204, 416, 256,
          roles={"Category": ["Date.Date"], "Y": [("m:Hormuz Transits (7d avg)", "All transits"), ("m:Hormuz Tankers (7d avg)", "Tankers"),
                                                  ("m:Hormuz Pre-war Baseline", "Pre-war baseline")]},
          title="Strait of Hormuz daily transits (7-day average)",
          objects=series_style({"Hormuz Transits (7d avg)": (TEAL, None, 2.5), "Hormuz Tankers (7d avg)": (AMBER, None, 2),
                                "Hormuz Pre-war Baseline": (SLATE, "dashed", 1.5)}),
          filters=yr([2026]), key="hormuz")
    p.add("lineClusteredColumnComboChart", 16, 472, 620, 240,
          roles={"Category": ["Date.Month"], "Y": [("m:Gasoline Price ($/gal)", "Retail gasoline ($/gal)")],
                 "Y2": [("m:Gasoline CPI YoY %", "Gasoline CPI YoY")]},
          title="At the pump: retail gasoline ($/gal) and gasoline CPI YoY",
          objects={"dataPoint": [{"properties": {"fill": color("#9FB3CC")}, "selector": {"metadata": "_Measures.Gasoline Price ($/gal)"}},
                                 {"properties": {"fill": color(CORAL)}, "selector": {"metadata": "_Measures.Gasoline CPI YoY %"}}]},
          filters=yr(YEARS_24_26), key="gas")
    p.add("lineChart", 648, 472, 616, 240,
          roles={"Category": ["IRF.Horizon Months"], "Y": [("m:IRF (%)", "Response"), ("m:IRF Lo 95", "95% low"), ("m:IRF Hi 95", "95% high")]},
          title="Local-projection IRF: gasoline CPI response to a +10% Brent shock (%, by months ahead)",
          objects=series_style({"IRF (%)": (CORAL, None, 2.5), "IRF Lo 95": (SLATE, "dotted", 1), "IRF Hi 95": (SLATE, "dotted", 1)}),
          filters=[filter_in("IRF", "Outcome", ["gasoline_cpi"])], key="irf")
    pages.append(p)

    # 6 ---------------------------------------------------------------- Global markets reaction
    p = Page("p06_markets", "Global Markets Reaction", "Event-study abnormal returns, equity paths since the war and volatility regimes")
    p.slicer(16, 108, 200, 84, "Instrument.Asset Class", title="Asset class")
    p.kpi_row([("S&P 500 War CAR D+20 %", "S&P 500 abnormal return, war D0..D+20"),
               ("Brent War CAR D+5 %", "Brent abnormal return, war D0..D+5"),
               ("VIX Latest", "VIX, latest"),
               ("S&P 500 vs Pre-war %", "S&P 500 vs pre-war close"),
               ("Significant CARs %", "Share of CARs significant at 5%")], x0=228, total_w=1036)
    key_syms = ["^GSPC", "^NSEI", "^STOXX50E", "^N225", "000001.SS", "BZ=F", "GC=F", "^VIX"]
    p.add("pivotTable", 16, 204, 760, 256,
          roles={"Rows": ["Event Study.Event Name"], "Columns": ["Instrument.Instrument"], "Values": [("m:CAR D+5 %", "CAR D0..D+5")]},
          title="Cumulative abnormal returns D0..D+5 by event (market model; red = sell-off)",
          objects={"values": [{"properties": {"backColor": {"solid": {"color": {"expr": meas("CAR Colour")}}}},
                               "selector": {"data": [{"dataViewWildcard": {"matchingOption": 1}}], "metadata": "_Measures.CAR D+5 %"}}],
                   "subTotals": [{"properties": {"rowSubtotals": lit(False), "columnSubtotals": lit(False)}}]},
          filters=[filter_in("Instrument", "Symbol", key_syms)], key="carmatrix")
    p.add("lineChart", 788, 204, 476, 256,
          roles={"Category": ["Date.Date"], "Y": [("m:Index (pre-war = 100)", "Index")], "Series": ["Instrument.Instrument"]},
          title="Equity indices rebased to the last pre-war close (= 100)",
          filters=yr([2026]) + [filter_in("Instrument", "Symbol", ["^GSPC", "^NSEI", "^STOXX50E", "^N225", "000001.SS"])], key="indices")
    p.add("areaChart", 16, 472, 620, 240,
          roles={"Category": ["Date.Date"], "Y": [("m:High-vol Probability", "P(high-vol regime)")], "Series": ["Instrument.Instrument"]},
          title="Markov-switching probability of the high-volatility regime (shaded)",
          filters=yr(YEARS_25_26), key="regimes")
    p.add("lineChart", 648, 472, 616, 240,
          roles={"Category": ["Date.Date"], "Y": [("m:GARCH Vol (ann.)", "GARCH vol (ann.)")], "Series": ["Instrument.Instrument"]},
          title="GARCH(1,1) conditional volatility, annualised",
          filters=yr(YEARS_25_26), key="garch")
    pages.append(p)

    # 7 ---------------------------------------------------------------- Forecast & scenarios
    p = Page("p07_forecast", "Forecast & Scenarios", "Counterfactual gaps with intervals, Brent and CPI forecasts vs EIA STEO, and model accuracy")
    p.slicer(16, 108, 200, 84, "Forecasts.Target Label", title="Forecast target", single=True)
    p.kpi_row([("Brent Forecast Q4 2026 ($)", "Brent Q4 2026, ARIMA ($/bbl)"),
               ("Brent AR(1) Q4 2026 ($)", "Brent Q4 2026, AR(1) ($/bbl)"),
               ("EIA Brent 4Q26 ($)", "EIA STEO Oct-26, 4Q26 ($/bbl)"),
               ("Headline CPI Forecast Oct-26 %", "Headline CPI YoY, Oct 2026 fcst"),
               ("Headline CPI Forecast Mar-27 %", "Headline CPI YoY, Mar 2027 fcst")], x0=228, total_w=1036)
    p.add("lineChart", 16, 204, 820, 256,
          roles={"Category": ["Date.Month"],
                 "Y": [("m:Actual (series)", "Actual"), ("m:Forecast (central)", "Forecast"), ("m:Forecast Lo 80", "80% low"),
                       ("m:Forecast Hi 80", "80% high"), ("m:Forecast Lo 95", "95% low"), ("m:Forecast Hi 95", "95% high"),
                       ("m:AR(1) Alternative", "AR(1) alternative"), ("m:EIA Reference", "EIA STEO")]},
          title="m:Forecast Title",
          objects={**series_style({"Actual (series)": (NAVY, None, 2.5), "Forecast (central)": (AMBER, None, 2.5),
                                   "Forecast Lo 80": (AMBER, "dashed", 1), "Forecast Hi 80": (AMBER, "dashed", 1),
                                   "Forecast Lo 95": (SLATE, "dotted", 1), "Forecast Hi 95": (SLATE, "dotted", 1),
                                   "AR(1) Alternative": (SKY, "dashed", 1.5), "EIA Reference": (CORAL, None, 2)}),
                   "markers": [{"properties": {"show": lit(True), "markerSize": num(3)}}]},
          filters=[filter_in("Date", "Year", [2024, 2025, 2026, 2027])], key="fan")
    p.add("tableEx", 848, 204, 416, 256,
          roles={"Values": ["Model Metrics.Series ID", "Model Metrics.Model", ("m:WAPE (best model)", "WAPE (best)")]},
          title="Counterfactual model accuracy: backtest WAPE of the best model per series",
          filters=[filter_in("Model Metrics", "Task", ["trade_counterfactual"])], sort=[("m:WAPE (best model)", "Ascending")], key="wape")
    p.add("clusteredBarChart", 16, 472, 620, 240,
          roles={"Category": ["Partner.Partner"], "Y": [("m:Effect since Apr 2025 ($bn)", "Effect"), ("m:Effect Lo 95 ($bn)", "95% low"),
                                                        ("m:Effect Hi 95 ($bn)", "95% high")]},
          title="Counterfactual gap in imports since Apr 2025 with 95% interval ($bn)",
          objects={"dataPoint": [{"properties": {"fill": color(NAVY)}, "selector": {"metadata": "_Measures.Effect since Apr 2025 ($bn)"}},
                                 {"properties": {"fill": color("#C9D2DE")}, "selector": {"metadata": "_Measures.Effect Lo 95 ($bn)"}},
                                 {"properties": {"fill": color("#9FB3CC")}, "selector": {"metadata": "_Measures.Effect Hi 95 ($bn)"}}]},
          filters=[filter_in("Tariff Effect", "Flow", ["imports"])], sort=[("m:Effect since Apr 2025 ($bn)", "Ascending")], key="gapbar")
    p.add("lineChart", 648, 472, 616, 240,
          roles={"Category": ["Date.Month"], "Y": [("m:Actual YoY %", "Actual"), ("m:Forecast YoY %", "Forecast"),
                                                   ("m:Forecast YoY Lo 80", "80% low"), ("m:Forecast YoY Hi 80", "80% high")]},
          title="Headline CPI YoY: actual vs SARIMAX + Brent forecast (80% band)",
          objects=series_style({"Actual YoY %": (NAVY, None, 2.5), "Forecast YoY %": (AMBER, None, 2.5),
                                "Forecast YoY Lo 80": (AMBER, "dashed", 1), "Forecast YoY Hi 80": (AMBER, "dashed", 1)}),
          filters=[filter_in("Date", "Year", [2024, 2025, 2026, 2027]), filter_in("Forecasts", "Target", ["headline_cpi"])], key="cpifc")
    pages.append(p)

    # 8 ---------------------------------------------------------------- tooltip page
    p = Page("p08_tooltip", "Country Tooltip", width=320, height=240, ptype="Tooltip", header=False)
    p.binding = {"name": "tipBinding", "type": "Tooltip"}
    p.hidden = True
    p.text_card(8, 8, 304, 44, "Tooltip Country", None, size=14)
    p.kpi(8, 60, 148, 80, "Import Change vs 2024 %", "Imports vs 2024", TEAL)
    p.kpi(164, 60, 148, 80, "Peak Statutory Rate %", "Peak tariff", CORAL)
    p.kpi(8, 148, 148, 80, "Imports ($bn)", "Imports ($bn)", AMBER)
    p.kpi(164, 148, 148, 80, "Share of US Imports %", "Share of US imports", SKY)
    pages.append(p)
    return pages


def build_report(root: Path, theme: dict) -> list[Page]:
    rp = root / "TradeWar.Report"
    d = rp / "definition"
    if d.exists():
        shutil.rmtree(d)
    write_json(rp / ".platform", {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/gitIntegration/platformProperties/2.0.0/schema.json",
        "metadata": {"type": "Report", "displayName": "TradeWar"},
        "config": {"version": "2.0", "logicalId": gid("report")}})
    write_json(rp / "definition.pbir", {"version": "4.0", "datasetReference": {"byPath": {"path": "../TradeWar.SemanticModel"}}})
    write_json(rp / "StaticResources" / "RegisteredResources" / THEME_FILE, theme)
    write_json(d / "version.json", {"$schema": f"{SCH}/versionMetadata/1.0.0/schema.json", "version": "2.0.0"})
    write_json(d / "report.json", {
        "$schema": f"{SCH}/report/{V_REP}/schema.json",
        "themeCollection": {"customTheme": {"name": THEME_FILE, "reportVersionAtImport": {"visual": "1.8.79", "report": "2.0.79", "page": "1.3.79"},
                                            "type": "RegisteredResources"}},
        "resourcePackages": [{"name": "RegisteredResources", "type": "RegisteredResources",
                              "items": [{"name": THEME_FILE, "path": THEME_FILE, "type": "CustomTheme"}]}],
        "settings": {"useStylableVisualContainerHeader": True, "exportDataMode": "AllowSummarized", "defaultDrillFilterOtherVisuals": True,
                     "allowChangeFilterTypes": True, "useEnhancedTooltips": True, "useDefaultAggregateDisplayName": True}})
    pages = build_pages()
    write_json(d / "pages" / "pages.json", {"$schema": f"{SCH}/pagesMetadata/1.0.0/schema.json",
                                            "pageOrder": [p.name for p in pages], "activePageName": pages[0].name})
    for p in pages:
        p.write(d / "pages")
    return pages