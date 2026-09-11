"""Stage `render`: fit the Thai into each region and draw it.

Reads pages/<id>.agent.json together with the cleaned artwork and the masks, and
writes out/<id>.png. Nothing here decides anything about meaning; it decides
where the letters go.

A region is drawn only where `clean` erased something. The mask is the record of
that: no mask, no space to draw into, and a sound effect or a phone screen that
was deliberately left alone does not get Thai painted over it.

There is no geometry here, and that is the point. The rectangle the Thai goes
into is the region's own `box` — where the original lettering sat. The artist
already chose it, and it is already the right shape: tall and narrow where the
Japanese ran down a bubble. Set the Thai into it, let the line breaker fill it,
and come down a size while it overflows.

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
import os
import statistics
import sys
import unicodedata
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from pythainlp.corpus.common import thai_words
from pythainlp.tokenize import subword_tokenize, word_tokenize
from pythainlp.util import Trie

from manga_honyaku.page import Series

# The project letters in iannnnn's 2005_iannnnnJPG, a Thai comic face, and the
# bold cut derived from it. Both are under fonts/; NOTICE says on what terms.
FONT = os.environ.get("MANGA_HONYAKU_FONT", "fonts/iannnnnJPG/2005_iannnnnJPG.ttf")
FONT_BOLD = os.environ.get(
    "MANGA_HONYAKU_FONT_BOLD", "fonts/iannnnnJPG-selfbold/2005_iannnnnJPG-Bold.ttf"
)

# Thai writes without spaces between words, so a line may only break where one
# word ends.
ENGINE = os.environ.get("MANGA_HONYAKU_SEGMENTER", "newmm")

THAI_MIN, THAI_MAX = 0x0E00, 0x0E7F

# Marks that open rather than close, and so belong to the word after them.
OPENING = set("“‘([{<«")

# `ๆ` repeats the word before it and means nothing apart from it, so it leans
# backwards exactly as a closing mark does. It has to be named: Unicode files it
# as a modifier letter, so the "no alphanumerics" test that finds the other
# marks reads it as a word in its own right and lets a line open with it.
REPEATING = "ๆ"

# A continuation line starting with a Thai token this short or shorter is a stub
# left by a break inside a compound. The penalty has to outweigh the raggedness
# a more even split would cost, which is why it is this large.
ORPHAN_CLUSTERS = 3
ORPHAN_PENALTY = 5000.0

# Thai pixels per pixel of the original's lettering. One number for a whole
# work — the real one is in series/lettering.json — because what has to survive
# translation is the *ratio* between the regions on a page, and a single
# multiplier preserves every one of them exactly. It is a property of the two
# faces, Thai against Japanese, so it is set once by eye on a rendered page and
# then left alone. Nothing about a region changes it.
K = 1.07

# The smallest lettering a work will accept, before the page's own scale. A work
# sets its own as `floor` in lettering.json; this is what a work that has not.
SMALLEST = 9

# And what nothing may go below whatever a work asks for.
UNREADABLE = 4

# A page where nothing could be measured still has to be lettered. Ordinary
# dialogue runs about this fraction of the page's height.
TYPICAL = 0.022

# Enough of the alphabet to take a median from. Thai consonants are drawn to one
# width give or take, so the middle of these is what one character costs.
THAI_CONSONANTS = "กขคงจฉชซดตถทนบปผพฟมยรลวสหอ"

# How far a line may miss its `room` before saying so is worth the noise. Under
# the first the bubble reads empty; over the second the lettering is visibly
# smaller than its neighbours. Between them nothing is wrong enough to mention.
EMPTY, CRAMPED = 0.45, 1.8

# The height `floor` is quoted for. `floor` counts absolute pixels rather than a
# ratio, so a volume scanned larger needs it scaled or the smallest lettering
# allowed comes out half as big on the page.
PAGE_HEIGHT = 1600

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


def measured_at(region: dict, page_height: int) -> float:
    """What the original lettered this region at, or the page's usual size.

    A `size` that is not a number is not a measurement — an earlier vocabulary
    here named sizes instead of measuring them, and a work carrying one of those
    names would otherwise reach the arithmetic and stop the run on a traceback.
    """
    size = region.get("size")
    return size if isinstance(size, (int, float)) else TYPICAL * page_height


def floor_for(values: dict, scale: float) -> int:
    """The smallest size this work letters at, in this page's pixels."""
    return max(UNREADABLE, round(values.get("floor", SMALLEST) * scale))


def settings(series: Path) -> dict:
    """This work's lettering values, from series/lettering.json.

    Typography is not one rule that fits every work. The code measures and
    executes; what the steps are, how much room a face needs between lines, how
    small is too small — those vary by work and by font, and they are recorded
    with the rest of the series' conventions rather than compiled in.

    How to arrive at them for a new work is in the `thai-manga-lettering` skill.
    Absent values fall back to the defaults above.
    """
    path = series / "lettering.json"
    return json.loads(path.read_text()) if path.exists() else {}


