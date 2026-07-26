"""Stage `render`: fit the Thai into each region and draw it.

Reads work/<page>.agent.json together with the cleaned artwork and the masks, and
writes out/<page>.png. Nothing here decides anything about meaning; it decides
where the letters go.

A region is drawn only where `clean` erased something. The mask is the record of
that: no mask, no space to draw into, and a sound effect or a phone screen that
was deliberately left alone does not get Thai painted over it.

Text is placed inside the mask itself, not inside the bounding box. A bubble is
round and its box is not, so a block sized to the box overflows the curve at the
corners. The mask is shrunk by a margin first, so the letters never touch the
outline they sit inside.

Thai needs no complex-text shaping here. Its marks stack above and below the
base letter, and in a font that gives them zero advance — Sarabun does — basic
layout puts them in the right place. A font that positions marks through GPOS
instead would need a shaping engine, so a new font is worth looking at before
it is trusted.

Derived from meangrinch/MangaTranslator (Apache-2.0); see NOTICE.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from pythainlp.tokenize import subword_tokenize, word_tokenize

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

# Below this the lettering stops being readable at print size, and a bubble that
# cannot hold its line at this size is reported rather than filled with specks.
MIN_SIZE = 13

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


def tokenise(text: str) -> list[tuple[str, bool]]:
    """Break points, each with whether a space belongs before it.

    Thai runs together without spaces, so the segmenter supplies the breaks. The
    spaces that are in the text separate phrases and must survive the round trip.
    """
    tokens: list[tuple[str, bool]] = []
    space = False
    for token in word_tokenize(text, engine=ENGINE):
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
    text: str, font: ImageFont.FreeTypeFont, width: float, clusters: bool
) -> list[str] | None:
    tokens = tokenise(text)
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


def safe_area(mask: np.ndarray, inset: int) -> tuple[np.ndarray, int, int]:
    """The mask pulled in by `inset` pixels, cropped to its own bounds."""
    import cv2

    ys, xs = np.nonzero(mask)
    if len(ys) == 0:
        return np.zeros((0, 0), bool), 0, 0
    y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    crop = mask[y0:y1, x0:x1].astype(np.uint8)
    # Distance to the outside; keeping only what is `inset` deep is an erosion
    # that follows the bubble's curve rather than a rectangle's corners.
    distance = cv2.distanceTransform(crop, cv2.DIST_L2, 5)
    return distance >= inset, int(y0), int(x0)


def place(safe: np.ndarray, h: int, w: int) -> tuple[int, int] | None:
    """Top-left of a h x w block lying wholly inside `safe`, nearest its centre."""
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
    ys, xs = np.nonzero(safe)
    target = np.array([ys.mean() - h / 2, xs.mean() - w / 2])
    return tuple(valid[np.argsort(((valid - target) ** 2).sum(axis=1))[0]])


def lay_out(text: str, safe: np.ndarray, font_path: str, largest: int):
    """The biggest size at which the text fits, with its lines and position.

    Word boundaries are tried at every size before any size is tried with
    breaks inside a word. Reversing that order — falling back to clusters as
    soon as one line is too tight — keeps the text large and splits ติดต่อมา as
    ติดต่|อมา, which reads as a typo rather than as a line break.
    """
    for clusters in (False, True):
        for size in range(largest, MIN_SIZE - 1, -1):
            font = ImageFont.truetype(font_path, size)
            line_height = int(size * LINE_SPACING)
            for fraction in (1.0, 0.85, 0.7, 0.55):
                lines = wrap(text, font, safe.shape[1] * fraction, clusters)
                if lines is None:
                    continue
                block_w = int(max(font.getlength(line) for line in lines)) + 2
                block_h = line_height * len(lines)
                at = place(safe, block_h, block_w)
                if at is not None:
                    return font, lines, line_height, at, block_w
    return None


def render(page: Image.Image, masks: np.ndarray, data: dict, font_path: str):
    image = page.copy()
    draw = ImageDraw.Draw(image)

    # A font that cannot draw a character draws an empty box, which looks like
    # lettering until someone reads it. Say so once, before anything is drawn.
    probe = ImageFont.truetype(font_path, 40)
    everything = "".join(r.get("target") or "" for r in data["regions"])
    absent = missing_glyphs(probe, everything)
    if absent:
        warn(f"{data['page']}: font has no glyph for {''.join(sorted(absent))}")

    # Lettering on one page should not swing from tiny to enormous just because
    # one bubble holds two words. The cap is what stops the short lines running
    # away; a crowded bubble is still free to go smaller.
    cap = round(image.height * 0.035)

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
        safe, top, left = safe_area(mask, inset)
        if not safe.any():
            warn(f"{data['page']} {region['id']}: no room inside the outline")
            continue

        laid = lay_out(
            target, safe, font_path, largest=min(cap, int(safe.shape[0] / 1.6))
        )
        if laid is None:
            warn(f"{data['page']} {region['id']}: {target!r} does not fit")
            continue

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
    args = ap.parse_args()

    if not args.font:
        raise SystemExit(
            "no font: pass --font or set MANGA_HONYAKU_FONT to a Thai .ttf. "
            "The marks must have zero advance; see this module's docstring."
        )
    args.out.mkdir(parents=True, exist_ok=True)

    for page in args.pages:
        data = json.loads(agent_path(args.work, page.stem).read_text())
        clean = Image.open(args.work / f"{page.stem}.clean.png").convert("RGB")
        masks = np.asarray(Image.open(args.work / f"{page.stem}.masks.png"))
        out = args.out / f"{page.stem}.png"
        render(clean, masks, data, args.font).save(out)
        drawn = sum(1 for r in data["regions"] if r.get("target"))
        print(f"{page.name}  {out}  {drawn} regions")


if __name__ == "__main__":
    main()
