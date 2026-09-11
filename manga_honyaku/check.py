"""Stage `check`: read every region again and say which lines moved.

Before a batch is rendered, each recorded `source` is compared against a fresh
OCR read of its own box. Most differences are the agent having corrected the
reading and are not worth looking at. One kind is:

    when the text read out of this box is what some *other* region on the same
    page has recorded, the two lines were written onto each other's ids.

Nothing else catches that. Re-reading the page will not, because the Thai is
plausible where it sits; only the boxes disagree.

Differences that are not swaps are counted and not printed unless asked for. A
source the agent wrote rather than read — a placeholder in parentheses, a name
the reader gets wrong every time — differs on every run and always will, so the
list of them is a constant. The count moving is worth noticing; the list is not.
"""

from __future__ import annotations

import argparse
import json
import unicodedata
from pathlib import Path

from PIL import Image

from manga_honyaku.ocr import load_reader, read
from manga_honyaku.page import Series


# A pause is written a dozen ways between the page, the reader and the agent —
# `…`, `...`, `・・・`, and a colon where the reader saw three dots on a slant.
# None of those differences are differences.
PAUSE = str.maketrans(dict.fromkeys(".・:：", "…"))


def settle(text: str) -> str:
    text = "".join((text or "").split()).translate(PAUSE)
    while "……" in text:
        text = text.replace("……", "…")
    return text


def says_something(text: str) -> bool:
    """Whether a reading could identify a line.

    A pause could not: many regions record nothing but `…`, so a box reading as
    a pause matches any of them and means nothing by it.
    """
    return any(unicodedata.category(c).startswith(("L", "N")) for c in text)


def compare(data: dict, image: Image.Image, reader) -> list[tuple]:
    """Every region whose fresh reading is not what the file records."""
    recorded = {r["id"]: settle(r.get("source")) for r in data["regions"]}
    elsewhere = {}
    for rid, text in recorded.items():
        if says_something(text):
            elsewhere.setdefault(text, []).append(rid)

    moved = []
    for region in data["regions"]:
        rid = region["id"]
        fresh = settle(read(image, region["box"], reader)[0])
        if fresh == recorded[rid]:
            continue
        holders = [other for other in elsewhere.get(fresh, []) if other != rid]
        moved.append((rid, recorded[rid], fresh, holders))
    return moved


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("series", type=Path, help="a work's directory under series/")
    ap.add_argument("pages", nargs="*", help="page ids; a directory; none for all")
    ap.add_argument(
        "--differences",
        action="store_true",
        help="also list the readings the agent corrected, which do not change "
        "between runs",
    )
    args = ap.parse_args()

    work = Series(args.series)
    reader = load_reader()
    swaps = differences = 0

    for page in work.ids(args.pages):
        data = json.loads(work.agent(page).read_text())
        image = Image.open(work.scan(page)).convert("RGB")
        for rid, was, now, holders in compare(data, image, reader):
            if holders:
                swaps += 1
                print(f"{page} {rid}: this box reads {now!r}, "
                      f"which {', '.join(holders)} has recorded")
                print(f"{' ' * len(page)} {' ' * len(rid)}  it records {was!r}")
            else:
                differences += 1
                if args.differences:
                    print(f"{page} {rid}: {was!r} -> {now!r}")

    print(f"\n{swaps} line(s) on the wrong region, {differences} other difference(s)")
    raise SystemExit(1 if swaps else 0)


if __name__ == "__main__":
    main()
