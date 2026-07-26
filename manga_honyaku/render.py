"""Stage `render`: fit the Thai into each region and draw it.

Reads work/<page>.agent.json together with the cleaned artwork and the masks, and
writes out/<page>.png. Nothing here decides anything about meaning; it decides
where the letters go.

A region is drawn only where `clean` erased something. The mask is the record of
that: no mask, no space to draw into, and a sound effect or a phone screen that
was deliberately left alone does not get Thai painted over it.

The geometry, the sizing and the collision test are MangaTranslator's, ported
rather than reinvented. A rectangle is grown from the bubble's own centre out to
its outline — moving that centre to the deepest point when it lands in the waist
between two conjoined lobes — the size is binary-searched within a narrow band
quoted for a one-megapixel page, and a laid-out block is checked corner by
corner against the mask rather than against that rectangle.

Thai is written horizontally, but a bubble is taller than it is wide, and Thai
lettering in manga is set to the bubble: a stack of short lines rather than two
long ones. So the column is narrowed a tenth at a time and the layout kept is
the one that stands tallest — the most lines the bubble will hold. That last
part is where this departs from upstream, which stops at the first width that
does not collide and so keeps the widest, shortest block that is merely legal.

Thai needs no complex-text shaping here. Its marks stack above and below the base
letter, and in a font that gives them zero advance — every Thai comic face does —
basic layout puts them in the right place. A font that positions marks through
GPOS instead would draw wrongly rather than fail, so a new one is worth looking
at before it is trusted.

Derived from meangrinch/MangaTranslator (Apache-2.0); see NOTICE.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
import unicodedata
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from pythainlp.corpus.common import thai_words
from pythainlp.tokenize import subword_tokenize, word_tokenize
from pythainlp.util import Trie

from manga_honyaku.page import agent_path

# The project letters in iannnnn's 2005_iannnnnJPG, a Thai comic face, and the
# bold cut derived from it. Not in this repository: its own name table records
# "For educations used only" and "All rights reserved", so it is referenced the
# way the model weights are. Put it under fonts/ or point these at it.
FONT = os.environ.get("MANGA_HONYAKU_FONT", "fonts/iannnnnJPG/2005_iannnnnJPG.ttf")
FONT_BOLD = os.environ.get(
    "MANGA_HONYAKU_FONT_BOLD", "fonts/iannnnnJPG-selfbold/2005_iannnnnJPG-Bold.ttf"
)

# Thai writes without spaces between words, so a line may only break where one
# word ends.
ENGINE = os.environ.get("MANGA_HONYAKU_SEGMENTER", "newmm")

# How finely a line may be broken, tried in this order at every size before the
# size comes down. A bubble is a tall oval because Japanese ran down it, so a
# phrase that will not wrap across is stacked down instead: `อะไรนะ` set as
# `อะ / ไร / นะ` is how Thai manga has filled these bubbles for as long as there
# has been Thai manga. `dict` breaks at syllables — `ติด|ต่อ|มา`, `ขอบ|คุณ` —
# and clusters are below it, for the word no syllable will fit either, where
# `ติ|ด|ต่|อ|มา` reads as a typo but is still better than nothing.
GRAINS = (None, "dict", "tcc_p")

THAI_MIN, THAI_MAX = 0x0E00, 0x0E7F

# Marks that open rather than close, and so belong to the word after them.
OPENING = set("“‘([{<«")

# A continuation line starting with a Thai token this short or shorter is a stub
# left by a break inside a compound. The penalty has to outweigh the raggedness
# a more even split would cost, which is why it is this large.
ORPHAN_CLUSTERS = 3
ORPHAN_PENALTY = 5000.0

# Fallbacks only. Every size a page is lettered at comes from series/lettering.md
# — a base and a set of named steps — because a letterer works from a small set
# of sizes and the translation should use the same set the same way. Nothing here
# is a size to letter at; these exist so a series with no file still renders.
BASE = 22
STEPS = {"normal": 1.0}
PADDING = 4.0
FLOOR = 9

# How many times a column is narrowed by a tenth in search of a taller
# block. Upstream stops at the first that does not collide and needs three;
# going on until the text will not wrap any narrower needs more.
SQUEEZES = 9

# Thai stacks marks above and below the base letter, so lines need more room
# between them than the font's own metrics suggest.
LINE_SPACING = 1.32


def warn(message: str) -> None:
    print(f"warning: {message}", file=sys.stderr)


def _signature(font: ImageFont.FreeTypeFont, char: str) -> bytes:
    mask = font.getmask(char)
    if not mask.size[0]:
        return b""
    return Image.frombytes("L", mask.size, bytes(mask)).tobytes()


def missing_glyphs(font: ImageFont.FreeTypeFont, text: str) -> set[str]:
    """Characters this font draws as the empty box.

    A font without the character renders .notdef, so comparing against a
    codepoint no font can have identifies it — no font library needed.
    """
    absent = _signature(font, "\U000f0000")
    return {c for c in set(text) if not c.isspace() and _signature(font, c) == absent}


def settings(series: Path) -> dict:
    """This work's lettering values, from series/lettering.md.

    Typography is not one rule that fits every work. The code measures the mask
    and executes a layout; what a band should be, how much clearance an outline
    of this weight wants, how much room a face needs between lines — those vary
    by work and by font, and they are recorded where the rest of the series'
    conventions are rather than compiled in.

    Absent values fall back to the defaults above, so a series with no file
    letters the way this one started out.
    """
    path = series / "lettering.md"
    if not path.exists():
        return {}
    found = {}
    section = ""
    for line in path.read_text().splitlines():
        if line.startswith("#"):
            section = line.strip("# ").lower()
            continue
        cells = [c.strip() for c in line.split("|")]
        if len(cells) < 4 or set(cells[1]) <= set("-: ") or not cells[2]:
            continue
        try:
            numbers = [float(v) for v in cells[2].split()]
        except ValueError:
            continue
        found.setdefault(section, {})[cells[1]] = (
            numbers[0] if len(numbers) == 1 else tuple(numbers)
        )
    return found


def original_size(region: dict) -> float | None:
    """What the Japanese in this region was lettered at.

    Japanese sets on a square grid, so a box of area A holding n characters was
    lettered at about sqrt(A / n) whichever way the text ran.

    A bubble holding only a pause is excluded: one character in a box sized for
    a beat of silence reads as enormous lettering, and the dots are drawn at
    ordinary size.
    """
    source = region.get("source") or ""
    if not any(unicodedata.category(c).startswith(("L", "N")) for c in source):
        return None
    characters = len([c for c in source if not c.isspace()])
    if not characters:
        return None
    x1, y1, x2, y2 = region["box"]
    return math.sqrt((x2 - x1) * (y2 - y1) / characters)


def step_for(region: dict, steps: dict) -> tuple[str, float]:
    """The series step this region's original size falls under.

    A letterer works from a small set of sizes, so the translation uses the same
    set and the original chooses which. Nothing about this is a judgement, which
    is why it is measured here rather than written into the working file.
    """
    size = original_size(region)
    ladder = sorted(
        ((name, v) for name, v in steps.items() if isinstance(v, tuple)),
        key=lambda item: item[1][1],
    )
    if not ladder:
        return "normal", 1.0
    if size is None:
        for name, (multiple, _) in ladder:
            if name == "normal":
                return name, multiple
        return ladder[0][0], ladder[0][1][0]
    for name, (multiple, ceiling) in ladder:
        if size <= ceiling:
            return name, multiple
    return ladder[-1][0], ladder[-1][1][0]


def lexicon(series: Path):
    """The series glossary, as words the segmenter must not break apart.

    A transliterated name is in no Thai dictionary: ชิโนบุ segments as ชิ|โน|บุ
    and the line breaker duly breaks a character into ชิโน and บุ on separate
    lines. The glossary already holds every agreed transliteration, so it is
    the list to hand the segmenter.
    """
    path = series / "glossary.md"
    if not path.exists():
        return None
    terms = set()
    for line in path.read_text().splitlines():
        cells = [c.strip() for c in line.split("|")]
        if len(cells) >= 4 and cells[2] and not set(cells[2]) <= set("-: "):
            terms.add(cells[2])
    if not terms:
        return None
    return Trie(set(thai_words()) | terms)


def tokenise(text: str, custom=None) -> list[tuple[str, bool]]:
    """Break points, each with whether a space belongs before it.

    Thai runs together without spaces, so the segmenter supplies the breaks. The
    spaces that are in the text separate phrases and must survive the round trip.
    """
    tokens: list[tuple[str, bool]] = []
    space = False
    pending = ""
    for token in word_tokenize(text, engine=ENGINE, custom_dict=custom):
        if not token:
            continue
        if token.isspace():
            space = True
            continue
        # The segmenter hands back `?`, `…` and quotes as tokens of their own,
        # and a line breaker told to stand as tall as it can will start a line
        # with one. Punctuation belongs to the word it leans on — which for an
        # opening mark is the word after it, not the word before.
        if not any(c.isalnum() for c in token):
            if token in OPENING:
                pending += token
            elif tokens and not space and not pending:
                tokens[-1] = (tokens[-1][0] + token, tokens[-1][1])
            else:
                tokens.append((pending + token, space))
                pending, space = "", False
            continue
        tokens.append((pending + token, space))
        pending, space = "", False
    if pending:
        tokens.append((pending, space))
    return tokens


def orphan_cost(token: str) -> float:
    """What it costs to start a continuation line with this token.

    A short Thai token at the head of a line is a stub left behind by a break
    inside a compound. Cost rises with cluster count inside the short band, so a
    three-cluster opener is charged more than a two-cluster head — a plain
    "shorter is worse" ordering prefers the wrong one of the two.
    """
    if not any(THAI_MIN <= ord(c) <= THAI_MAX for c in token):
        return 0.0
    clusters = len([c for c in subword_tokenize(token, engine="tcc_p") if c])
    if clusters == 0 or clusters > ORPHAN_CLUSTERS:
        return 0.0
    return ORPHAN_PENALTY * clusters


def break_lines(
    tokens: list[tuple[str, bool]], font: ImageFont.FreeTypeFont, width: float
) -> list[str] | None:
    """Lines chosen to minimise total raggedness, not filled greedily.

    Greedy filling packs each line to the edge and leaves the last one nearly
    empty, which in a bubble as narrow as these reads as a mistake. Minimising
    the sum of slack cubed spreads the words evenly instead. Knuth-Plass in
    shape, following the same approach as MangaTranslator's layout engine.
    """
    space_w = font.getlength(" ")
    widths = [font.getlength(t) for t, _ in tokens]
    n = len(tokens)
    if n == 0:
        return None

    cost = [float("inf")] * (n + 1)
    came_from = [0] * (n + 1)
    cost[0] = 0.0
    for i in range(1, n + 1):
        line = 0.0
        for j in range(i - 1, -1, -1):
            if j < i - 1 and tokens[j + 1][1]:
                line += space_w
            line += widths[j]
            if line > width:
                break
            badness = (width - line) ** 3
            if j > 0:
                badness += orphan_cost(tokens[j][0])
            if cost[j] + badness < cost[i]:
                cost[i] = cost[j] + badness
                came_from[i] = j
    if cost[n] == float("inf"):
        return None

    lines, end = [], n
    while end > 0:
        start = came_from[end]
        piece = tokens[start][0]
        for token, space in tokens[start + 1 : end]:
            piece += (" " if space else "") + token
        lines.insert(0, piece)
        end = start
    return lines


def wrap(
    text: str, font: ImageFont.FreeTypeFont, width: float, grain, custom=None
) -> list[str] | None:
    """Lines at one column width, breaking no finer than `grain` asks for.

    A token wider than the column is split; anything that fits is left whole, so
    a finer grain only ever reaches the words that need it.
    """
    tokens = tokenise(text, custom)
    if grain:
        broken: list[tuple[str, bool]] = []
        for token, space in tokens:
            if font.getlength(token) <= width:
                broken.append((token, space))
            else:
                parts = [p for p in subword_tokenize(token, engine=grain) if p]
                broken.extend(
                    (part, space if k == 0 else False) for k, part in enumerate(parts)
                )
        tokens = broken
    return break_lines(tokens, font, width)


def safe_box(mask: np.ndarray, padding: float):
    """The rectangle a line may occupy inside a bubble.

    Ported from MangaTranslator's calculate_centroid_expansion_box. The mask is
    padded by a pixel first so that a bubble touching the page edge does not get
    an inflated distance there; everything at least `padding` deep is the safe
    area; its centroid is the anchor.

    The step that matters for conjoined bubbles: where the centroid falls in a
    constriction — less than seven tenths of the deepest point — it sits in the
    waist between two lobes, and the anchor moves to the pole of inaccessibility
    instead. Then four rays from the anchor give the nearest edge in each
    direction, and the smaller of each opposing pair, doubled, is a rectangle
    centred on the anchor and wholly inside the bubble.
    """
    import cv2

    if mask is None or not mask.any():
        return None
    padded = np.zeros((mask.shape[0] + 2, mask.shape[1] + 2), np.uint8)
    padded[1:-1, 1:-1] = mask.astype(np.uint8) * 255
    distance = cv2.distanceTransform(padded, cv2.DIST_L2, cv2.DIST_MASK_PRECISE)[
        1:-1, 1:-1
    ]
    safe = ((distance >= padding).astype(np.uint8)) * 255
    if not safe.any():
        return None

    moments = cv2.moments(safe)
    if moments["m00"] == 0:
        return None
    cx = moments["m10"] / moments["m00"]
    cy = moments["m01"] / moments["m00"]

    _, deepest, _, pole = cv2.minMaxLoc(distance)
    h, w = safe.shape
    xi = max(0, min(int(round(cx)), w - 1))
    yi = max(0, min(int(round(cy)), h - 1))
    if distance[yi, xi] < deepest * 0.70:
        cx, cy = float(pole[0]), float(pole[1])
        xi, yi = int(round(cx)), int(round(cy))

    if safe[yi, xi] != 255:
        pixels = np.argwhere(safe == 255)
        nearest = np.argmin(((pixels - np.array([cy, cx])) ** 2).sum(axis=1))
        yi, xi = (int(v) for v in pixels[nearest])
        cx, cy = float(xi), float(yi)

    left = np.where(safe[yi, 0:xi] == 0)[0]
    right = np.where(safe[yi, xi:] == 0)[0]
    up = np.where(safe[0:yi, xi] == 0)[0]
    down = np.where(safe[yi:, xi] == 0)[0]
    to_left = xi - (left.max() if left.size else 0)
    to_right = right.min() if right.size else w - xi
    to_top = yi - (up.max() if up.size else 0)
    to_bottom = down.min() if down.size else h - yi

    half_w = min(to_left, to_right)
    half_h = min(to_top, to_bottom)
    half_w = half_w - 1 if half_w > 1 else half_w
    half_h = half_h - 1 if half_h > 1 else half_h
    box_w, box_h = 2 * max(0, half_w), 2 * max(0, half_h)
    if box_w <= 0 or box_h <= 0:
        return None
    return int(round(cx - box_w / 2)), int(round(cy - box_h / 2)), box_w, box_h


def collides(lines, font, line_height: int, box, mask: np.ndarray) -> bool:
    """Whether any line would cross the outline. Ported from _check_collision.

    Each line is centred in the box and the block is centred in it vertically,
    which is where it will be drawn; the four corners of every line are then
    tested against the mask. Corners are what a rectangle has and an oval does
    not, so they are where a block that fits the box but not the bubble sticks
    out.
    """
    bx, by, bw, bh = box
    mask_h, mask_w = mask.shape
    y = by + (bh - line_height * len(lines)) / 2
    for line in lines:
        line_w = font.getlength(line)
        x = bx + (bw - line_w) / 2
        y1, y2 = int(y), int(y + line_height)
        x1, x2 = int(x), int(x + line_w)
        for px, py in ((x1, y1), (x2, y1), (x1, y2), (x2, y2)):
            if not mask[
                max(0, min(py, mask_h - 1)), max(0, min(px, mask_w - 1))
            ]:
                return True
        y += line_height
    return False


def lay_out(
    text: str,
    box,
    mask: np.ndarray,
    font_path: str,
    smallest: int,
    largest: int,
    custom=None,
    line_spacing: float = LINE_SPACING,
    squeezes: int = SQUEEZES,
    lines_wanted: int | None = None,
):
    """The largest size that fits inside the outline, not merely inside the box.

    Thai is written horizontally, but a bubble is taller than it is wide, and
    Thai lettering in manga is set to the bubble rather than to the line: a
    stack of short lines rather than two long ones. Thai readers read it that
    way and have for as long as manga has been translated into Thai.

    So height is what is maximised, not size alone and not width. The column is
    narrowed a tenth at a time and every layout that fits is kept; the one
    chosen is the one that stands tallest — the most lines the bubble will hold.

    The narrowing and the collision test are MangaTranslator's. What differs is
    where it stops: upstream squeezes only until nothing collides, which leaves
    the first, widest, shortest block that happens to be legal. Taking the
    tallest instead is what fills a bubble that is taller than it is wide.

    Grain is tried inside the size search, not around it, so a phrase that will
    not wrap at word boundaries is stacked more finely at the size the original
    asked for rather than lettered smaller to make the words fit across.
    """
    _, _, width, height = box
    best = None
    low, high = smallest, largest
    while low <= high:
        size = (low + high) // 2
        if size <= 0:
            break
        font = ImageFont.truetype(font_path, size)
        line_height = int(size * line_spacing)

        fitted = None
        for grain in GRAINS:
            column = float(width)
            for _ in range(squeezes):
                lines = wrap(text, font, column, grain, custom)
                if lines is None:
                    # Narrowing only makes it taller; it will not start fitting.
                    break
                if line_height * len(lines) > height:
                    break
                if not collides(lines, font, line_height, box, mask):
                    # `lines` on a region is the agent overruling the default
                    # rule for a bubble where standing tallest is wrong — a
                    # short line in a wide bubble stacked into syllables.
                    if lines_wanted and len(lines) != lines_wanted:
                        pass
                    elif fitted is None or len(lines) > len(fitted):
                        fitted = lines
                column *= 0.90
            if fitted is not None:
                # A coarser grain held at this size. Going finer would only buy
                # breaks inside words that did not need breaking.
                break

        if fitted is not None:
            best = (font, fitted, line_height)
            low = size + 1
        else:
            high = size - 1
    return best


def render(
    page: Image.Image,
    masks: np.ndarray,
    data: dict,
    font_path: str,
    custom=None,
    weights: dict[str, str] | None = None,
    values: dict | None = None,
):
    values = values or {}
    sizes = values.get("sizes", {})
    other = values.get("other values", {})
    base = sizes.get("base", BASE)
    steps = {k: v for k, v in sizes.items() if k != "base"} or STEPS
    line_spacing = other.get("line_spacing", LINE_SPACING)
    squeezes = int(other.get("squeezes", SQUEEZES))
    image = page.copy()
    draw = ImageDraw.Draw(image)

    # A font that cannot draw a character draws an empty box, which looks like
    # lettering until someone reads it. Say so once, before anything is drawn.
    probe = ImageFont.truetype(font_path, 40)
    everything = "".join(r.get("target") or "" for r in data["regions"])
    absent = missing_glyphs(probe, everything)
    if absent:
        warn(f"{data['page']}: font has no glyph for {''.join(sorted(absent))}")

    weights = {"regular": font_path, **(weights or {})}
    scale = math.sqrt(image.width * image.height / 1_000_000)
    smallest = max(4, round(other.get("floor", FLOOR) * scale))
    padding = max(1.0, other.get("padding", PADDING) * scale)
    placements = []

    for index, region in enumerate(data["regions"], start=1):
        target = region.get("target")
        if not target:
            continue
        mask = masks == index
        if not mask.any():
            # clean left this one alone, so there is nowhere to put the Thai.
            continue

        # Clearance is for the drawn outline. A free-floating region has none:
        # its mask is the text's own extent, and holding letters off the edge of
        # that costs size for nothing to gain.
        box = safe_box(mask, padding if region.get("bubble") else 1.0)
        if box is None:
            warn(f"{data['page']} {region['id']}: no room inside the outline")
            continue
        bx, by, bw, bh = box

        if region.get("bubble"):
            _, multiple = step_for(region, steps)
            wanted = max(smallest, round(base * multiple * scale))
        else:
            # Free-floating text has no ladder because it needs none. A bubble's
            # box is bigger than the lettering inside it, so something has to say
            # how big that lettering should be; a free region's box is the
            # lettering's own extent, drawn around it. Filling the box is the
            # answer the original already gave. A heading is this case too.
            wanted = max(smallest, bh)
        face = weights.get(region.get("weight") or "regular", font_path)
        laid = lay_out(
            target,
            box,
            mask,
            face,
            smallest,
            wanted,
            custom,
            line_spacing,
            squeezes,
            region.get("lines"),
        )
        if laid is None:
            warn(f"{data['page']} {region['id']}: {target!r} does not fit")
            continue
        placements.append((region, box, mask, face, custom, laid))

    # One sentence lettered at two sizes reads as two sentences. Where regions
    # share an utterance they were one line in the original and are lettered
    # together here, at the size the tightest of them can hold.
    shared: dict[str, int] = {}
    for region, *_rest, laid in placements:
        group = region.get("utterance")
        if group:
            shared[group] = min(shared.get(group, 10**6), laid[0].size)

    for region, box, mask, face, custom, laid in placements:
        bx, by, bw, bh = box
        group = region.get("utterance")
        if group and shared[group] != laid[0].size:
            again = lay_out(
                region["target"], box, mask, face, shared[group], shared[group],
                custom, line_spacing, squeezes, region.get("lines"),
            )
            if again is not None:
                laid = again

        font, lines, line_height = laid
        block_h = line_height * len(lines)
        top = by + (bh - block_h) / 2
        for i, line in enumerate(lines):
            width = font.getlength(line)
            draw.text(
                (bx + (bw - width) / 2, top + i * line_height),
                line,
                font=font,
                fill=(0, 0, 0),
            )

    return image


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("pages", nargs="+", type=Path)
    ap.add_argument("--work", type=Path, default=Path("work"))
    ap.add_argument("--out", type=Path, default=Path("out"))
    ap.add_argument("--font", default=FONT, help="path to a Thai .ttf")
    ap.add_argument("--series", type=Path, default=Path("series"))
    ap.add_argument(
        "--font-bold",
        default=FONT_BOLD,
        help="the same face in bold, for regions the agent marks",
    )

    args = ap.parse_args()

    if not args.font or not Path(args.font).exists():
        raise SystemExit(
            f"no font at {args.font!r}. Put 2005_iannnnnJPG under fonts/, or "
            "point --font / MANGA_HONYAKU_FONT at another Thai face whose marks "
            "have zero advance — see this module's docstring."
        )
    args.out.mkdir(parents=True, exist_ok=True)
    custom = lexicon(args.series)
    values = settings(args.series)
    weights = (
        {"bold": args.font_bold}
        if args.font_bold and Path(args.font_bold).exists()
        else {}
    )

    for page in args.pages:
        data = json.loads(agent_path(args.work, page.stem).read_text())
        clean = Image.open(args.work / f"{page.stem}.clean.png").convert("RGB")
        masks = np.asarray(Image.open(args.work / f"{page.stem}.masks.png"))
        out = args.out / f"{page.stem}.png"
        render(clean, masks, data, args.font, custom, weights, values).save(out)
        drawn = sum(1 for r in data["regions"] if r.get("target"))
        print(f"{page.name}  {out}  {drawn} regions")


if __name__ == "__main__":
    main()
