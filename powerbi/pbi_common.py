"""Shared helpers for the PBIP builder: TMDL writer (semantic model) and PBIR JSON helpers (report)."""
from __future__ import annotations

import json
import re
import uuid
from pathlib import Path

NS = uuid.UUID("6f1c2b8e-3a51-4c1e-9a8e-1d2f3a4b5c6d")


def gid(*parts: str) -> str:
    """Deterministic GUID so rebuilds give stable diffs."""
    return str(uuid.uuid5(NS, "|".join(parts)))


def hid(*parts: str) -> str:
    return gid(*parts).replace("-", "")[:20]


def q(name: str) -> str:
    """Quote a TMDL object name when needed."""
    return name if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name) else "'" + name.replace("'", "''") + "'"


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def write_json(path: Path, obj) -> None:
    write(path, json.dumps(obj, indent=2, ensure_ascii=False) + "\n")


# ------------------------------------------------------------------ PBIR expression helpers
def lit(v):
    if isinstance(v, bool):
        s = "true" if v else "false"
    elif isinstance(v, int):
        s = f"{v}L"
    elif isinstance(v, float):
        s = f"{v}D"
    else:
        s = "'" + str(v).replace("'", "''") + "'"
    return {"expr": {"Literal": {"Value": s}}}


def num(v: float):
    return {"expr": {"Literal": {"Value": f"{v}D"}}}


def color(hex_: str):
    return {"solid": {"color": lit(hex_)}}


def meas(name: str, entity: str = "_Measures"):
    return {"Measure": {"Expression": {"SourceRef": {"Entity": entity}}, "Property": name}}


def col(entity: str, prop: str):
    return {"Column": {"Expression": {"SourceRef": {"Entity": entity}}, "Property": prop}}


def ref_of(field) -> str:
    k = "Measure" if "Measure" in field else "Column"
    return f'{field[k]["Expression"]["SourceRef"]["Entity"]}.{field[k]["Property"]}'


def proj(field, display: str | None = None):
    p = {"field": field, "queryRef": ref_of(field), "nativeQueryRef": ref_of(field).split(".", 1)[1]}
    if display:
        p["displayName"] = display
    if "Column" in field:
        p["active"] = True
    return p


def F(spec: str):
    """'Table.Column' -> column field, 'm:Name' -> measure field."""
    if spec.startswith("m:"):
        return meas(spec[2:])
    t, c = spec.split(".", 1)
    return col(t, c)


def literal_value(v) -> str:
    return lit(v)["expr"]["Literal"]["Value"]


def filter_in(entity: str, prop: str, values: list, name: str | None = None, how: str | None = None):
    alias = entity[0].lower()
    f = {
        "name": name or hid("flt", entity, prop, json.dumps(values)),
        "field": col(entity, prop),
        "type": "Categorical",
        "filter": {
            "Version": 2,
            "From": [{"Name": alias, "Entity": entity, "Type": 0}],
            "Where": [{"Condition": {"In": {
                "Expressions": [{"Column": {"Expression": {"SourceRef": {"Source": alias}}, "Property": prop}}],
                "Values": [[{"Literal": {"Value": literal_value(v)}}] for v in values]}}}],
        },
    }
    if how:
        f["howCreated"] = how
    return f