"""Stage `prepare`: open the working file for a page.

Rewrites work/<page>.detector.json as work/<page>.agent.json — the same regions, with a
slot for everything the agent is about to work out. From here on the working
file is the agent's: it drops the regions it will not touch, adds the ones the
detector never saw, and accumulates the source and the translation.

This stage is mechanical on purpose. It carries 212 regions across a chapter
without a judgement being made about any of them, which is the part worth
automating; deciding which of them is speech is the part that is not.

OCR runs here rather than as a stage of its own. Its output is a `source` field
in the working file, and a stage that filled that field afterwards would be
writing into a file the agent had already edited — the failure the split between
the two files exists to prevent. Running it at creation means it can only ever
write into slots that are still empty.

Nothing here overwrites an existing working file. Redoing a page means redoing
the reading, so it has to be asked for.
"""

from __future__ import annotations

import argparse
import json
import math
import unicodedata
from pathlib import Path

from PIL import Image

from manga_honyaku.ocr import load_reader, read
from manga_honyaku.page import agent_path, detector_path
from manga_honyaku.render import settings

# Left present and empty rather than absent, so that a fresh working file shows
# what it is waiting for: what the text says, and what it is for. `clean` and
# `render` read absent and null alike.
SLOTS = {"source": None, "role": None}

# Fallback bands, for a series with no stylesheet. The real ones are in
# series/lettering.json, because where one size ends and the next begins is a
# fact about the artist's hand and not about this program.
BANDS = {"quiet": 35, "normal": 47, "loud": 60, "shout": 88}
LARGEST = "display"
PAGE_HEIGHT = 1600


def lettered_at(box: list[float], source: str) -> float | None:
    """The size the Japanese was set at, from the box and the character count.

    Japanese sets on a square grid, so a box of area A holding n characters was
    lettered at about sqrt(A / n) whichever way the text ran.

    A region holding only a pause is excluded: one character in a box sized for a
    beat of silence measures as enormous lettering, and the dots were drawn at
    ordinary size.
    """
    if not any(unicodedata.category(c).startswith(("L", "N")) for c in source):
        return None
    characters = len([c for c in source if not c.isspace()])
    if not characters:
        return None
    x1, y1, x2, y2 = box
    return math.sqrt((x2 - x1) * (y2 - y1) / characters)


def size_of(box: list[float], source: str, bands: dict, scale: float) -> str:
    """Which of the series' sizes this region's Japanese was lettered at.

    Measured once, here, and written into the working file: the number is a
    property of the artwork and it never changes again, so deriving it at every
    render is the same work for the same answer. What the name is worth in Thai
    is the stylesheet's business, so a size can be changed by eye afterwards
    without anything being measured a second time.
    """
    measured = lettered_at(box, source)
    if measured is None:
        return "normal"
    for name, ceiling in sorted(bands.items(), key=lambda item: item[1]):
        if measured < ceiling * scale:
            return name
    return LARGEST


def reading(
    detected: dict, image: Image.Image | None, reader, values: dict | None = None
) -> dict:
    values = values or {}
    bands = values.get("bands") or BANDS
    # The bands are quoted for a page of a stated height. A volume scanned larger
    # measures larger throughout, and would otherwise land every bubble in the
    # loudest band it has.
    scale = detected["img_height"] / values.get("page_height", PAGE_HEIGHT)

    regions = []
    for region in detected["regions"]:
        entry = {**region, **SLOTS}
        if reader is not None:
            entry["source"] = read(image, region["box"], reader)
        entry["size"] = size_of(region["box"], entry["source"] or "", bands, scale)
        regions.append(entry)

    return {
        "version": detected["version"],
        "page": detected["page"],
        "img_width": detected["img_width"],
        "img_height": detected["img_height"],
        "detector": detected["detector"],
        "regions": regions,
        "questions": [],
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("pages", nargs="+", type=Path)
    ap.add_argument("--work", type=Path, default=Path("work"))
    ap.add_argument("--series", type=Path, default=Path("series"))
    ap.add_argument(
        "--force",
        action="store_true",
        help="rewrite working files that already exist, discarding the roles, "
        "reading order, speakers and translations in them",
    )
    ap.add_argument(
        "--no-ocr",
        action="store_true",
        help="leave every source empty for the agent to fill by reading the page",
    )
    args = ap.parse_args()

    reader = None if args.no_ocr else load_reader()
    values = settings(args.series)

    for page in args.pages:
        out = agent_path(args.work, page.stem)
        if out.exists() and not args.force:
            print(f"{page.name}  {out.name} exists, skipping")
            continue

        detected = json.loads(detector_path(args.work, page.stem).read_text())
        image = None if reader is None else Image.open(page).convert("RGB")
        data = reading(detected, image, reader, values)
        out.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
        print(f"{page.name}  {out.name}  {len(data['regions'])} regions")


if __name__ == "__main__":
    main()
