"""Crop raw 1600x900 Power BI Desktop captures to the report canvas + page tabs (drops title bar, ribbon, side rail,
collapsed panes and the Windows taskbar). Idempotent: already-cropped files are skipped.

    python powerbi/tools/crop_screenshots.py docs/screenshots
The same box (x=48..1488, y=168..836 at 1600x900) is used to crop the demo video.
"""
from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image

BOX = (48, 168, 1488, 836)


def main(folder: str) -> None:
    for f in sorted(Path(folder).glob("*.png")):
        im = Image.open(f)
        if im.size != (1600, 900):
            print(f"skip {f.name} {im.size}")
            continue
        im.crop(BOX).save(f, optimize=True)
        print(f"cropped {f.name}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "docs/screenshots")
