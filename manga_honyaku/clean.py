"""Stage `clean`: erase the Japanese lettering and record each bubble's interior.

Writes build/<id>.clean.png and build/<id>.masks.png. Both are derived and can
be thrown away and rebuilt from the scans at any time.

Reads pages/<id>.agent.json, which by this point says which regions are speech
and which are artwork. The detector's own file is not consulted.

RT-DETR returns boxes, not masks, and nothing here segments. The interior is
recovered from the artwork instead: inside a detected bubble box, it is the
largest region of paper that the outline encloses.

Free-floating text is painted out as a white rectangle. There is no outline to
follow and no way to know what the artwork behind it looked like, so nothing
subtler is available without an inpainting model. On a page margin the result is
invisible; over drawn artwork it is a white patch, and that is the trade.

Which free-floating regions get erased is the agent's call, not this stage's: a
sound effect is artwork and must survive, and only a reader can tell one from a
line of unbubbled speech. A region with no role yet is left alone.

Derived from meangrinch/MangaTranslator (Apache-2.0); see NOTICE.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

from manga_honyaku.page import Series

# Bubble interiors are paper and everything drawn on them is ink. Nothing about
# that split is marginal, so a fixed threshold holds up better here than an
# adaptive one, which chases the screentone in the artwork behind the bubble.
PAPER = 200

# Roles that are recorded but never painted over. An effect drawn as lettering is
# artwork, and so is a sign or a phone screen — what it says reaches the reader
# through the translation, not by overwriting the drawing. A declined region is
# left for a different reason: erasing it would leave a hole with nothing to put
# in it.
KEEP = {"sfx", "image_text"}


def _touches_edge(stats: np.ndarray, i: int, h: int, w: int) -> bool:
    return (
        stats[i, cv2.CC_STAT_LEFT] == 0
        or stats[i, cv2.CC_STAT_TOP] == 0
        or stats[i, cv2.CC_STAT_LEFT] + stats[i, cv2.CC_STAT_WIDTH] == w
        or stats[i, cv2.CC_STAT_TOP] + stats[i, cv2.CC_STAT_HEIGHT] == h
    )


def joined(regions: list[dict]) -> list[list[dict]]:
    """Regions whose outlines overlap, gathered into groups.

    Conjoined bubbles are detected one lobe at a time and their boxes overlap,
    so the lobes have to be handled together to be separated at all.
    """
    groups: list[list[dict]] = []
    for region in regions:
        box = region["bubble"]
        touching = [
            g
            for g in groups
            if any(
                box[0] < o["bubble"][2]
                and o["bubble"][0] < box[2]
                and box[1] < o["bubble"][3]
                and o["bubble"][1] < box[3]
                for o in g
            )
        ]
        merged = [region] + [r for g in touching for r in g]
        groups = [g for g in groups if g not in touching] + [merged]
    return groups


def interiors(gray: np.ndarray, group: list[dict]) -> dict[str, np.ndarray]:
    """One interior mask per region, sharing out an interior the lobes hold jointly.

    Cropping each lobe to its own bubble box cuts the shared interior along a box
    edge — a straight line nowhere near the waist where the lobes actually meet.
    One lobe takes a slice of the other, and text centred in what is left of it
    sits off-centre in the bubble a reader sees.

    So the interior is found once for the whole group, then shared out by
    proximity: every pixel goes to the region whose text sits nearest it. For a
    lone bubble the group is one region and this is the interior entire.
    """
    x1 = int(min(r["bubble"][0] for r in group))
    y1 = int(min(r["bubble"][1] for r in group))
    x2 = int(max(r["bubble"][2] for r in group))
    y2 = int(max(r["bubble"][3] for r in group))
    crop = gray[y1:y2, x1:x2]
    if crop.size == 0:
        return {}

    def enclosed(paper: np.ndarray) -> np.ndarray | None:
        count, labels, _, _ = cv2.connectedComponentsWithStats(paper, connectivity=4)
        if count < 2:
            return None

        # Each region names the component its own text sits on; together they
        # are the interior the group occupies, whether that is one lobe or three.
        chosen = set()
        for region in group:
            tx1, ty1, tx2, ty2 = (int(v) for v in region["box"])
            window = labels[
                max(ty1 - y1, 0) : max(ty2 - y1, 0), max(tx1 - x1, 0) : max(tx2 - x1, 0)
            ]
            if window.size == 0:
                continue
            overlap = np.bincount(window.ravel(), minlength=count)
            overlap[0] = 0
            if overlap.any():
                chosen.add(int(np.argmax(overlap)))
        if not chosen:
            return None

        # The lettering sits in the holes of that shape. Filling them is what
        # turns "the paper you can see" into "the whole inside of the bubble". A
        # hole is any part of the complement that does not reach the crop edge.
        shape = np.isin(labels, list(chosen))
        h, w = paper.shape
        ocount, olabels, ostats, _ = cv2.connectedComponentsWithStats(
            (~shape).astype(np.uint8), connectivity=4
        )
        holes = np.isin(
            olabels, [i for i in range(1, ocount) if not _touches_edge(ostats, i, h, w)]
        )
        return shape | holes

    paper = (crop > PAPER).astype(np.uint8)
    combined = enclosed(paper)
    if combined is None:
        return {}

    # A bubble drawn over a screentone is paper with ink ruled through it, so the
    # threshold hands back the tone's gaps as separate stripes, one stripe wins
    # the overlap, and the text is set into a sliver of the bubble. Closing joins
    # the stripes; eroding by the same amount gives back the outline the close
    # ate. It is a fallback rather than the rule because the close also bridges a
    # thin outline elsewhere and floods the artwork around the bubble.
    #
    # A lone bubble's outline box is drawn around the bubble, so its interior
    # fills most of it; anything near half is not an interior. A group's box has
    # corners no lobe occupies and is legitimately this empty, so it is left out.
    if len(group) == 1 and combined.sum() < 0.5 * combined.size:
        kernel = np.ones((3, 3), np.uint8)
        wider = enclosed(cv2.morphologyEx(paper, cv2.MORPH_CLOSE, kernel))
        if wider is not None:
            wider = cv2.erode(wider.astype(np.uint8), kernel).astype(bool)
            if wider.sum() > combined.sum():
                combined = wider

    # Each lobe keeps what its own outline encloses. The detector drew a box per
    # lobe and those boxes overlap only in the waist, so the only pixels in
    # dispute are the ones in that overlap, and they go to the nearer lobe.
    rows, cols = np.mgrid[y1:y2, x1:x2]
    # Ink outside the lettering is artwork. A balloon drawn as a ring of separate
    # ticks encloses nothing, so the paper runs straight out of it and the ticks
    # stand in the middle of what the flood claims; repainting the claim takes
    # the balloon's edge with it. Painting paper over paper costs nothing, so the
    # claim keeps all the paper it found and gives back every dark pixel that is
    # not where the lettering sat. A glyph that overruns its box is the same
    # trade the box already makes, and `audit` reports what it leaves.
    lettering = np.zeros_like(combined)
    for region in group:
        lx1, ly1, lx2, ly2 = (int(v) for v in region["box"])
        lettering[max(ly1 - y1, 0) : max(ly2 - y1, 0), max(lx1 - x1, 0) : max(lx2 - x1, 0)] = True
    combined = combined & (paper.astype(bool) | lettering)

    owned = []
    for region in group:
        bx1, by1, bx2, by2 = region["bubble"]
        inside = (cols >= bx1) & (cols < bx2) & (rows >= by1) & (rows < by2)
        cy, cx = (by1 + by2) / 2, (bx1 + bx2) / 2
        owned.append((inside & combined, (rows - cy) ** 2 + (cols - cx) ** 2))

    claims = np.stack([o for o, _ in owned])
    farness = np.stack([np.where(o, d, np.inf) for o, d in owned])
    winner = np.argmin(farness, axis=0)

    out = {}
    for i, region in enumerate(group):
        mask = np.zeros(gray.shape, bool)
        mask[y1:y2, x1:x2] = claims[i] & (winner == i)
        if mask.any():
            out[region["id"]] = mask
    return out


def free_mask(shape: tuple[int, int], box: list[float]) -> np.ndarray:
    """The box itself, not a pixel more.

    No margin: these boxes are cropped tight enough that a chapter title's box
    ends on the row where the panel's top rule begins, so any margin at all cuts
    the rule. `ocr.py` does grow its crop, where a clipped glyph costs more than
    the extra pixels.
    """
    x1, y1, x2, y2 = box
    mask = np.zeros(shape, bool)
    mask[int(y1) : int(y2), int(x1) : int(x2)] = True
    return mask


def clean(page: Image.Image, data: dict) -> tuple[Image.Image, Image.Image]:
    art = np.asarray(page).copy()
    gray = np.asarray(page.convert("L"))
    masks = np.zeros(gray.shape, np.uint8)

    # Whether there is an outline to follow is the only question here, and
    # `bubble` answers it directly. `placement` is not consulted: it records what
    # the model saw, so that its disagreement with the agent stays visible, not
    # so that anything branches on it.
    wanted = [
        r
        for r in data["regions"]
        if r.get("role")
        and r.get("role") not in KEEP
        and r.get("status") != "declined"
    ]
    found: dict[str, np.ndarray] = {}
    for group in joined([r for r in wanted if r.get("bubble")]):
        found.update(interiors(gray, group))

    for index, region in enumerate(data["regions"], start=1):
        if region not in wanted:
            continue

        mask = found.get(region["id"])
        if mask is not None:
            # Repaint with the bubble's own paper rather than white, so a bubble
            # that is toned or tinted does not come back as a white hole.
            paper = art[mask & (gray > PAPER)]
            art[mask] = np.median(paper, axis=0) if len(paper) else 255
        else:
            # No outline, or none that could be traced. Painting the box out is
            # cruder than following a curve, but a region the agent asked to
            # have erased is never quietly left with the Japanese still in it.
            mask = free_mask(gray.shape, region["box"])
            art[mask] = 255

        masks[mask] = index

    return Image.fromarray(art), Image.fromarray(masks, mode="L")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("series", type=Path, help="a work's directory under series/")
    ap.add_argument("pages", nargs="*", help="page ids; a directory; none for all")
    args = ap.parse_args()

    work = Series(args.series)
    for page in work.ids(args.pages):
        data = json.loads(work.agent(page).read_text())
        cleaned, masks = clean(Image.open(work.scan(page)).convert("RGB"), data)
        cleaned.save(work.derived(page, "clean.png"))
        masks.save(work.derived(page, "masks.png"))
        print(f"{page}  {len(set(np.asarray(masks).flat)) - 1} bubbles cleaned")


if __name__ == "__main__":
    main()
