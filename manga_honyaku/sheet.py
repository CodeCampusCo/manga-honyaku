"""Build a contact sheet sized for reading, not for archiving.

An image is read at roughly its pixel count over 750 tokens, and anything longer
than 1568px on a side is resampled down to that before it is read at all. So a
full-resolution page costs the most a page can cost and shows nothing a 1568px
one does not. Pages laid out side by side share that budget: four pages on one
sheet cost what one page costs.

So the width is capped at `WIDEST`: a page at 1568px costs about 2300 tokens and
at 800px about 1200, and reads no worse. One page and two pages then come out the
same price, which makes reading a spread free next to reading a page.

`--crop` takes a box out before the sheet is built, so reading one bubble never
means writing a resize by hand and guessing at the size.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image

# Beyond this the reader resamples, so pixels past it are paid for and thrown
# away.
LIMIT = 1568

# The most any one image is worth. Past this a page stops getting easier to read
# and goes on getting more expensive, quadratically.
WIDEST = 800

# Measured on this project's pages: at 380px wide a bubble's Thai is still
# readable, and panel layout stays clear well below that.
LEGIBLE = 380


def build(
    paths: list[Path],
    columns: int | None = None,
    width: int | None = None,
    crop: tuple[int, int, int, int] | None = None,
):
    images = [Image.open(p).convert("RGB") for p in paths]
    if crop:
        images = [i.crop(crop) for i in images]
    columns = columns or len(images)
    rows = -(-len(images) // columns)
    tallest = max(i.height / i.width for i in images)

    if width is None:
        width = min(WIDEST, LIMIT // columns, int(LIMIT / (rows * tallest)))
    cell_h = int(width * tallest)

    sheet = Image.new("RGB", (columns * width, rows * cell_h), "white")
    for index, image in enumerate(images):
        scaled = image.resize((width, round(image.height * width / image.width)))
        sheet.paste(scaled, ((index % columns) * width, (index // columns) * cell_h))
    return sheet, width


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("images", nargs="+", type=Path)
    ap.add_argument("-o", "--out", type=Path, required=True)
    ap.add_argument("--columns", type=int, help="default: all on one row")
    ap.add_argument("--width", type=int, help="per image; default: as large as fits")
    ap.add_argument(
        "--crop",
        metavar="X1,Y1,X2,Y2",
        help="take this box out of every image first, in the images' own pixels",
    )
    args = ap.parse_args()

    crop = None
    if args.crop:
        got = [int(v) for v in args.crop.replace(" ", "").split(",")]
        if len(got) != 4:
            raise SystemExit("--crop wants four numbers: X1,Y1,X2,Y2")
        crop = tuple(got)

    sheet, width = build(args.images, args.columns, args.width, crop)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(args.out)
    note = "" if width >= LEGIBLE else "  (too small to read lettering)"
    cost = round(sheet.width * sheet.height / 750)
    print(f"{args.out}  {sheet.width}x{sheet.height}  {width}px each  ~{cost} tokens{note}")


if __name__ == "__main__":
    main()
