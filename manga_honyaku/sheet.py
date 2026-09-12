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

`--rtl` puts the first image named on the right. Without it a spread comes out
mirrored and nothing says so, because the panels still make sense one at a time —
so which way round a sheet was built is printed either way.

Given a work's directory it takes page ids, like every other tool here, and
`--region` crops a named region instead of a box of numbers. Without those a page
is named by writing `build/<ch>/<pp>.boxes.png` out by hand, and reading a region
off the sheet means converting sheet pixels back to page pixels — which is where
two reading-order errors in one chapter came from.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from PIL import Image

from manga_honyaku.page import Series

# Beyond this the reader resamples, so pixels past it are paid for and thrown
# away.
LIMIT = 1568

# The most any one image is worth. Past this a page stops getting easier to read
# and goes on getting more expensive, quadratically.
WIDEST = 800

# Measured on this project's pages: at 380px wide a bubble's Thai is still
# readable, and panel layout stays clear well below that.
LEGIBLE = 380

# What a region crop shows beside the region, as a share of its own size. A box
# on its own answers what it says; the question being asked of a crop is usually
# which panel it sits in.
CONTEXT = 1.0

SHOWN = {
    "boxes": lambda work, page: work.derived(page, "boxes.png"),
    "raw": lambda work, page: work.scan(page),
    "out": lambda work, page: work.rendered(page),
}


def pages(work: Series, ids: list[str], show: str) -> list[Path]:
    """The image each page id names, falling back to the scan where `annotate`
    has not run."""
    found = []
    for page in ids:
        path = SHOWN[show](work, page)
        if not path.exists() and show == "boxes":
            path = work.scan(page)
        if not path.exists():
            raise SystemExit(f"no {show} image for {page}")
        found.append(path)
    return found


def around(work: Series, page: str, rid: str) -> tuple[int, int, int, int]:
    """The box of a named region, grown to show what it sits in."""
    data = json.loads(work.agent(page).read_text())
    for region in data["regions"]:
        if region["id"] == rid:
            x1, y1, x2, y2 = region["box"]
            wide, tall = (x2 - x1) * CONTEXT, (y2 - y1) * CONTEXT
            return (
                int(max(x1 - wide, 0)),
                int(max(y1 - tall, 0)),
                int(min(x2 + wide, data["img_width"])),
                int(min(y2 + tall, data["img_height"])),
            )
    raise SystemExit(f"{page} has no region {rid}")


def build(
    paths: list[Path],
    columns: int | None = None,
    width: int | None = None,
    crop=None,
    rtl: bool = False,
):
    """One box taken out of every image, or a list with one box per image."""
    images = [Image.open(p).convert("RGB") for p in paths]
    boxes = crop if isinstance(crop, list) else [crop] * len(images)
    images = [i.crop(b) if b else i for i, b in zip(images, boxes)]
    columns = columns or len(images)
    rows = -(-len(images) // columns)
    tallest = max(i.height / i.width for i in images)

    if width is None:
        width = min(WIDEST, LIMIT // columns, int(LIMIT / (rows * tallest)))
    cell_h = int(width * tallest)

    sheet = Image.new("RGB", (columns * width, rows * cell_h), "white")
    for index, image in enumerate(images):
        scaled = image.resize((width, round(image.height * width / image.width)))
        column = index % columns
        if rtl:
            column = columns - 1 - column
        sheet.paste(scaled, (column * width, (index // columns) * cell_h))
    return sheet, width


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument(
        "images",
        nargs="+",
        type=Path,
        metavar="IMAGE | series/<work> PAGE...",
    )
    ap.add_argument("-o", "--out", type=Path, required=True)
    ap.add_argument("--columns", type=int, help="default: all on one row")
    ap.add_argument("--width", type=int, help="per image; default: as large as fits")
    ap.add_argument(
        "--crop",
        metavar="X1,Y1,X2,Y2",
        help="take this box out of every image first, in the images' own pixels",
    )
    ap.add_argument(
        "--region",
        nargs="+",
        metavar="ID | PAGE:ID",
        help="crop these regions and their surrounds, one per cell",
    )
    ap.add_argument(
        "--show",
        choices=sorted(SHOWN),
        default="boxes",
        help="which image a page id names; default the annotated page",
    )
    ap.add_argument(
        "--rtl",
        action="store_true",
        help="lay them out right to left, so the first one named is on the right",
    )
    args = ap.parse_args()

    work = None
    images = args.images
    ids: list[str] = []
    if images[0].is_dir():
        work = Series(images[0])
        ids = [str(p) for p in images[1:]]

    crop = None
    if args.region:
        if work is None:
            raise SystemExit("--region wants a work")
        # Each region names its own page, or takes the one page given. Ten boxes
        # off ten pages is one sheet, which is what the candidate list asks for.
        wanted = [
            spec.split(":", 1) if ":" in spec else (ids[0] if len(ids) == 1 else None, spec)
            for spec in args.region
        ]
        if any(page is None for page, _ in wanted):
            raise SystemExit("name the page: --region 09/01:F1, or give one page id")
        ids = [page for page, _ in wanted]
        crop = [around(work, page, rid) for page, rid in wanted]
    elif args.crop:
        got = [int(v) for v in args.crop.replace(" ", "").split(",")]
        if len(got) != 4:
            raise SystemExit("--crop wants four numbers: X1,Y1,X2,Y2")
        crop = tuple(got)

    if work is not None:
        images = pages(work, ids or work.ids([]), args.show)

    sheet, width = build(images, args.columns, args.width, crop, args.rtl)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(args.out)
    note = "" if width >= LEGIBLE else "  (too small to read lettering)"
    cost = round(sheet.width * sheet.height / 750)
    order = ""
    if len(images) > 1:
        order = "  right to left" if args.rtl else "  left to right"
    # The scale is printed so that a position read off the sheet converts back
    # without the conversion being worked out first.
    # The scale converts a position read off the sheet back to the page, so it is
    # printed only where there is one of it: cells cropped to different shapes
    # each have their own.
    boxes = crop if isinstance(crop, list) else [crop] * len(images)
    where = ""
    if len(set(boxes)) == 1:
        box = boxes[0]
        across = (box[2] - box[0]) if box else Image.open(images[0]).width
        where = f"  {width / across:.3f}x" + (f" from {box[0]},{box[1]}" if box else "")
    print(
        f"{args.out}  {sheet.width}x{sheet.height}  {width}px each"
        f"  ~{cost} tokens{order}{note}{where}"
    )


if __name__ == "__main__":
    main()