def widths(font_path: str) -> tuple[float, set[str]]:
    """What a character of this face costs: one width, and which cost nothing.

    Asked of the font rather than of Unicode. Thai's above-vowels carry a
    combining class of zero — a fact about collation, not about typesetting — so
    `unicodedata.combining` calls ั ิ ี ึ ื ็ ์ ํ ๎ ordinary characters and
    overstates a line by about a tenth. The face is the only authority on what
    it draws, and asking it means a face whose marks do advance would measure
    correctly here without anyone remembering to come back.

    A mark is measured **on a base and not alone.** Pillow answers for a lone
    mark differently depending on whether libraqm is in the build — zero without
    it, a full width with it — and one of those machines is this one and the
    other is the CI runner. Asked the way the text is actually set, the two
    agree to under a pixel across a line, which is the same question `wrap` puts
    to the font.
    """
    face = ImageFont.truetype(font_path, 100)
    base = THAI_CONSONANTS[0]
    alone = face.getlength(base)
    # Under a twentieth of a character is nothing. Shaping through HarfBuzz
    # returns fractional advances, and four of these marks come back a tenth of
    # a pixel wider than the base they sit on; asking for exactly zero calls
    # them ordinary characters and overstates every line that has one.
    free = {
        chr(c)
        for c in range(0x0E00, 0x0E60)
        if _named(chr(c)) and face.getlength(base + chr(c)) - alone < alone / 20
    }
    one = statistics.median(face.getlength(c) for c in THAI_CONSONANTS) / 100
    return one, free


def _named(character: str) -> bool:
    """Whether Unicode assigns this code point at all."""
    try:
        unicodedata.name(character)
    except ValueError:
        return False
    return True


def room_for(box: list[float], size: int, spacing: float, one: float) -> int:
    """How many characters the box holds at that size.

    The translator's budget, written into the working file so that the length of
    a line is something to compose against rather than something to discover at
    render. It is a guide and not a bar: a line landing well over it is lettered
    smaller, which the reader forgives, and one landing under half of it leaves
    the bubble looking empty, which the reader sees before reading it.
    """
    x1, y1, x2, y2 = box
    lines = int((y2 - y1) // (size * spacing))
    return max(0, round(lines * (x2 - x1) / (size * one)))


def lexicon(series: Path):
    """The segmenter's dictionary: pythainlp's, plus `series/words.txt`.

    One Thai word per line, nothing else in the file.

    What belongs in it: words that mean nothing once cut in half. Names, and
    transliterations no Thai dictionary carries — `ฮารุกะ` otherwise segments as
    `ฮา|รุ|กะ` and lands across two lines. What does not: a phrase whose parts
    are ordinary words. In the dictionary a phrase is a single token, and a token
    too wide for its box brings that whole region's size down.

    Called once per run: the Trie costs about 200ms to build, and every page
    after the first reuses it.
    """
    path = series / "words.txt"
    if not path.exists():
        return None
    terms = {word.strip() for word in path.read_text().splitlines() if word.strip()}
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
        if token == REPEATING or not any(c.isalnum() for c in token):
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
    text: str, font: ImageFont.FreeTypeFont, width: float, custom=None
) -> list[str] | None:
    """Lines that fit the column, or None when a word is wider than it is."""
    return break_lines(tokenise(text, custom), font, width)


