"""Stage `annotate`: draw the region ids from work/<page>.detector.json onto a copy.

This is what the agent reads alongside the raw page, so it must not obscure the
thing it is annotating.

Derived from meangrinch/MangaTranslator (Apache-2.0); see NOTICE.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from manga_honyaku.page import detector_path

COLOURS = {"text_bubble": (60, 120, 255), "text_free": (255, 40, 40)}


def annotate(image: Image.Image, regions: list[dict]) -> Image.Image:
    image = image.copy()
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default(size=max(16, round(image.width / 44)))

    for region in regions:
        x1, y1, x2, y2 = (int(v) for v in region["box"])
        colour = COLOURS.get(region["detector_class"], (128, 128, 128))
        draw.rectangle([x1, y1, x2, y2], outline=colour, width=3)

        # The label sits outside the box. Drawn inside it covers the first
        # character of the very text the annotation exists to make readable,
        # and nothing signals the error — the agent just reads it wrong.
        tw, th = draw.textbbox((0, 0), region["id"], font=font)[2:]
        lx, ly = x1, y1 - th - 8
        if ly < 0:
            ly = y2 + 2
        if lx + tw + 8 > image.width:
            lx = image.width - tw - 8
        draw.rectangle([lx, ly, lx + tw + 8, ly + th + 6], fill=colour)
        draw.text((lx + 4, ly + 2), region["id"], fill=(255, 255, 255), font=font)

    return image


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("pages", nargs="+", type=Path)
    ap.add_argument("--work", type=Path, default=Path("work"))
    args = ap.parse_args()

    for page in args.pages:
        data = json.loads(detector_path(args.work, page.stem).read_text())
        out = args.work / f"{page.stem}.boxes.png"
        annotate(Image.open(page).convert("RGB"), data["regions"]).save(out)
        print(f"{page.name}  {out}  {len(data['regions'])} regions")


if __name__ == "__main__":
    main()
