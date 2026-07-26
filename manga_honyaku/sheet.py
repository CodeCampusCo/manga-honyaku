"""Build a contact sheet sized for reading, not for archiving.

An image is read at roughly its pixel count over 750 tokens, and anything longer
than 1568px on a side is resampled down to that before it is read at all. So a
full-resolution page costs the most a page can cost and shows nothing a 1568px
one does not. Pages laid out side by side share that budget: four pages on one
sheet cost what one page costs.

This scales the pages to fit the limit and reports the width each one ended up
at, because the thing worth knowing is whether the lettering survived. Below
`LEGIBLE` it has not, and the sheet is only good for panel layout and reading
order — read fewer pages per sheet instead.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image

# Beyond this the reader resamples, so pixels past it are paid for and thrown
# away.
LIMIT = 1568

# Measured on this project's pages: at 380px wide a bubble's Thai is still
# readable, and panel layout stays clear well below that.
LEGIBLE = 380


def build(paths: list[Path], columns: int | None = None, width: int | None = None):
    images = [Image.open(p).convert("RGB") for p in paths]
    columns = columns or len(images)
    rows = -(-len(images) // columns)
    tallest = max(i.height / i.width for i in images)

    if width is None:
        width = min(LIMIT // columns, int(LIMIT / (rows * tallest)))
    cell_h = int(width * tallest)

    sheet = Image.new("RGB", (columns * width, rows * cell_h), "white")
    for index, image in enumerate(images):
        scaled = image.resize((width, round(image.height * width / image.width)))
        x = (index % columns) * width
        y = (index // columns) * cell_h
        sheet.paste(scaled, (x, y))
    return sheet, width


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("images", nargs="+", type=Path)
    ap.add_argument("-o", "--out", type=Path, required=True)
    ap.add_argument("--columns", type=int, help="default: all on one row")
    ap.add_argument("--width", type=int, help="per image; default: as large as fits")
    args = ap.parse_args()

    sheet, width = build(args.images, args.columns, args.width)
    sheet.save(args.out)
    note = "" if width >= LEGIBLE else "  (too small to read lettering)"
    print(f"{args.out}  {sheet.width}x{sheet.height}  {width}px per image{note}")


if __name__ == "__main__":
    main()
