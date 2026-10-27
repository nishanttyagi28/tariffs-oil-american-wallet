"""Write the TMDL semantic model (powerbi/TradeWar.SemanticModel) from powerbi/data/_schema.json + pbi_measures."""
from __future__ import annotations

import json
import re
from pathlib import Path

from pbi_common import gid, q, write, write_json
from pbi_measures import M

TYPE = {"VARCHAR": "string", "DOUBLE": "double", "FLOAT": "double", "BIGINT": "int64", "INTEGER": "int64",
        "HUGEINT": "int64", "SMALLINT": "int64", "DATE": "dateTime", "TIMESTAMP": "dateTime", "BOOLEAN": "boolean"}

SORT_BY = {("Date", "Month Label"): "Month", ("Date", "Trade Phase"): "Trade Phase Order", ("Date", "War Phase"): "War Phase Order",
           ("Partner", "Partner"): "Partner Order", ("Trade Metric", "Metric"): "Metric Order",
           ("Oil Shock", "War Phase"): "War Phase Order"}
DATA_CATEGORY = {("Country", "Map Name"): "Country", ("Country", "Latitude"): "Latitude", ("Country", "Longitude"): "Longitude",
                 ("Country Before After", "Latitude"): "Latitude", ("Country Before After", "Longitude"): "Longitude",
                 ("Chokepoint", "Latitude"): "Latitude", ("Chokepoint", "Longitude"): "Longitude",
                 ("Events", "Source URL"): "WebUrl"}

# (from table, from column) -> (to table, to column)   many-to-one, single direction
RELS = [
    *[(t, "Month", "Date", "Date") for t in ["Trade", "Tariff Rate", "Customs", "CPI", "Macro", "Household", "Trade Diversion",
                                            "Counterfactual", "Forecasts"]],
    *[(t, "Date", "Date", "Date") for t in ["Market", "Oil", "Chokepoint Daily", "Oil Shock", "Vol Regimes"]],
    ("Events", "Event Date", "Date", "Date"),
    ("Trade", "ISO3", "Country", "ISO3"), ("Tariff Rate", "ISO3", "Country", "ISO3"), ("Country Before After", "ISO3", "Country", "ISO3"),
    ("CPI", "Series ID", "CPI Category", "Series ID"),
    ("Market", "Symbol", "Instrument", "Symbol"), ("Vol Regimes", "Symbol", "Instrument", "Symbol"),
    ("Event Study", "Symbol", "Instrument", "Symbol"),
    ("Chokepoint Daily", "Chokepoint ID", "Chokepoint", "Chokepoint ID"),
    ("Counterfactual", "Partner Code", "Partner", "Partner Code"), ("Tariff Effect", "Partner Code", "Partner", "Partner Code"),
]
HIDDEN_TABLES: set[str] = set()
# calculated columns: table -> [(name, dataType, DAX)]
CALC_COLS: dict[str, list[tuple[str, str, str]]] = {
    "Instrument": [("Short Name", "string",
                    'SWITCH ( Instrument[Symbol], "^GSPC", "S&P 500", "^NSEI", "Nifty 50", "^STOXX50E", "Euro Stoxx 50", '
                    '"^N225", "Nikkei 225", "000001.SS", "Shanghai", "BZ=F", "Brent", "CL=F", "WTI", "GC=F", "Gold", '
                    '"^VIX", "VIX", "^BSESN", "Sensex", "^GDAXI", "DAX", Instrument[Instrument] )')],
}


def col_format(table: str, name: str, dtype: str) -> str | None:
    if dtype == "dateTime":
        return "mmm yyyy" if name == "Month" or name.endswith("Month") else "yyyy-mm-dd"
    if dtype != "double":
        return None
    if name.endswith("%") or name.startswith(("Share of", "Import Share", "Prob ")) or name in ("Ret", "Log Ret", "Brent Ret"):
        return "0.0%"
    if "$M" in name or name.startswith(("CF ", "Effect Lo", "Effect Hi")):
        return "#,0"
    if "USD" in name:
        return "#,0.00"
    return "#,0.00"


