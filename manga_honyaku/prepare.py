"""Stage `prepare`: open the working file for a page.

Rewrites build/<id>.detector.json as pages/<id>.agent.json — the same regions, with a
slot for everything the agent is about to work out. From here on the working
file is the agent's: it drops the regions it will not touch, adds the ones the
detector never saw, and accumulates the source and the translation.

This stage is mechanical on purpose. Carrying a chapter's regions across without
a judgement being made about any of them is the part worth automating; deciding
which of them is speech is the part that is not.

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
from itertools import groupby
from pathlib import Path

from PIL import Image

from manga_honyaku.ocr import load_reader, read
from manga_honyaku.page import Series
from manga_honyaku.render import (
    FONT,
    K,
    LINE_SPACING,
    TYPICAL,
    room_for,
    settings,
    widths,
)

# Left present and empty rather than absent, so that a fresh working file shows
# what it is waiting for: what the text says, and what it is for. `clean` and
# `render` read absent and null alike.
SLOTS = {"source": None, "role": None}

# Every way this book writes a pause.
PAUSE = ".。・…‥·˙⋯｡︙"


def cells(source: str) -> int:
    """How many cells of the grid the source fills.

    One character to a cell, except that a pause is often recorded twice over,
    once in each script — `・・・...` where the page has three dots. Counting both
    makes the region measure about a sixth smaller than it is, so a run of pause
    marks counts as its longest unbroken stretch of one mark.
    """
    total = 0
    for pause, run in groupby("".join(source.split()), key=lambda c: c in PAUSE):
        marks = list(run)
        total += (
            max(len(list(same)) for _, same in groupby(marks)) if pause else len(marks)
        )
    return total


def lettered_at(box: list[float], source: str) -> float | None:
    """How large this region has to be lettered, in the page's own pixels.

    `sqrt(box area / n)` — Japanese sets on a square grid, so n characters
    filling a box of area A were set at about sqrt(A / n) whichever way the text
    ran.

    The box is measured rather than the ink it contains. The box is loose — its
    padding runs from 4% to six times the ink — but the padding varies with the
    region's shape and not with its scale, so it stays steady where an ink extent
    swings with whichever glyphs a region happens to hold. It also carries some
    of the space available into the answer, which is what makes horizontal Thai
    fill a box drawn for vertical Japanese. The `thai-manga-lettering` skill has
    the measurements behind both.

    A region holding only a pause is excluded: one character in a box sized for a
    beat of silence measures as enormous lettering, and the dots were drawn at
    ordinary size.
    """
    if not any(unicodedata.category(c).startswith(("L", "N")) for c in source):
        return None
    characters = cells(source)
    if not characters:
        return None
    x1, y1, x2, y2 = box
    return math.sqrt((x2 - x1) * (y2 - y1) / characters)


def tag(entry: dict, size: float | None, style: dict) -> None:
    """The two fields the geometry decides: what size, and how much of it.

    `size` is a number in the page's own pixels and nothing here interprets it.
    What carries meaning is the ratio between the regions on a page, and one
    multiplier preserves every one of them exactly.
    """
    if size is not None:
        entry["size"] = round(size)
    if not entry.get("bubble"):
        # Free-floating text is lettered to its own extent rather than to a
        # size, so there is no budget to state.
        entry.pop("room", None)
        return
    at = max(1, round(style.get("k", K) * entry["size"]))
    room = room_for(
        entry["box"], at, style.get("line_spacing", LINE_SPACING), style["one"]
    )
    # A box too small to hold one line at its own size has no budget to state,
    # and a stated zero reads as "write nothing".
    if room:
        entry["room"] = room
    else:
        entry.pop("room", None)


def tag_page(entries: list[dict], height: int, style: dict) -> None:
    """Size every region on a page, then the budget that follows from it.

    A page at a time because of the regions that cannot be measured — a burst
    bubble reading `!?`, a box holding only a pause. They still have to be
    lettered, and the honest guess is what the rest of this page was set at
    rather than a constant carried in from another book. A size already on such
    a region is kept: it is the only judgement that region has ever had.
    """
    measured = [lettered_at(e["box"], e.get("source") or "") for e in entries]
    known = sorted(m for m in measured if m)
    usual = known[len(known) // 2] if known else TYPICAL * height
    for entry, size in zip(entries, measured):
        if size is None:
            # Only a number is a measurement; anything else in the slot is not
            # one, and the page's own median is the better guess.
            kept = entry.get("size")
            size = kept if isinstance(kept, (int, float)) else usual
        tag(entry, size, style)


def reading(
    detected: dict, image: Image.Image | None, reader, values: dict | None = None
) -> dict:
    values = values or {}
    style = {**values, "one": widths(values.get("font") or FONT)[0]}

    regions = []
    for region in detected["regions"]:
        entry = {**region, **SLOTS}
        if reader is not None:
            entry["source"] = read(image, region["box"], reader)
        regions.append(entry)
    tag_page(regions, detected["img_height"], style)

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
    ap.add_argument("series", type=Path, help="a work's directory under series/")
    ap.add_argument("pages", nargs="*", help="page ids; a directory; none for all")
    ap.add_argument(
        "--force",
        action="store_true",
        help="rewrite working files that already exist, discarding the roles, "
        "reading order, speakers and translations in them",
    )
    ap.add_argument(
        "--retag",
        action="store_true",
        help="only re-measure the size tags and the room that follows from "
        "them, leaving everything else in the working files alone",
    )
    ap.add_argument(
        "--no-ocr",
        action="store_true",
        help="leave every source empty for the agent to fill by reading the page",
    )
    args = ap.parse_args()

    work = Series(args.series)
    values = settings(args.series)

    # Changing `k` after pages have been read is ordinary — the first one is
    # guessed before there is a rendered page to judge it on. Re-running prepare
    # would answer it by discarding the translation, so retagging is its own
    # switch: it reads what the working files already say and writes back the
    # two fields the geometry decides.
    if args.retag:
        style = {**values, "one": widths(values.get("font") or FONT)[0]}
        for page in work.ids(args.pages):
            out = work.agent(page)
            data = json.loads(out.read_text())
            before = [(r.get("size"), r.get("room")) for r in data["regions"]]
            tag_page(data["regions"], data["img_height"], style)
            after = [(r.get("size"), r.get("room")) for r in data["regions"]]
            out.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
            moved = sum(a != b for a, b in zip(before, after))
            print(f"{page}  {moved} of {len(data['regions'])} retagged")
        return

    reader = None if args.no_ocr else load_reader()

    for page in work.ids(args.pages, prepared=False):
        out = work.agent(page)
        if out.exists() and not args.force:
            print(f"{page}  exists, skipping")
            continue

        detected = json.loads(work.derived(page, "detector.json").read_text())
        scan = None if reader is None else Image.open(work.scan(page)).convert("RGB")
        data = reading(detected, scan, reader, values)
        out.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
        print(f"{page}  {out}  {len(data['regions'])} regions")


if __name__ == "__main__":
    main()
