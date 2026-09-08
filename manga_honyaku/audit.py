"""Stage `audit`: everything about a finished page that a machine can check.

Run it after `render`. It reads the working file against the artwork that was
actually produced and reports what is wrong, so that reading the pages can be
spent on the one question a machine cannot answer — whether the Thai reads.

Every check here exists because the failure it looks for reached a rendered page
at least once and nothing said so. Two of them are silent by construction:

  - `render` counts regions that *have* a target, not regions it drew. A region
    whose interior came out empty is reported as drawn and is blank on the page.
  - Nothing anywhere reports Japanese that survived `clean`. Furigana and small
    glyphs set against a bubble's outline are joined to the ink outside it, so
    the flood that finds the interior never reaches them, and they sit under the
    Thai in the finished page.

Neither needs a model to find. The masks record which region claimed which
pixels, so a region absent from them drew nothing; and ink left inside a
region's own box, outside the interior that was repainted, is text that should
have gone and did not.

The rest is bookkeeping the working file can answer on its own, and is here
because a translator checking it by hand is a translator not reading the page.

**Nothing here judges how the page looks.** The `page-look` pass does that by
eye, against an exception list a Thai reader calibrated. **A check whose output
is never work is not a check**, and this file is only worth running if everything
it prints is.

`status` has three values and each answers a different question, which is why
the third had to exist:

    ok        take the Japanese out and put this Thai in its place
    declined  leave the artwork alone; the reason says why
    erase     take the Japanese out and put nothing back

`erase` is for lettering that has to go and has no Thai — furigana boxed on its
own, a stray glyph the interior fill could not reach. Written as `ok` with no
target it is indistinguishable from a line somebody forgot to translate, and
written as `declined` it is never erased at all, so the page keeps the Japanese
while the record says it was handled.
"""

import argparse
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

from .clean import KEEP, PAPER
from .page import Series

# A region's box is where the lettering sat, so on a tight box some of the
# bubble's own outline falls inside it and reads as ink no matter how clean the
# page is. Across a volume that noise sits under 2% of the box at the 95th
# percentile and under 3.2% at the 99th, while the two regions known to have
# kept their Japanese measured 5.0% and 5.7%. The line goes above the noise,
# not at it: a checker that fires on every page is one nobody reads.
#
# **This one is a note, not a defect.** How much ink is left is not the
# question — where it is, is. Original lettering runs past its own box all the
# time, and residue at a margin is invisible; residue sitting under the Thai is
# a broken page. Only the rendered page answers that, so this points at pages to
# look at and never at pages to fix.
RESIDUE = 0.035


# `นะ` takes `คะ` and `น่ะ` takes `ค่ะ`: the tone mark matches across the pair or
# the spelling is wrong. Thai writers mix them constantly, so the instinct for
# what ordinary writing looks like is what produces the error rather than what
# catches it — which is exactly the shape of thing a machine should hold.
MISSPELT = {"นะค่ะ": "นะคะ", "น่ะคะ": "น่ะค่ะ"}


def cleaned(region: dict) -> bool:
    """Whether `clean` would have erased this region — its rule, not a copy."""
    return bool(
        region.get("role")
        and region.get("role") not in KEEP
        and region.get("status") != "declined"
    )


def record(data: dict) -> list[str]:
    """What the working file can be asked about without opening an image."""
    out = []
    regions = data["regions"]
    orders = sorted(r["order"] for r in regions if r.get("order") is not None)
    if orders != list(range(1, len(regions) + 1)):
        out.append(f"reading order is not 1..{len(regions)}: {orders}")

    for r in regions:
        rid = r["id"]
        if not r.get("role"):
            out.append(f"{rid}: no role, so no stage will touch it")
        if r.get("status") == "ok" and not r.get("target"):
            out.append(f"{rid}: ok with no target — erased, and nothing drawn back")
        if r.get("status") == "erase" and r.get("target"):
            out.append(f"{rid}: erase with a target — say which it is")
        if r.get("status") == "declined" and not r.get("reason"):
            out.append(f"{rid}: declined with no reason")
    return out


def spelling(data: dict) -> list[str]:
    """Misspellings no reading pass reliably catches, because they read fine."""
    out = []
    for r in data["regions"]:
        target = r.get("target") or ""
        for wrong, right in MISSPELT.items():
            if wrong in target:
                out.append(f"{r['id']}: {wrong} is not a spelling — {right}")
    return out


def drawn(data: dict, masks: Path) -> list[str]:
    """Regions that were erased and then drew nothing into the hole."""
    if not masks.exists():
        return ["no masks — the page has not been cleaned"]
    present = set(np.asarray(Image.open(masks)).flat)
    out = []
    for index, r in enumerate(data["regions"], start=1):
        if cleaned(r) and r.get("target") and index not in present:
            out.append(f"{r['id']}: has a target but claimed no interior — blank")
    return out


def residue(data: dict, clean_png: Path, masks: Path) -> list[str]:
    """Ink left inside a region's box that the interior never covered."""
    if not clean_png.exists() or not masks.exists():
        return []
    grey = np.asarray(Image.open(clean_png).convert("L"))
    ids = np.asarray(Image.open(masks))
    out = []
    for index, r in enumerate(data["regions"], start=1):
        if not cleaned(r):
            continue
        x1, y1, x2, y2 = (int(v) for v in r["box"])
        box_grey = grey[y1:y2, x1:x2]
        if box_grey.size == 0:
            continue
        left = (box_grey < PAPER) & (ids[y1:y2, x1:x2] != index)
        share = left.sum() / box_grey.size
        if share > RESIDUE:
            out.append(
                f"{r['id']}: {share:.0%} of its box is still ink — look at the "
                f"rendered page; fix only if it shows under the Thai"
            )
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("series", help="a work's directory under series/")
    parser.add_argument("pages", nargs="*", help="page ids; a directory; none for all")
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="print only the pages that have something wrong",
    )
    args = parser.parse_args()

    work = Series(Path(args.series))

    total = 0
    for page in work.ids(args.pages):
        data = json.loads(work.agent(page).read_text())
        found = (
            record(data)
            + spelling(data)
            + drawn(data, work.derived(page, "masks.png"))
            + residue(data, work.derived(page, "clean.png"), work.derived(page, "masks.png"))
        )
        if not work.rendered(page).exists():
            found.insert(0, "not rendered")
        total += len(found)
        if found:
            print(page)
            for line in found:
                print(f"  {line}")
        elif not args.quiet:
            print(f"{page}  ok")

    print(f"\n{total} finding(s)")
    sys.exit(1 if total else 0)


if __name__ == "__main__":
    main()