def build_model(root: Path, data_root: str) -> dict:
    schema = json.loads((root / "data" / "_schema.json").read_text(encoding="utf-8"))
    sm = root / "TradeWar.SemanticModel"
    d = sm / "definition"
    write_json(sm / ".platform", {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/gitIntegration/platformProperties/2.0.0/schema.json",
        "metadata": {"type": "SemanticModel", "displayName": "TradeWar"},
        "config": {"version": "2.0", "logicalId": gid("semanticmodel")}})
    write_json(sm / "definition.pbism", {"version": "4.2", "settings": {}})
    write(d / "database.tmdl", "database\n\tcompatibilityLevel: 1601\n\n")

    tables = list(schema.keys()) + ["_Measures"]
    order = ", ".join(json.dumps(t) for t in ["DataRoot"] + tables)
    model = ["model Model", "\tculture: en-US", "\tdefaultPowerBIDataSourceVersion: powerBI_V3", "\tsourceQueryCulture: en-US",
             "\tdataAccessOptions", "\t\tlegacyRedirects", "\t\treturnErrorValuesAsNull", "",
             f"annotation PBI_QueryOrder = [{order}]", "", "annotation __PBI_TimeIntelligenceEnabled = 0", "",
             "annotation PBI_ProTooling = [\"DevMode\"]", ""]
    model += [f"ref table {q(t)}" for t in tables]
    write(d / "model.tmdl", "\n".join(model) + "\n")

    write(d / "expressions.tmdl",
          f"expression DataRoot = \"{data_root}\" meta [IsParameterQuery=true, Type=\"Text\", IsParameterQueryRequired=true]\n"
          f"\tlineageTag: {gid('expr', 'DataRoot')}\n\n\tannotation PBI_ResultType = Text\n\n\tannotation PBI_NavigationStepName = Navigation\n\n")

    cols: dict[str, set[str]] = {}
    for t, columns in schema.items():
        cols[t] = {c["name"] for c in columns}
        L = [f"table {q(t)}", f"\tlineageTag: {gid('table', t)}"]
        if t == "Date":
            L.append("\tdataCategory: Time")
        L.append("")
        for c in columns:
            dt = TYPE.get(c["type"].split("(")[0].upper())
            assert dt, f"unknown type {c['type']} for {t}.{c['name']}"
            L.append(f"\tcolumn {q(c['name'])}")
            L.append(f"\t\tdataType: {dt}")
            if t == "Date" and c["name"] == "Date":
                L.append("\t\tisKey")
            fmt = col_format(t, c["name"], dt)
            if fmt:
                L.append(f"\t\tformatString: {fmt}")
            if (t, c["name"]) in DATA_CATEGORY:
                L.append(f"\t\tdataCategory: {DATA_CATEGORY[(t, c['name'])]}")
            L.append(f"\t\tlineageTag: {gid('col', t, c['name'])}")
            L.append("\t\tsummarizeBy: none")
            L.append(f"\t\tsourceColumn: {c['name']}")
            if (t, c["name"]) in SORT_BY:
                L.append(f"\t\tsortByColumn: {q(SORT_BY[(t, c['name'])])}")
            L += ["", "\t\tannotation SummarizationSetBy = User", ""]
        for cn, ct, cx in CALC_COLS.get(t, []):
            cols[t].add(cn)
            L += [f"\tcolumn {q(cn)} = {cx}", f"\t\tdataType: {ct}", f"\t\tlineageTag: {gid('col', t, cn)}",
                  "\t\tsummarizeBy: none", "", "\t\tannotation SummarizationSetBy = Automatic", ""]
        L += [f"\tpartition {q(t)} = m", "\t\tmode: import", "\t\tsource =", "\t\t\t\tlet",
              f"\t\t\t\t    Source = Parquet.Document(File.Contents(DataRoot & \"\\{t}.parquet\"))",
              "\t\t\t\tin", "\t\t\t\t    Source", "", "\tannotation PBI_ResultType = Table", ""]
        write(d / "tables" / f"{t}.tmdl", "\n".join(L) + "\n")

    # measures table
    L = ["table _Measures", f"\tlineageTag: {gid('table', '_Measures')}", ""]
    names = [n for n, *_ in M]
    dup = {n for n in names if names.count(n) > 1}
    assert not dup, f"duplicate measures {dup}"
    for name, folder, fmt, expr in M:
        lines = expr.split("\n")
        if len(lines) == 1:
            L.append(f"\tmeasure {q(name)} = {lines[0]}")
        else:
            L.append(f"\tmeasure {q(name)} =")
            L += [f"\t\t\t{x}" for x in lines]
        if fmt:
            L.append(f"\t\tformatString: {fmt}")
        L.append(f"\t\tdisplayFolder: {folder}")
        L.append(f"\t\tlineageTag: {gid('measure', name)}")
        L.append("")
    L += ["\tcolumn Dummy", "\t\tdataType: string", "\t\tisHidden", f"\t\tlineageTag: {gid('col', '_Measures', 'Dummy')}",
          "\t\tsummarizeBy: none", "\t\tsourceColumn: Dummy", "", "\t\tannotation SummarizationSetBy = Automatic", "",
          "\tpartition _Measures = m", "\t\tmode: import", "\t\tsource =", "\t\t\t\tlet",
          "\t\t\t\t    Source = #table(type table [Dummy = text], {})", "\t\t\t\tin", "\t\t\t\t    Source", "",
          "\tannotation PBI_ResultType = Table", ""]
    write(d / "tables" / "_Measures.tmdl", "\n".join(L) + "\n")

    R = []
    for ft, fc, tt, tc in RELS:
        assert fc in cols[ft] and tc in cols[tt], (ft, fc, tt, tc)
        R += [f"relationship {gid('rel', ft, fc, tt, tc)}", f"\tfromColumn: {q(ft)}.{q(fc)}", f"\ttoColumn: {q(tt)}.{q(tc)}", ""]
    write(d / "relationships.tmdl", "\n".join(R) + "\n")

    validate_measures(cols)
    return cols


def validate_measures(cols: dict[str, set[str]]) -> None:
    mnames = {n for n, *_ in M}
    errors = []
    for name, _, _, expr in M:
        e = re.sub(r'"[^"]*"', '""', expr)  # drop string literals
        for tq, tb, c in re.findall(r"(?:'([^']+)'|\b([A-Za-z_][A-Za-z0-9_ ]*?))\[([^\]]+)\]", e):
            t = (tq or tb).strip()
            if t not in cols:
                errors.append(f"{name}: unknown table {t!r}")
            elif c not in cols[t]:
                errors.append(f"{name}: unknown column {t}[{c}]")
        for mref in re.findall(r"(?<![\w'\]])\[([^\]]+)\]", e):
            if mref not in mnames:
                errors.append(f"{name}: unknown measure [{mref}]")
    assert not errors, "\n".join(errors)
