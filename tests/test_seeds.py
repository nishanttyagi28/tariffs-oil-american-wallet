"""Seeds are the hand-verified event timeline: they must parse and carry sources."""
import csv
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SEEDS = ROOT / "seeds"


def rows(name):
    with open(SEEDS / name, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def test_tariff_events_have_dates_and_sources():
    r = rows("tariff_events.csv")
    assert len(r) >= 15
    for x in r:
        date.fromisoformat(x["event_date"])
        assert x["source_url"].startswith("http"), x["event_id"]


def test_war_events_start_on_28_feb_2026():
    r = rows("war_events.csv")
    starts = [x for x in r if x["category"] == "war_start"]
    assert len(starts) == 1 and starts[0]["event_date"] == "2026-02-28"
    assert all(x["source_url"].startswith("http") for x in r)


def test_event_phases_are_contiguous():
    r = rows("event_phases.csv")
    for kind in {x["phase_type"] for x in r}:
        ph = sorted((x for x in r if x["phase_type"] == kind), key=lambda x: int(x["phase_order"]))
        for a, b in zip(ph, ph[1:]):
            gap = (date.fromisoformat(b["start_date"]) - date.fromisoformat(a["end_date"])).days
            assert gap == 1, (kind, a["phase_code"], b["phase_code"])


def test_no_bom_in_seeds():
    for p in SEEDS.glob("*.csv"):
        assert not p.read_bytes().startswith(b"\xef\xbb\xbf"), p.name
