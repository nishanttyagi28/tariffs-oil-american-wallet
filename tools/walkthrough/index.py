"""Encode the raw walkthrough recordings and write docs/walkthrough/INDEX.md (part + timestamp -> file + note).

Usage: python tools/walkthrough/index.py [--log .scratch/wt_log_12345.json ...] [--no-encode]
When several logs are given, a later log replaces every part it contains (used after re-recording single parts).
"""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "docs" / "walkthrough"
PARTS = {
    1: (
        "part1_overview_config_ingest_staging.mp4",
        "Overview, config & CI, ingest/*, dbt project, macros, staging and intermediate models",
    ),
    2: ("part2_dbt_marts_tests_seeds.mp4", "dbt marts (core + Power BI), ml sources, dbt tests, seeds"),
    3: ("part3_sql_analyses_ml.mp4", "35 SQL analyses + runner, the ML layer"),
    4: (
        "part4_powerbi_generator_semantic_model.mp4",
        "Power BI export/generator scripts, GUI helper scripts, PBIP and the TMDL semantic model",
    ),
    5: ("part5_report_tests_tools_docs.mp4", "PBIR report definition, Python tests, tools, docs"),
}


def probe(path: Path) -> float:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    return float(out.strip())


def mmss(t: float) -> str:
    return f"{int(t // 60):02d}:{int(t % 60):02d}"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--log", nargs="+", default=[str(ROOT / ".scratch" / "wt_log_12345.json")])
    ap.add_argument("--no-encode", action="store_true")
    a = ap.parse_args()
    by_part: dict[int, list] = {}
    for lp in a.log:
        entries = json.loads(Path(lp).read_text(encoding="utf-8-sig"))
        for part in {e["part"] for e in entries}:
            by_part[part] = [e for e in entries if e["part"] == part]
    log = [e for part in sorted(by_part) for e in by_part[part]]
    OUT.mkdir(parents=True, exist_ok=True)
    rows = []
    for part, (name, title) in PARTS.items():
        raw = ROOT / ".scratch" / f"wt_part{part}_raw.mp4"
        dst = OUT / name
        if not a.no_encode:
            subprocess.run(
                [
                    "ffmpeg",
                    "-v",
                    "error",
                    "-y",
                    "-i",
                    str(raw),
                    "-c:v",
                    "libx264",
                    "-preset",
                    "medium",
                    "-crf",
                    "26",
                    "-pix_fmt",
                    "yuv420p",
                    "-r",
                    "15",
                    "-movflags",
                    "+faststart",
                    "-an",
                    str(dst),
                ],
                check=True,
            )
        items = [e for e in log if e["part"] == part]
        rows.append((part, name, title, probe(dst), dst.stat().st_size / 1e6, items))
    md = [
        "# VS Code walkthrough: every project file",
        "",
        "Screen recordings of VS Code opening every source and config file in the repo, in pipeline order",
        "(data blobs, the warehouse, screenshots, per-visual PBIR JSON and ML run logs are skipped).",
        "Use the timestamps below to write the voice-over. Recorded at 1600x856, 15 fps, H.264, no audio.",
        "",
        "| Part | Video | Duration | Size | Files | What it covers |",
        "|---|---|---|---|---|---|",
    ]
    for part, name, title, dur, size, items in rows:
        md.append(f"| {part} | [{name}]({name}) | {mmss(dur)} | {size:.1f} MB | {len(items)} | {title} |")
    for part, name, title, dur, _size, items in rows:
        md += ["", f"## Part {part}: {title}", "", f"Video: [{name}]({name}) ({mmss(dur)})", "", "| Time | File | Note |", "|---|---|---|"]
        for e in items:
            md.append(f"| {mmss(e['t'])} | `{e['path']}` | {e['note'].replace('|', '/')} |")
    md += [
        "",
        "Regenerate: `python tools/walkthrough/plan.py`, then `powershell -File tools/walkthrough/record.ps1`, "
        "then `python tools/walkthrough/index.py` (writes the MP4s and this file).",
        "",
    ]
    (OUT / "INDEX.md").write_text("\n".join(md), encoding="utf-8", newline="\n")
    for part, name, _t, dur, size, items in rows:
        print(f"part {part}: {name} {mmss(dur)} {size:.1f} MB {len(items)} files")


if __name__ == "__main__":
    main()
