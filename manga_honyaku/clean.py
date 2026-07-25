"""Stage `clean`: erase the Japanese lettering and record each bubble's interior.

Writes work/<page>.clean.png and work/<page>.masks.png. Both are derived and can
be thrown away and rebuilt from raw/ at any time.

The upstream cleaner takes a segmentation mask per bubble, from either SAM or a
YOLO model. Excluding `ultralytics` took the YOLO one with it, and RT-DETR
returns boxes, not masks. Rather than add a segmentation model back, the
interior is recovered from the artwork: inside a detected bubble box, the
interior is simply the largest region of paper that the outline encloses.

Free-floating text is left alone. Most of it is sound effects, which the design
requires be left untouched, and the rest sits directly on artwork that only an
inpainting model could restore — a decision this stage does not need to make.

Derived from meangrinch/MangaTranslator (Apache-2.0); see NOTICE.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

# Bubble interiors are paper and everything drawn on them is ink. Nothing about
# that split is marginal, so a fixed threshold holds up better here than an
# adaptive one, which chases the screentone in the artwork behind the bubble.
PAPER = 200

# Regions the agent has ruled out. Erasing a declined region would leave a hole
# with nothing to put in it, and an effect drawn as lettering is artwork.
KEEP = {"sfx"}


def _touches_edge(stats: np.ndarray, i: int, h: int, w: int) -> bool:
    return (
        stats[i, cv2.CC_STAT_LEFT] == 0
        or stats[i, cv2.CC_STAT_TOP] == 0
        or stats[i, cv2.CC_STAT_LEFT] + stats[i, cv2.CC_STAT_WIDTH] == w
        or stats[i, cv2.CC_STAT_TOP] + stats[i, cv2.CC_STAT_HEIGHT] == h
    )


def interior(
    gray: np.ndarray, box: list[float], text_box: list[float]
) -> np.ndarray | None:
    """Boolean mask of the paper enclosed by one bubble outline, holes filled.

    Cropped to the bubble box, so a lobe of a conjoined bubble yields that lobe
    and not the whole joined interior.
    """
    x1, y1, x2, y2 = (int(v) for v in box)
    crop = gray[y1:y2, x1:x2]
    if crop.size == 0:
        return None

    paper = (crop > PAPER).astype(np.uint8)
    count, labels, stats, _ = cv2.connectedComponentsWithStats(paper, connectivity=4)
    if count < 2:
        return None

    # Neither position nor size identifies the interior on its own. A seed
    # walked out from the centre lands inside a letter, because the centre of a
    # bubble is where the lettering is and the counter of あ or ロ is paper too.
    # Size picks the paper outside the bubble whenever the box is loose. What
    # does hold is that the interior is the paper the text sits on, so take the
    # component overlapping the text box most.
    tx1, ty1, tx2, ty2 = (int(v) for v in text_box)
    window = labels[
        max(ty1 - y1, 0) : max(ty2 - y1, 0), max(tx1 - x1, 0) : max(tx2 - x1, 0)
    ]
    if window.size == 0:
        return None
    overlap = np.bincount(window.ravel(), minlength=count)
    overlap[0] = 0  # background is not a candidate
    if not overlap.any():
        return None
    region = labels == int(np.argmax(overlap))

    # The lettering sits in the holes of that component. Filling them is what
    # turns "the paper you can see" into "the whole inside of the bubble". A
    # hole is any part of the complement that does not reach the edge of the
    # box; flooding inward from a corner would fail on a bubble that reaches it.
    h, w = paper.shape
    ocount, olabels, ostats, _ = cv2.connectedComponentsWithStats(
        (~region).astype(np.uint8), connectivity=4
    )
    holes = np.isin(
        olabels,
        [i for i in range(1, ocount) if not _touches_edge(ostats, i, h, w)],
    )

    mask = np.zeros(gray.shape, bool)
    mask[y1:y2, x1:x2] = region | holes
    return mask


def lobe_for(region: dict, bubbles: list[list[float]]) -> list[float] | None:
    """The bubble box holding this region's text.

    Conjoined bubbles are detected one lobe at a time and the lobes overlap, so
    where several contain the text, the smallest is the lobe it belongs to.
    """
    x1, y1, x2, y2 = region["box"]
    cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
    holding = [
        b for b in bubbles if b[0] <= cx <= b[2] and b[1] <= cy <= b[3]
    ]
    if not holding:
        return None
    return min(holding, key=lambda b: (b[2] - b[0]) * (b[3] - b[1]))


def clean(page: Image.Image, data: dict) -> tuple[Image.Image, Image.Image]:
    art = np.asarray(page).copy()
    gray = np.asarray(page.convert("L"))
    masks = np.zeros(gray.shape, np.uint8)

    for index, region in enumerate(data["regions"], start=1):
        if region["detector_class"] != "text_bubble":
            continue
        if region.get("status") == "declined" or region.get("class") in KEEP:
            continue
        box = lobe_for(region, data.get("bubbles", []))
        if box is None:
            continue
        mask = interior(gray, box, region["box"])
        if mask is None:
            continue

        # Repaint with the bubble's own paper rather than white, so a bubble
        # that is toned or tinted does not come back as a white hole.
        paper = art[mask & (gray > PAPER)]
        art[mask] = np.median(paper, axis=0) if len(paper) else 255
        masks[mask] = index

    return Image.fromarray(art), Image.fromarray(masks, mode="L")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("pages", nargs="+", type=Path)
    ap.add_argument("--work", type=Path, default=Path("work"))
    args = ap.parse_args()

    for page in args.pages:
        data = json.loads((args.work / f"{page.stem}.json").read_text())
        cleaned, masks = clean(Image.open(page).convert("RGB"), data)
        cleaned.save(args.work / f"{page.stem}.clean.png")
        masks.save(args.work / f"{page.stem}.masks.png")
        print(f"{page.name}  {len(set(np.asarray(masks).flat)) - 1} bubbles cleaned")


if __name__ == "__main__":
    main()
