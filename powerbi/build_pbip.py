"""Build the Power BI project (PBIP: TMDL semantic model + PBIR report) from the exported Parquet schema.

    python powerbi/export_for_pbi.py     # warehouse -> powerbi/data/*.parquet
    python powerbi/build_pbip.py         # -> powerbi/TradeWar.pbip, TradeWar.SemanticModel/, TradeWar.Report/

The DataRoot M parameter defaults to this repo's powerbi/data folder; change it in Power BI
(Transform data > Edit parameters) if the repo lives elsewhere.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from pbi_common import write_json  # noqa: E402
from pbi_measures import M  # noqa: E402
from pbi_model import build_model  # noqa: E402
from pbi_report import build_report  # noqa: E402
from pbi_theme import THEME  # noqa: E402


def check_fields(pages, cols: dict[str, set[str]]) -> list[str]:
    mnames = {n for n, *_ in M}
    errs = []

    def walk(o, where):
        if isinstance(o, dict):
            for k in ("Measure", "Column"):
                if k in o and isinstance(o[k], dict) and "Property" in o[k]:
                    ent = o[k]["Expression"]["SourceRef"].get("Entity")
                    prop = o[k]["Property"]
                    if ent is None:
                        continue
                    if k == "Measure" and prop not in mnames:
                        errs.append(f"{where}: unknown measure {prop}")
                    if k == "Column" and (ent not in cols or prop not in cols[ent]):
                        errs.append(f"{where}: unknown column {ent}.{prop}")
            for v in o.values():
                walk(v, where)
        elif isinstance(o, list):
            for v in o:
                walk(v, where)

    for p in pages:
        for v in p.visuals:
            walk(v, f"{p.name}/{v['visual']['visualType']}")
        walk(p.filters, f"{p.name}/page-filters")
        walk(p.binding or {}, f"{p.name}/binding")
    return errs


def main() -> None:
    data_root = str(ROOT / "data")
    cols = build_model(ROOT, data_root)
    pages = build_report(ROOT, THEME)
    write_json(ROOT / "TradeWar.pbip", {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/pbip/pbipProperties/1.0.0/schema.json",
        "version": "1.0", "artifacts": [{"report": {"path": "TradeWar.Report"}}], "settings": {"enableAutoRecovery": True}})
    errs = check_fields(pages, cols)
    if errs:
        raise SystemExit("\n".join(errs))
    nvis = sum(len(p.visuals) for p in pages)
    print(f"model: {len(cols)} tables, {len(M)} measures | report: {len(pages)} pages, {nvis} visuals")


if __name__ == "__main__":
    main()