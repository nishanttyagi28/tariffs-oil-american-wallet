"""Run every ingest module in sequence (one process, low memory). Usage: python -m ingest.run_all [module ...]"""
import importlib
import logging
import sys
import time
import traceback

MODULES = ["naturalearth", "crosswalk", "census_country", "census_hs", "eurostat", "statcan", "worldbank",
           "bls", "fred", "treasury", "eia", "yahoo", "portwatch", "gscpi", "comtrade"]


def main(argv=None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    mods = (argv or sys.argv[1:]) or MODULES
    failures = []
    for name in mods:
        t = time.time()
        try:
            res = importlib.import_module(f"ingest.{name}").run()
            print(f"[ok] {name:15s} rows={res.get('rows')} {res.get('min_date','')}..{res.get('max_date','')} "
                  f"{res.get('status')} {res.get('note','')} ({time.time()-t:.0f}s)")
        except Exception as e:
            failures.append(name)
            print(f"[FAIL] {name}: {e}")
            traceback.print_exc()
    print("failures:", failures or "none")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