def lay_out(
    text: str,
    box,
    font_path: str,
    smallest: int,
    largest: int,
    custom=None,
    line_spacing: float = LINE_SPACING,
):
    """The largest size at which the text fits the box.

    The box is where the original's lettering sat, so it is already the shape
    the translation wants — tall and narrow where the Japanese ran down a
    bubble. That makes the whole of layout two steps: break to the column the
    box gives, and come down a size while the stack is taller than the box.

    Nothing searches for a better column, because there is no better column to
    find. Anything that overflows is answered by size, and only by size.
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
        lines = wrap(text, font, width, custom)
        if lines is not None and line_height * len(lines) <= height:
            best = (font, lines, line_height)
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
    k = values.get("k", K)
    line_spacing = values.get("line_spacing", LINE_SPACING)
    scale = page.height / values.get("page_height", PAGE_HEIGHT)
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
    smallest = floor_for(values, scale)
    placements = []

    for index, region in enumerate(data["regions"], start=1):
        target = region.get("target")
        if not target:
            continue
        mask = masks == index
        if not mask.any():
            # clean left this one alone, so there is nowhere to put the Thai.
            continue

        # Where the original's lettering sat, and so where this goes.
        x1, y1, x2, y2 = region["box"]
        box = (x1, y1, x2 - x1, y2 - y1)
        bx, by, bw, bh = box

        if region.get("bubble"):
            # The size was measured when the page was prepared: what the
            # Japanese was lettered at, in this page's own pixels. Both faces
            # are measured on the same page, so `k` needs no scaling.
            wanted = max(smallest, round(k * measured_at(region, page.height)))
        else:
            # Free-floating text takes no step. Its box is the lettering's own
            # extent, drawn around it, so filling that box is the answer the
            # original already gave. A chapter heading is this case.
            wanted = max(smallest, bh)
        face = weights.get(region.get("weight") or "regular", font_path)
        laid = lay_out(target, box, face, smallest, wanted, custom, line_spacing)
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
                region["target"], box, face, shared[group], shared[group],
                custom, line_spacing,
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


def calibrate(work: Series, pages, custom, font: str, values: dict) -> None:
    """What each candidate `k` would do, so it is chosen on evidence.

    A region is set at `k` times its measured size and comes down while it
    overflows, so past some `k` the page stops getting bigger and raising it only
    turns regions that fitted into regions that get shrunk. Shrinking is
    arbitrary, so what pays is the ratio between the regions on a page, which is
    the one thing the size carries. The eye cannot see that happening — the last
    three rows of this table look alike on paper and are not alike at all.

    Take the knee: the largest `k` at which `drew` is still rising.
    """
    spacing = values.get("line_spacing", LINE_SPACING)
    regions = []
    for page in pages:
        data = json.loads(work.agent(page).read_text())
        scale = data["img_height"] / values.get("page_height", PAGE_HEIGHT)
        smallest = floor_for(values, scale)
        for r in data["regions"]:
            if not r.get("target") or not r.get("bubble"):
                continue
            x1, y1, x2, y2 = r["box"]
            size = measured_at(r, data["img_height"])
            regions.append((r["target"], (x1, y1, x2 - x1, y2 - y1), smallest, size))

    print(f"{len(regions)} regions with Thai in a bubble")
    print(f"{'k':>6}{'fitted':>9}{'drew':>9}{'ratios kept':>14}")
    for k in (0.7, 0.8, 0.9, 1.0, 1.1, 1.2):
        got = []
        for target, box, smallest, size in regions:
            wanted = max(smallest, round(k * size))
            laid = lay_out(target, box, font, smallest, wanted, custom, spacing)
            if laid:
                got.append((laid[0].size / size, laid[0].size >= wanted))
        drew = [g for g, _ in got]
        fitted = sum(f for _, f in got) / len(got)
        kept = 1 - statistics.pstdev(drew) / statistics.mean(drew)
        print(f"{k:6.2f}{fitted:8.0%}{statistics.median(drew):8.2f}x{kept:13.0%}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("series", type=Path, help="a work's directory under series/")
    ap.add_argument("pages", nargs="*", help="page ids; a directory; none for all")
    ap.add_argument(
        "--calibrate",
        action="store_true",
        help="draw nothing; print what each candidate `k` would do, to choose "
        "the one in lettering.json by",
    )
    ap.add_argument(
        "--font",
        help="path to a Thai .ttf, overriding the one in lettering.json",
    )
    ap.add_argument(
        "--font-bold",
        default=FONT_BOLD,
        help="the same face in bold, for regions the agent marks",
    )

    args = ap.parse_args()

    work = Series(args.series)
    custom = lexicon(args.series)
    values = settings(args.series)

    # The face belongs with the rest of the stylesheet: `room` was counted in
    # its widths when the page was prepared, so rendering in another one would
    # letter to a budget nothing had measured.
    font = args.font or values.get("font") or FONT
    if not Path(font).exists():
        raise SystemExit(
            f"no font at {font!r}. Put 2005_iannnnnJPG under fonts/, name a face "
            "in the work's lettering.json, or point --font / MANGA_HONYAKU_FONT "
            "at another Thai face whose marks have zero advance — see this "
            "module's docstring."
        )
    _, free = widths(font)
    if args.calibrate:
        calibrate(work, work.ids(args.pages), custom, font, values)
        return
    weights = (
        {"bold": args.font_bold}
        if args.font_bold and Path(args.font_bold).exists()
        else {}
    )

    for page in work.ids(args.pages):
        data = json.loads(work.agent(page).read_text())
        clean = Image.open(work.derived(page, "clean.png")).convert("RGB")
        masks = np.asarray(Image.open(work.derived(page, "masks.png")))
        out = work.rendered(page)
        render(clean, masks, data, font, custom, weights, values).save(out)
        drawn = sum(1 for r in data["regions"] if r.get("target"))
        print(f"{page}  {out}  {drawn} regions")

        # Not a failure, so not a warning: a line may miss its budget and be the
        # right line anyway. Said once, in numbers, for whoever wants to look.
        for region in data["regions"]:
            target, room = region.get("target"), region.get("room")
            if not target or not room:
                continue
            written = sum(1 for c in target if c not in free)
            if not EMPTY * room < written < CRAMPED * room:
                print(f"{' ' * len(page)}  {region['id']} wrote {written} of {room}")


if __name__ == "__main__":
    main()
