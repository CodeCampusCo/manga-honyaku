"""Stage `render`: fit the Thai into each region and draw it.

Reads work/<page>.agent.json together with the cleaned artwork and the masks, and
writes out/<page>.png. Nothing here decides anything about meaning; it decides
where the letters go.

A region is drawn only where `clean` erased something. The mask is the record of
that: no mask, no space to draw into, and a sound effect or a phone screen that
was deliberately left alone does not get Thai painted over it.

The geometry and the sizing are MangaTranslator's, ported rather than
reinvented. A rectangle is grown from the bubble's own centre out to its
outline — moving that centre to the deepest point when it lands in the waist
between two conjoined lobes — and the size is binary-searched within a narrow
band quoted for a one-megapixel page. Between them those two produce a page
that letters evenly, which is the thing several attempts at deriving a size
per bubble did not.

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

# The band lettering is chosen from, and the clearance kept from the outline.
# These are MangaTranslator's defaults, quoted for a one-megapixel page and
# scaled by the square root of the actual area so one setting holds across scan
# resolutions.
#
# The band is what makes a page even. It is narrow — a factor of two — so most
# bubbles reach the top of it and land on the same size; only a bubble that
# genuinely cannot hold its line comes down, and it cannot come down far. Sizing
# each bubble to whatever it happens to hold produces a page that shouts and
# whispers by accident, which is what this replaced.
#
# Upstream's own defaults are 8 and 16. Those are a configured value there and
# are one here too: against this artwork they letter at about half what the
# Japanese did, and 11 to 22 puts the Thai at roughly two thirds of it, which is
# where it sits in MangaTranslator's own render of this page. `--size` retunes
# the pair for a series.
BAND = (11, 22)
PADDING = 4.0

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


def lay_out(
    text: str,
    width: int,
    height: int,
    font_path: str,
    smallest: int,
    largest: int,
    custom=None,
):
    """The largest size in the band whose wrapped block fits the rectangle.

    Binary search over the band, as MangaTranslator does. Word boundaries are
    tried at every size before any size is tried with breaks inside a word:
    reversing that keeps the text large and splits ติดต่อมา as ติดต่|อมา, which
    reads as a typo rather than as a line break.
    """
    for clusters in (False, True):
        best = None
        low, high = smallest, largest
        while low <= high:
            size = (low + high) // 2
            if size <= 0:
                break
            font = ImageFont.truetype(font_path, size)
            line_height = int(size * LINE_SPACING)
            lines = wrap(text, font, width, clusters, custom)
            if lines is not None and line_height * len(lines) <= height:
                best = (font, lines, line_height)
                low = size + 1
            else:
                high = size - 1
        if best is not None:
            return best
    return None


def render(
    page: Image.Image,
    masks: np.ndarray,
    data: dict,
    font_path: str,
    custom=None,
    weights: dict[str, str] | None = None,
    band: tuple[int, int] = BAND,
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
    smallest, largest = (max(4, round(v * scale)) for v in band)
    padding = max(1.0, PADDING * scale)
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

        # `scale` and `weight` are the agent's, for the lines the band cannot
        # reach on its own: a shout the artist drew no larger, a whisper drawn
        # no smaller, a word that wants a heavier cut.
        emphasis = float(region.get("scale") or 1.0)
        face = weights.get(region.get("weight") or "regular", font_path)
        laid = lay_out(
            target,
            bw,
            bh,
            face,
            smallest,
            max(smallest, round(largest * emphasis)),
            custom,
        )
        if laid is None:
            warn(f"{data['page']} {region['id']}: {target!r} does not fit")
            continue
        placements.append((region, box, face, custom, laid))

    # One sentence lettered at two sizes reads as two sentences. Where regions
    # share an utterance they were one line in the original and are lettered
    # together here, at the size the tightest of them can hold.
    shared: dict[str, int] = {}
    for region, *_rest, laid in placements:
        group = region.get("utterance")
        if group:
            shared[group] = min(shared.get(group, 10**6), laid[0].size)

    for region, (bx, by, bw, bh), face, custom, laid in placements:
        group = region.get("utterance")
        if group and shared[group] != laid[0].size:
            again = lay_out(
                region["target"], bw, bh, face, shared[group], shared[group], custom
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
        "--font-bold", help="the same face in bold, for regions the agent marks"
    )
    ap.add_argument(
        "--size",
        type=int,
        nargs=2,
        metavar=("MIN", "MAX"),
        default=BAND,
        help="lettering band for a one-megapixel page (default %(default)s)",
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
        render(clean, masks, data, args.font, custom, weights, tuple(args.size)).save(out)
        drawn = sum(1 for r in data["regions"] if r.get("target"))
        print(f"{page.name}  {out}  {drawn} regions")


if __name__ == "__main__":
    main()
