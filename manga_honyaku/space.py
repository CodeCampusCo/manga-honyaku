"""Where a gloss goes: the rectangle a region's Thai occupies, and the blank
space on a page to choose one from.

Free-placement lettering is erased by painting a white rectangle over its `box`,
and that box is the bounding rectangle of a vertical Japanese column, so it
sweeps up whatever the artist drew between and beside the glyphs. On `05/12` it
is 258x978 and it takes the manager's whole head. Every attempt to repair the
artwork instead — erasing the dark pixels, a text-segmentation model, an
inpainter — either destroyed line art or cost two models and a new dependency.

`at` is the answer that erases nothing. The Japanese stays where the artist drew
it and the Thai is drawn somewhere else on the same page: a margin, a gutter, a
blank corner inside a panel. Some publishers do exactly this. One rule follows
and governs everything else — **where `at` is present, every measurement uses
`at` instead of `box`** — which leaves `box` one job, saying where the Japanese
sits, so `clean` knows what to leave alone and `--repeats` can still find the
same line in another chapter.

`--space` is the half that chooses. Reading coordinates off a picture is what
`running-the-manga-pipeline` forbids, and picking a gutter by eye is exactly
that, so the picking happens here: the page's blank rectangles are found, the
ones this region's own Thai cannot use are dropped, and what is left is offered
as letters. `--take` writes the box. No coordinate passes through the agent in
either direction.

**No damage figure is printed and none should be.** Counting the dark pixels a
rectangle would cover measures how much line art is destroyed, which on a colour
page reports 3% where the truth is 100%. Whether a spot is acceptable is a
judgement made from the picture.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from string import ascii_lowercase

import cv2
import numpy as np
from PIL import Image, ImageFont

from manga_honyaku.annotate import annotate
from manga_honyaku.clean import PAPER
from manga_honyaku.page import Series
from manga_honyaku.render import (
    FONT,
    K,
    LINE_SPACING,
    PAGE_HEIGHT,
    floor_for,
    lay_out,
    lexicon,
    measured_at,
    settings,
    tokenise,
    where,
)

# A block of the page counts as blank only when every pixel in it is paper.
# Eight is fine enough to find a gutter and coarse enough that every maximal
# rectangle on a page can be enumerated for nothing.
BLOCK = 8

# What each region's box keeps around itself. The Japanese is staying on the
# page, so a gloss set flush against it reads as one column in two scripts.
AIR = 4

# Ink narrower than this is scan noise, not drawing. These scans put stray
# pixels at 224 on paper a reader sees as white, and a single speck left in
# splits a clean margin into two halves too narrow to use. Opening the ink drops
# anything that does not contain a square this wide.
SPECK = 3

# What a corner strip keeps between itself and the two page edges it sits in.
PAD = 10

# How many blank rectangles are worth reading. They come nearest first, so what
# this drops is the far end of the page: a four-character sound fits ninety
# places on some of these pages, and a list of ninety is not a list.
MOST = 12

# Roles whose regions were lettered by the artist as running text, and so the
# ones the gloss bar is measured from. A sign or a sound effect is drawn at
# whatever size the drawing wanted and says nothing about how small this work
# sets a sentence.
LETTERED = {"caption", "dialogue"}




def smallest_free(work: Series) -> list[tuple]:
    """Every free caption and dialogue region of the work, smallest size first.

    `size` is written by `prepare` from the Japanese and the box around it, so
    this is measurable before a word of Thai exists — unlike `k`, which is
    judged on a rendered page. What it answers is how small this work lets a
    sentence outside a balloon get, which is the bar a gloss has to clear:
    anything smaller is smaller than any caption the artist drew.

    Bubbles are left out because their size is a step off `k` rather than the
    extent of the lettering, and the other three roles because a sign, a sound
    and a masthead are drawn at whatever size the artwork wanted. A region that
    already carries an `at` is left out too: its `size` measures the rectangle
    somebody chose for it here, so it is not evidence about what the artist drew,
    and counted it would let one cramped gloss lower the bar for the next.
    """
    found = []
    for page in work.ids([]):
        for region in json.loads(work.agent(page).read_text())["regions"]:
            size = region.get("size")
            if region.get("bubble") or region.get("role") not in LETTERED:
                continue
            if region.get("at"):
                continue
            if isinstance(size, (int, float)):
                found.append((size, page, region["id"], region["role"]))
    return sorted(found)


def measured_bar(work: Series, values: dict) -> int | None:
    """That smallest size in Thai pixels, or None where nothing carries a role."""
    found = smallest_free(work)
    return round(found[0][0] * values.get("k", K)) if found else None


def bar_for(values: dict, gloss: int, scale: float) -> int:
    """The bar in this page's own pixels, and never under the work's floor.

    Scaled like `floor` and for the same reason: both count absolute pixels, so
    a volume scanned larger needs them scaled or the smallest lettering allowed
    comes out half the size on the page.
    """
    return max(floor_for(values, scale), round(gloss * scale))


def blank(gray: np.ndarray, regions: list[dict], region: dict) -> np.ndarray:
    """Blocks of the page that are paper and that nothing has claimed.

    Every region's `box` is subtracted because the Japanese in it is staying
    there, this region's included. Every *other* region's `at` is subtracted
    because a gloss already put there occupies the space; this region's own `at`
    is not, so that re-running offers the rectangle it currently holds.
    """
    ink = (gray <= PAPER).astype(np.uint8)
    ink = cv2.morphologyEx(ink, cv2.MORPH_OPEN, np.ones((SPECK, SPECK), np.uint8))
    free = ink == 0
    for other in regions:
        taken = [other["box"]]
        if other is not region and other.get("at"):
            taken.append(other["at"])
        for x1, y1, x2, y2 in (tuple(int(v) for v in box) for box in taken):
            free[max(y1 - AIR, 0) : y2 + AIR, max(x1 - AIR, 0) : x2 + AIR] = False
    rows, cols = free.shape[0] // BLOCK, free.shape[1] // BLOCK
    return free[: rows * BLOCK, : cols * BLOCK].reshape(
        rows, BLOCK, cols, BLOCK
    ).all(axis=(1, 3))


def rectangles(grid: np.ndarray) -> list[tuple[int, int, int, int]]:
    """Every maximal rectangle of blank blocks, in block coordinates.

    The histogram sweep: each column carries the run of blank blocks ending at
    this row, and a stack pops a run as soon as a *shorter* one arrives, which
    is the widest rectangle that run's height allows. A popped rectangle is kept
    only when the row below breaks it, so each is reported once rather than once
    for every row it grew through.

    Popping on equal heights instead — which the usual largest-rectangle sweep
    does, because it only wants an area — cuts every run at each column it
    passes and reports a page of one-block-wide slivers.
    """
    rows, cols = grid.shape
    heights = [0] * cols
    found = []
    for r in range(rows):
        for c in range(cols):
            heights[c] = heights[c] + 1 if grid[r, c] else 0
        stack: list[tuple[int, int]] = []
        for c in range(cols + 1):
            high = heights[c] if c < cols else 0
            start = c
            while stack and stack[-1][1] > high:
                start, tall = stack.pop()
                if r + 1 == rows or not grid[r + 1, start:c].all():
                    found.append((start, r - tall + 1, c, r + 1))
            if high and (not stack or stack[-1][1] < high):
                stack.append((start, high))
    return found


def gap(a, b) -> float:
    """How far apart two rectangles are, zero where they touch or overlap."""
    return math.hypot(
        max(0, a[0] - b[2], b[0] - a[2]), max(0, a[1] - b[3], b[1] - a[3])
    )


def share(a, b) -> float:
    """How much of the smaller of two rectangles the two have in common."""
    wide = min(a[2], b[2]) - max(a[0], b[0])
    tall = min(a[3], b[3]) - max(a[1], b[1])
    if wide <= 0 or tall <= 0:
        return 0.0
    smaller = min((a[2] - a[0]) * (a[3] - a[1]), (b[2] - b[0]) * (b[3] - b[1]))
    return wide * tall / smaller


def block(laid) -> tuple[int, int]:
    """The rectangle the laid-out text actually fills, inside the one it was
    given.

    What goes into `at` is this and not the blank area it was found in. `render`
    centres a free-placement block in its rectangle, so a rectangle larger than
    the text leaves the Thai floating in the middle of a strip with nothing to
    anchor it.
    """
    font, lines, line_height = laid
    wide = math.ceil(max(font.getlength(line) for line in lines))
    return wide, line_height * len(lines)


def nearest(wide: int, tall: int, outer, box) -> tuple[int, int, int, int]:
    """A block of that size inside `outer`, as near `box` as it will go.

    Centring it on the box and clamping to `outer` is the nearest position on
    each axis, so the gloss sits against the lettering it is standing in for.
    """
    x = min(max((box[0] + box[2] - wide) / 2, outer[0]), outer[2] - wide)
    y = min(max((box[1] + box[3] - tall) / 2, outer[1]), outer[3] - tall)
    return (round(x), round(y), round(x) + wide, round(y) + tall)


def one_line(
    text: str, width: float, font: str, custom, spacing: float, bar: int, wanted: int
):
    """The largest single line this width holds the whole text on.

    Advance width is linear in the size, so the first size tried is the answer
    or a pixel above it, and the walk down ends at once.
    """
    at_bar = ImageFont.truetype(font, bar).getlength(text)
    if not at_bar:
        return None
    for size in range(min(int(bar * width / at_bar), wanted), bar - 1, -1):
        laid = lay_out(
            text, (0, 0, width, math.ceil(size * spacing)), font, size, size,
            custom, spacing,
        )
        if laid:
            return laid
    return None


def corners(
    region: dict,
    page: tuple[int, int],
    font: str,
    custom,
    spacing: float,
    bar: int,
    wanted: int,
) -> list[tuple]:
    """The four corner-anchored strips, in case the page offers nothing else.

    A page can have nowhere blank a gloss fits — `05/00` is a colour opener and
    has none — and the rule that no coordinate is ever typed then leaves nowhere
    at all to go. So the corners are offered after whatever the page does have:
    one horizontal line of the text, set into each corner with `PAD` of air.

    **They are not blank and nothing here pretends they are.** Which corner a
    page can spare is a judgement made from the picture, the same as every other
    spot offered.

    And because a corner is paid for in artwork, it is set at the bar and not at
    the size the region would take elsewhere: a blank spot may match the weight
    of the line it stands in for, a hole may only be readable.
    """
    width, height = page
    laid = one_line(
        region["target"], width - 2 * PAD, font, custom, spacing, bar, bar
    )
    if laid is None:
        return []
    wide, tall = block(laid)
    found = [
        ((x, y, x + wide, y + tall), laid[0].size, f"{down} {across} corner")
        for across, x in (("left", PAD), ("right", width - PAD - wide))
        for down, y in (("top", PAD), ("bottom", height - PAD - tall))
    ]
    return sorted(found, key=lambda row: gap(row[0], region["box"]))


def margin(box, width: int, height: int) -> bool:
    """Whether this rectangle reaches the edge of the page.

    A rectangle that does is paper by construction — nothing was ever drawn out
    there. One that does not passed a brightness test and nothing more, and
    bright skin, cloth and sky all pass a brightness test. So this decides how
    carefully the spot has to be looked at, and it decides nothing else: it is
    not part of the ranking, and a gutter inside the artwork is often the right
    answer.
    """
    return (
        box[0] <= BLOCK
        or box[1] <= BLOCK
        or box[2] >= width - BLOCK
        or box[3] >= height - BLOCK
    )


def spaces(
    gray: np.ndarray,
    regions: list[dict],
    region: dict,
    font: str,
    custom,
    spacing: float,
    bar: int,
    wanted: int,
) -> list[tuple]:
    """Blank rectangles this region's Thai fits in, nearest to its box first.

    A rectangle the text cannot use is not a candidate, so each is laid out with
    the same function `fit` and `render` use, at or above the bar. Distance from
    the region's own box is the ranking, with one qualification: distances
    within a line of type of each other are the same distance, and between those
    the wider rectangle wins. Thai reads across, and a blank strip the shape of
    the Japanese column it replaces sets seven one-word lines down a margin.

    The two cheap tests before the layout are exact rather than approximate: no
    line can be narrower than the widest token, and no rectangle can hold the
    text in fewer lines than its total ink divided by its width.
    """
    probe = ImageFont.truetype(font, bar)
    tokens = tokenise(region["target"], custom)
    if not tokens:
        return []
    widest = max(probe.getlength(token) for token, _ in tokens)
    ink = sum(probe.getlength(token) for token, _ in tokens)
    line = bar * spacing

    laid: dict[tuple[int, int], object] = {}
    found = []
    for x1, y1, x2, y2 in rectangles(blank(gray, regions, region)):
        area = (x1 * BLOCK, y1 * BLOCK, x2 * BLOCK, y2 * BLOCK)
        wide, tall = area[2] - area[0], area[3] - area[1]
        if wide < widest or tall < math.ceil(ink / wide) * line:
            continue
        if (wide, tall) not in laid:
            laid[(wide, tall)] = lay_out(
                region["target"], (0, 0, wide, tall), font, bar,
                min(tall, wanted), custom, spacing,
            )
        if laid[(wide, tall)]:
            found.append((area, laid[(wide, tall)]))

    # Two rectangles that overlap are one spot on the page reported twice, and
    # the sweep returns every maximal rectangle, so a margin arrives as a dozen
    # of them differing by a block. Kept is the one the text draws largest in.
    kept: list[tuple] = []
    for area, fitted in sorted(
        found, key=lambda row: (-row[1][0].size, gap(row[0], region["box"]))
    ):
        if not any(share(area, other) for other, _ in kept):
            kept.append((area, fitted))

    height, width = gray.shape
    trimmed = []
    for area, fitted in kept:
        box = nearest(*block(fitted), area, region["box"])
        place = "page edge" if margin(box, width, height) else "in the drawing"
        trimmed.append((box, fitted[0].size, place))
    return sorted(
        trimmed,
        key=lambda row: (
            int(gap(row[0], region["box"]) / line),
            -(row[0][2] - row[0][0]) / (row[0][3] - row[0][1]),
        ),
    )


def report(
    work: Series, series: Path, page_id: str, rid: str, take: str | None
) -> None:
    """`--space`: the blank rectangles this region's Thai could be drawn in.

    Prints shapes, distances and letters, and never an origin. The rectangles
    are drawn onto `build/<page>.space.png` under the same letters, because the
    one question this cannot answer is whether a spot is somewhere the page can
    spare — and that is answered by looking at it.
    """
    values = settings(series)
    data = json.loads(work.agent(page_id).read_text())
    region = next((r for r in data["regions"] if r["id"] == rid), None)
    if region is None:
        raise SystemExit(f"{page_id} has no region {rid}")
    if not region.get("target"):
        raise SystemExit(
            f"{page_id} {rid} has no target yet. Which rectangles will do "
            "depends on the words going into them, so the Thai comes first."
        )

    gloss = values.get("gloss") or measured_bar(work, values)
    if gloss is None:
        raise SystemExit(
            "this work has no `gloss` in lettering.json, and no free caption or "
            "dialogue region to measure one from. See `new-manga-work`."
        )
    scale = data["img_height"] / values.get("page_height", PAGE_HEIGHT)
    bar = bar_for(values, gloss, scale)
    face = values.get("font") or FONT
    custom = lexicon(series)
    spacing = values.get("line_spacing", LINE_SPACING)
    page = (data["img_width"], data["img_height"])
    wanted = max(bar, round(values.get("k", K) * measured_at(region, page[1])))
    found = spaces(
        np.asarray(Image.open(work.scan(page_id)).convert("L")),
        data["regions"], region, face, custom, spacing, bar, wanted,
    )
    offered = list(
        zip(
            ascii_lowercase,
            found[:MOST] + corners(region, page, face, custom, spacing, bar, wanted),
        )
    )

    if take:
        chosen = dict(offered).get(take)
        if chosen is None:
            raise SystemExit(f"{page_id} {rid} was not offered a space {take!r}")
        box = chosen[0]
        region["at"] = list(box)
        # The two together are one decision. Written apart, a region with an
        # `at` and a status of `ok` has `clean` paint its box out *and* `render`
        # draw the Thai elsewhere, which costs the artwork twice over.
        region["status"] = "glossed"
        work.agent(page_id).write_text(
            json.dumps(data, ensure_ascii=False, indent=2) + "\n"
        )
        print(
            f"{page_id} {rid}  status glossed, `at` "
            f"{box[2] - box[0]}x{box[3] - box[1]}\n"
            f"  now: prepare --retag {series} {page_id}, then clean and render"
        )
        return

    if not offered:
        print(f"{page_id} {rid}  nothing on this page holds {region['target']!r} "
              f"at the bar of {bar}, corners included")
        return

    x1, y1, x2, y2 = region["box"]
    said = "from lettering.json" if values.get("gloss") else "measured from the work"
    print(
        f"{page_id} {rid}  {x2 - x1:.0f}x{y2 - y1:.0f}  {region.get('role') or '—'}"
        f"  bar {bar} ({said})\n  {region['target']}\n"
    )
    for letter, (box, size, place) in offered:
        print(
            f"  {letter}  {box[2] - box[0]:>4}x{box[3] - box[1]:<4}"
            f"  {gap(box, region['box']):>5.0f}px away  draws at {size:>3}  {place}"
        )
    if len(found) > MOST:
        print(f"  ({len(found) - MOST} more blank rectangles, all further away)")

    out = work.derived(page_id, "space.png")
    annotate(
        Image.open(work.scan(page_id)).convert("RGB"),
        [{"box": region["box"], "id": rid, "placement": "bubble"}]
        + [
            {"box": box, "id": letter, "placement": "free"}
            for letter, (box, *_) in offered
        ],
    ).save(out)
    print(
        f"\n  Nearest first, and a rectangle that reads across beats one the shape\n"
        f"  of the column it replaces. {out} has them under the same letters,\n"
        f"  with {rid} itself in blue — look at it before taking one.\n"
        f"  --take {offered[0][0]} writes that rectangle into {rid}'s `at`."
    )


def bar_report(work: Series, series: Path) -> None:
    """`--bar`: what this work's smallest free lettering says a gloss may be.

    The bar `--space` holds candidates to, and the sixth value in
    `lettering.json`. `floor` cannot serve as it: `floor` is the hard legibility
    limit, and at 7 it admits rectangles that letter this work's Thai half the
    size of any caption its artist drew.
    """
    values = settings(series)
    found = smallest_free(work)
    if not found:
        print("no free caption or dialogue region carries a role yet — "
              "nothing to measure the bar from")
        return
    for size, page, rid, role in found[:5]:
        print(f"  {size:>4}  {page} {rid:<4} {role}")
    k = values.get("k", K)
    print(f"\n  {found[0][0]} x k {k} = {measured_bar(work, values)}"
          f"   ({len(found)} free caption and dialogue regions)")
    if values.get("gloss") is not None:
        print(f"  lettering.json says gloss {values['gloss']}")
    else:
        print("  lettering.json has no `gloss` — write it in")
