"""Stage `render`: fit the Thai into each region and draw it.

Reads work/<page>.agent.json together with the cleaned artwork and the masks, and
writes out/<page>.png. Nothing here decides anything about meaning; it decides
where the letters go.

A region is drawn only where `clean` erased something. The mask is the record of
that: no mask, no space to draw into, and a sound effect or a phone screen that
was deliberately left alone does not get Thai painted over it.

Text goes inside the region's own box, and inside the bubble outline, and inside
neither alone. The box is where the Japanese was, and that placement is a
composition the letterer chose; the outline is a curve that a rectangle overflows
at the corners. So the two are intersected, and the outline side of it is pulled
in with a distance transform.

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
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from pythainlp.corpus.common import thai_words
from pythainlp.tokenize import subword_tokenize, word_tokenize
from pythainlp.util import Trie

from manga_honyaku.page import agent_path

FONT = os.environ.get("MANGA_HONYAKU_FONT")

# Thai writes without spaces between words, so a line may only break where one
# word ends.
ENGINE = os.environ.get("MANGA_HONYAKU_SEGMENTER", "newmm")

THAI_MIN, THAI_MAX = 0x0E00, 0x0E7F

# A continuation line starting with a Thai token this short or shorter is a stub
# left by a break inside a compound. The penalty has to outweigh the raggedness
# a more even split would cost, which is why it is this large.
ORPHAN_CLUSTERS = 3
ORPHAN_PENALTY = 5000.0

# Thai set beside the Japanese it replaces reads right at about this fraction of
# it. The number is the whole of the correspondence: wherever the original was
# lettered at 40, the Thai is lettered at 26, on every page and in every bubble.
# It is the one value a series would retune, and retuning it moves the entire
# work together rather than one bubble at a time.
#
# Thai needs more room than Japanese for the same sentence, so a target this size
# does not always fit. Where it does not, that region alone comes down; the rest
# of the page is unaffected.
RATIO = 0.65

# The floor, for a one-megapixel page and scaled by the square root of the actual
# area so it holds across scan resolutions. Below this the lettering stops being
# readable at print size, and a region that cannot hold its line here is reported
# rather than filled with specks.
FLOOR = 9

# How far the letters stay clear of the bubble outline, as a fraction of the
# region's shorter side.
INSET = 0.06

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


def original_size(region: dict) -> float | None:
    """How big the Japanese was, from the box it filled and how much filled it.

    Japanese sets on a square grid, so a box of area A holding n characters was
    lettered at about sqrt(A / n) — whichever way the text ran. Over the first
    page translated this read every ordinary bubble at 41 to 46 px and picked
    out the three the artist drew differently: the emphatic 撮影会？ at 80, and
    the muttered aside at 30.

    Sizing the Thai from this instead of from a fixed band is what keeps that
    difference. A band flattens it, and a fit against the bubble alone can even
    invert it, because the bubble with the fewest words is often the biggest.
    """
    source = region.get("source") or ""
    characters = len([c for c in source if not c.isspace()])
    if not characters:
        return None
    x1, y1, x2, y2 = region["box"]
    return math.sqrt((x2 - x1) * (y2 - y1) / characters)


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
    for token in word_tokenize(text, engine=ENGINE, custom_dict=custom):
        if not token:
            continue
        if token.isspace():
            space = True
            continue
        tokens.append((token, space))
        space = False
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
    text: str, font: ImageFont.FreeTypeFont, width: float, clusters: bool, custom=None
) -> list[str] | None:
    tokens = tokenise(text, custom)
    if clusters:
        broken: list[tuple[str, bool]] = []
        for token, space in tokens:
            if font.getlength(token) <= width:
                broken.append((token, space))
            else:
                parts = [p for p in subword_tokenize(token, engine="tcc_p") if p]
                broken.extend(
                    (part, space if k == 0 else False) for k, part in enumerate(parts)
                )
        tokens = broken
    return break_lines(tokens, font, width)


def safe_area(
    mask: np.ndarray, box: list[float], inset: int, confine: bool = True
) -> tuple[np.ndarray, int, int, tuple[float, float]]:
    """Where the Thai may go: inside the outline, and inside the original box.

    The mask alone would let a line spread across the whole bubble. The box is
    where the Japanese was, and where it was is a composition the letterer
    chose — text that drifts out of it lands somewhere the artist left empty on
    purpose. The mask still does the work the box cannot: the distance transform
    pulls the area in from the outline along the bubble's curve, so a line never
    touches it even where the box corner would.
    """
    import cv2

    if confine:
        limit = np.zeros(mask.shape, bool)
        x1, y1, x2, y2 = (int(v) for v in box)
        limit[y1:y2, x1:x2] = True
        within = mask & limit
    else:
        within = mask

    ys, xs = np.nonzero(within)
    if len(ys) == 0:
        return np.zeros((0, 0), bool), 0, 0, (0.0, 0.0)
    top, bottom, left, right = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    # Measured on the bubble, not on the intersection: the box edge is not an
    # edge to keep clear of, only the drawn outline is.
    distance = cv2.distanceTransform(mask.astype(np.uint8), cv2.DIST_L2, 5)
    safe = (distance >= inset) & within

    bys, bxs = np.nonzero(mask)
    centre = (float(bys.mean()) - top, float(bxs.mean()) - left)
    return safe[top:bottom, left:right], int(top), int(left), centre


def place(
    safe: np.ndarray, h: int, w: int, centre: tuple[float, float]
) -> tuple[int, int] | None:
    """Top-left of a h x w block wholly inside `safe`, as near `centre` as it goes.

    `centre` is the middle of the bubble, not of the area the block may occupy.
    Text sitting central in its bubble is what the eye expects; centring it in
    the box instead inherits whatever offset the Japanese column happened to
    have, and the box constraint still stops it drifting further than that.
    """
    H, W = safe.shape
    if h > H or w > W:
        return None
    # An integral image turns "is every pixel of this rectangle inside?" into
    # four lookups, so every position can be tested at once.
    integral = np.pad(safe.astype(np.int32), ((1, 0), (1, 0))).cumsum(0).cumsum(1)
    covered = (
        integral[h:, w:] - integral[:-h, w:] - integral[h:, :-w] + integral[:-h, :-w]
    )
    valid = np.argwhere(covered == h * w)
    if len(valid) == 0:
        return None
    target = np.array([centre[0] - h / 2, centre[1] - w / 2])
    return tuple(valid[np.argsort(((valid - target) ** 2).sum(axis=1))[0]])


def lay_out(
    text: str,
    safe: np.ndarray,
    font_path: str,
    largest: int,
    smallest: int,
    centre: tuple[float, float],
    custom=None,
):
    """The biggest size at which the text fits, with its lines and position.

    Word boundaries are tried at every size before any size is tried with
    breaks inside a word. Reversing that order — falling back to clusters as
    soon as one line is too tight — keeps the text large and splits ติดต่อมา as
    ติดต่|อมา, which reads as a typo rather than as a line break.
    """
    for clusters in (False, True):
        for size in range(largest, smallest - 1, -1):
            font = ImageFont.truetype(font_path, size)
            line_height = int(size * LINE_SPACING)
            for fraction in (1.0, 0.85, 0.7, 0.55):
                lines = wrap(text, font, safe.shape[1] * fraction, clusters, custom)
                if lines is None:
                    continue
                block_w = int(max(font.getlength(line) for line in lines)) + 2
                block_h = line_height * len(lines)
                at = place(safe, block_h, block_w, centre)
                if at is not None:
                    return font, lines, line_height, at, block_w
    return None


def render(
    page: Image.Image,
    masks: np.ndarray,
    data: dict,
    font_path: str,
    custom=None,
    weights: dict[str, str] | None = None,
):
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
    placements = []

    for index, region in enumerate(data["regions"], start=1):
        target = region.get("target")
        if not target:
            continue
        mask = masks == index
        if not mask.any():
            # clean left this one alone, so there is nowhere to put the Thai.
            continue

        x1, y1, x2, y2 = region["box"]
        inset = max(2, round(INSET * min(x2 - x1, y2 - y1)))

        # The size is decided before anything is wrapped, from the size the
        # Japanese was. The line breaking then has to make that size work.
        # Doing it the other way — take the largest that happens to fit —
        # lets the shape of each box set the size, and text the artist
        # lettered identically comes out anywhere across a range of two.
        original = original_size(region)
        # `scale` is the agent's, for the lines the ratio cannot reach: a shout
        # the artist drew no larger, a whisper drawn no smaller.
        emphasis = float(region.get("scale") or 1.0)
        smallest = max(4, round(FLOOR * scale))
        wanted = max(
            smallest,
            round(original * RATIO * emphasis) if original else smallest * 3,
        )
        face = weights.get(region.get("weight") or "regular", font_path)

        # At that size, the box first and the whole bubble second. The box is
        # where the Japanese sat, but it was a column set vertically, and
        # holding horizontal Thai inside a column that narrow buys a faithful
        # position at the cost of the size. Coming down in size is the last
        # resort, once neither area could hold it.
        laid = None
        for confine in (True, False):
            area = safe_area(mask, region["box"], inset, confine)
            if not area[0].any():
                continue
            safe, top, left, centre = area
            laid = lay_out(target, safe, face, wanted, wanted, centre, custom)
            if laid is not None:
                break
        if laid is None:
            safe, top, left, centre = safe_area(mask, region["box"], inset, False)
            if not safe.any():
                warn(f"{data['page']} {region['id']}: no room inside the outline")
                continue
            laid = lay_out(target, safe, face, wanted, smallest, centre, custom)
        if laid is None:
            warn(f"{data['page']} {region['id']}: {target!r} does not fit")
            continue
        placements.append((region, safe, top, left, centre, custom, face, laid))

    # One sentence lettered at two sizes reads as two sentences. Where regions
    # share an utterance they were one line in the original and are lettered
    # together here, at the size the tightest of them can hold.
    shared: dict[str, int] = {}
    for region, *_rest, laid in placements:
        group = region.get("utterance")
        if group:
            shared[group] = min(shared.get(group, 10**6), laid[0].size)

    for region, safe, top, left, centre, custom, face, laid in placements:
        group = region.get("utterance")
        if group and shared[group] != laid[0].size:
            again = lay_out(
                region["target"], safe, face,
                shared[group], shared[group], centre, custom,
            )
            if again is not None:
                laid = again

        font, lines, line_height, (by, bx), block_w = laid
        for i, line in enumerate(lines):
            width = font.getlength(line)
            draw.text(
                (left + bx + (block_w - width) / 2, top + by + i * line_height),
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
        "--font-bold", help="the same face in bold, for regions the agent marks"
    )
    args = ap.parse_args()

    if not args.font:
        raise SystemExit(
            "no font: pass --font or set MANGA_HONYAKU_FONT to a Thai .ttf. "
            "The marks must have zero advance; see this module's docstring."
        )
    args.out.mkdir(parents=True, exist_ok=True)
    custom = lexicon(args.series)
    weights = {"bold": args.font_bold} if args.font_bold else {}

    for page in args.pages:
        data = json.loads(agent_path(args.work, page.stem).read_text())
        clean = Image.open(args.work / f"{page.stem}.clean.png").convert("RGB")
        masks = np.asarray(Image.open(args.work / f"{page.stem}.masks.png"))
        out = args.out / f"{page.stem}.png"
        render(clean, masks, data, args.font, custom, weights).save(out)
        drawn = sum(1 for r in data["regions"] if r.get("target"))
        print(f"{page.name}  {out}  {drawn} regions")


if __name__ == "__main__":
    main()
