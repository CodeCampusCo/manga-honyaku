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
    warn,
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


def overlapping(regions: list[dict], threshold: float = 0.85) -> list[tuple]:
    """Region pairs standing on the same lettering, largest coverage first.

    `detect` drops a duplicate only when both boxes came back under the same
    class, so one piece of text found once as bubble text and once as free text
    survives as two regions. It happens on every chapter, and reading a box
    column by eye does not find them all: on the third chapter here a translator
    doing exactly that found 6 of the 14 pairs, which is the kind of reading a
    machine should be doing instead.

    **A pair is a decision, not a defect.** One of the two is the region to
    letter and the other has to be declined, and which is which depends on what
    the text is: the free one for a sign or a spine, the bubble one where the
    balloon's outline was found and `clean` can follow it. So this reports and
    does not choose. Nothing downstream reports it at all — two regions both set
    to `ok` are erased and lettered on top of each other.

    Coverage is measured against the smaller box rather than the union, because
    the shape that matters is containment: a box drawn around a whole phrase and
    a second box around one of its columns overlap very little as a fraction of
    the pair, and completely as a fraction of the smaller.
    """
    found = []
    for i, a in enumerate(regions):
        for b in regions[i + 1 :]:
            ax1, ay1, ax2, ay2 = a["box"]
            bx1, by1, bx2, by2 = b["box"]
            wide = min(ax2, bx2) - max(ax1, bx1)
            tall = min(ay2, by2) - max(ay1, by1)
            if wide <= 0 or tall <= 0:
                continue
            smaller = min((ax2 - ax1) * (ay2 - ay1), (bx2 - bx1) * (by2 - by1))
            cover = wide * tall / smaller
            if cover > threshold:
                found.append((a, b, cover))
    return sorted(found, key=lambda pair: -pair[2])


def uncovered(regions: list[dict]) -> list[tuple]:
    """Declined regions with a lettered one inside them, and how much of their
    height that lettered part actually covers.

    The shape it is looking for reached a rendered page: a drawn phrase boxed
    whole and boxed again in part, the whole declined as "partial" and the part
    lettered, so the rest of the phrase stands in Japanese under the Thai. On
    `04/09` the reason recorded for the declined box says the small one is the
    whole phrase; the boxes say the opposite, and 「ファンじゃん」 is still on the
    page.

    **It reports and does not judge, because no threshold separates the two
    cases.** Measured over four chapters, the same arrangement occurs seven
    times legitimately: a box drawn round a logo that happens to contain the
    chapter title, a caption whose remainder is Latin and needs nothing, a
    phrase whose parts are *all* lettered so the whole is covered. Their
    coverage runs 17% to 100% and the real defects run 29% and 46% — the ranges
    overlap, and what separates them is the reason, which is prose. So this is a
    worklist for `regions --todo`, not a check for `audit`, whose standard is
    that everything it prints is work.
    """
    out = []
    for big in regions:
        if big.get("status") != "declined":
            continue
        inside = [
            r for r in regions
            if r is not big and r.get("status") == "ok"
            and big["box"][0] - 1 <= r["box"][0] and r["box"][2] <= big["box"][2] + 1
            and big["box"][1] - 1 <= r["box"][1] and r["box"][3] <= big["box"][3] + 1
        ]
        if not inside:
            continue
        top, bottom = int(big["box"][1]), int(big["box"][3])
        covered = sum(
            any(r["box"][1] <= y <= r["box"][3] for r in inside)
            for y in range(top, bottom)
        )
        out.append((big, inside, covered / max(1, bottom - top)))
    return sorted(out, key=lambda row: row[2])


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
        for a, b, cover in overlapping(data["regions"]):
            warn(
                f"{page} {a['id']} and {b['id']}: one covers {cover:.0%} of the "
                f"other. Letter one and decline the other."
            )


if __name__ == "__main__":
    main()
