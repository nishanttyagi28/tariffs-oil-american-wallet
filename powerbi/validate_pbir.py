"""Validate the PBIR JSON files against Microsoft's published schemas (downloaded once to E:/caches/pbir-schemas)."""
from __future__ import annotations

import json
import sys
import urllib.request
from pathlib import Path

from jsonschema import Draft7Validator
from referencing import Registry, Resource

CACHE = Path("E:/caches/pbir-schemas")
WEB = "https://developer.microsoft.com/json-schemas/"
RAW = "https://raw.githubusercontent.com/microsoft/json-schemas/main/"


def fetch(uri: str):
    rel = uri.split("json-schemas/", 1)[1].split("#")[0]
    p = CACHE / rel
    if not p.exists():
        p.parent.mkdir(parents=True, exist_ok=True)
        with urllib.request.urlopen(RAW + rel, timeout=30) as r:
            p.write_bytes(r.read())
    return Resource.from_contents(json.loads(p.read_text(encoding="utf-8")))


def main(root: Path) -> int:
    reg = Registry(retrieve=fetch)
    bad = 0
    files = [f for f in root.rglob("*.json") if "RegisteredResources" not in f.parts]
    for f in files:
        obj = json.loads(f.read_text(encoding="utf-8"))
        sch = obj.get("$schema")
        if not sch or "fabric/item/report" not in sch:
            continue
        schema = fetch(sch).contents
        v = Draft7Validator(schema, registry=reg)
        errs = sorted(v.iter_errors(obj), key=lambda e: list(e.path))
        for e in errs[:5]:
            bad += 1
            print(f"{f.relative_to(root)}: {'/'.join(map(str, e.path))}: {e.message[:300]}")
    print(f"checked {len(files)} files, {bad} errors")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(Path(__file__).resolve().parent / "TradeWar.Report"))