"""Tool `fit`: what size a candidate line would be lettered at, before it is set.

Not a stage — it draws nothing and writes nothing, so it is safe to run on a page
mid-edit. It answers the question the wording pass keeps asking:

    uv run python -m manga_honyaku.fit series/<work> 01/05 F1 "เธอนำแสง"
    uv run python -m manga_honyaku.fit series/<work> 01/05

Named region/text pairs are measured; with none, every target the page's working
file already holds is. Each line reports the box, the size the Japanese was
lettered at, the size the Thai would be drawn at, how much of the box that fills,
and the lines it breaks into.

In a box drawn for vertical Japanese the size is set by the **longest token**,
not by the length of the line, so the fix for a caption lettered half-size is
usually a different word of the same meaning rather than a shorter sentence — and
the difference is large enough to be worth asking about rather than discovering
at render.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from manga_honyaku.page import Series
from manga_honyaku.render import FONT, LINE_SPACING, lay_out, lexicon, settings

# Below the floor nothing is readable, and the tool has to agree with `render`
# about that or it answers a question nobody asked.
SMALLEST = 7


def measure(region: dict, text: str, font: str, custom, spacing: float):
    """The size, the fill and the lines, or None where nothing fits."""
    x1, y1, x2, y2 = region["box"]
    width, height = x2 - x1, y2 - y1
    laid = lay_out(
        text, (x1, y1, width, height), font, SMALLEST, max(SMALLEST, int(height)),
        custom, spacing,
    )
    if laid is None:
        return None
    font_used, lines, line_height = laid
    return font_used.size, line_height * len(lines) / height, lines


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("series", type=Path, help="a work's directory under series/")
    ap.add_argument("page", help="one page id")
    ap.add_argument(
        "pairs",
        nargs="*",
        metavar="ID TEXT",
        help="region id and candidate line, repeated; none for what is already set",
    )
    args = ap.parse_args()

    if len(args.pairs) % 2:
        raise SystemExit("pairs are a region id and a line: F1 'เธอนำแสง'")

    work = Series(args.series)
    values = settings(args.series)
    font = values.get("font") or FONT
    spacing = values.get("line_spacing", LINE_SPACING)
    custom = lexicon(args.series)

    data = json.loads(work.agent(args.page).read_text())
    regions = {r["id"]: r for r in data["regions"]}

    pairs = list(zip(args.pairs[::2], args.pairs[1::2]))
    if not pairs:
        pairs = [(r["id"], r["target"]) for r in data["regions"] if r.get("target")]

    for rid, text in pairs:
        region = regions.get(rid)
        if region is None:
            raise SystemExit(f"{args.page} has no region {rid}")
        x1, y1, x2, y2 = region["box"]
        shape = f"{x2 - x1:.0f}x{y2 - y1:.0f}"
        got = measure(region, text, font, custom, spacing)
        if got is None:
            print(f"{rid:>4}  {shape}  jp={region.get('size')}  does not fit  {text}")
            continue
        size, fill, lines = got
        print(
            f"{rid:>4}  {shape}  jp={region.get('size')}  thai={size}"
            f"  fills {fill:.0%}  {lines}"
        )


if __name__ == "__main__":
    main()
