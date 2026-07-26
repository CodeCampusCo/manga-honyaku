"""Stage `detect`: find text regions on a page and write work/<page>.detector.json.

Geometry only. What each region says, who says it and in what order are the
agent's job, and the fields for them are left absent rather than guessed at.

Derived from meangrinch/MangaTranslator (Apache-2.0); see NOTICE.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import torch
from PIL import Image
from transformers import RTDetrImageProcessor, RTDetrV2ForObjectDetection

from manga_honyaku.page import detector_path

# The weights are referenced, never vendored. Set this to a local directory to
# reuse a copy you already have instead of filling the Hugging Face cache again.
DETECTOR = os.environ.get(
    "MANGA_HONYAKU_DETECTOR", "ogkalu/comic-text-and-bubble-detector"
)

# RT-DETR's post-processing runs a float64 operation that the MPS backend does
# not implement, and the failure surfaces as an empty result rather than an
# error. The model is small and runs once per page, so it is pinned to CPU.
DEVICE = torch.device("cpu")

# The detector's two text labels, and what each one is recorded as. `placement`
# answers where the text sits, which is the only question the model is in a
# position to answer about it; what the text is for is the agent's `role`.
#
# The id prefix is spelled out rather than taken from the label's first letter,
# which would give text_bubble and text_free the same one and collide.
TEXT = {
    "text_bubble": {"prefix": "B", "placement": "bubble"},
    "text_free": {"prefix": "F", "placement": "free"},
}


def warn(message: str) -> None:
    print(f"warning: {message}", file=sys.stderr)


def _iou(a: list[float], b: list[float]) -> float:
    x1, y1 = max(a[0], b[0]), max(a[1], b[1])
    x2, y2 = min(a[2], b[2]), min(a[3], b[3])
    if x2 <= x1 or y2 <= y1:
        return 0.0
    overlap = (x2 - x1) * (y2 - y1)
    areas = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1])
    return overlap / (areas - overlap)


def dedupe(found, threshold: float = 0.5):
    """Keep the highest-scoring box where several cover the same thing.

    RT-DETR does not need NMS as a rule, and over a chapter of 227 regions only
    one thing produced duplicates: a panel edge of screentone, whose dot lattice
    read as a column of vertical text and returned five near-identical boxes at
    up to 0.95 IoU. No pair of genuine regions came close to the threshold —
    adjacent lobes of a conjoined bubble overlap, but nothing like this much.
    """
    kept: list = []
    for region in sorted(found, key=lambda f: f[2], reverse=True):
        if not any(
            k[0] == region[0] and _iou(k[1], region[1]) > threshold for k in kept
        ):
            kept.append(region)
    return kept


def load_detector():
    model = RTDetrV2ForObjectDetection.from_pretrained(DETECTOR).to(DEVICE).eval()
    processor = RTDetrImageProcessor.from_pretrained(DETECTOR)
    return model, processor


def detect(image: Image.Image, model, processor, conf: float = 0.35, imgsz: int = 640):
    """Return [(label, [x1, y1, x2, y2], score)] for every detection, unsorted."""
    inputs = processor(
        images=image,
        return_tensors="pt",
        size={"height": imgsz, "width": imgsz},
    )
    inputs = {k: v.to(DEVICE) for k, v in inputs.items()}
    with torch.inference_mode():
        outputs = model(**inputs)
    result = processor.post_process_object_detection(
        outputs,
        threshold=conf,
        target_sizes=[(image.height, image.width)],
    )[0]

    names = model.config.id2label
    w, h = image.width, image.height
    found = [
        (
            names[int(label)],
            # Boxes run past the edge of the page — clamp here so that no later
            # stage has to crop or mask against a negative coordinate.
            [
                round(min(max(v, 0.0), limit), 1)
                for v, limit in zip(box.tolist(), (w, h, w, h))
            ],
            round(float(score), 3),
        )
        for box, score, label in zip(
            result["boxes"], result["scores"], result["labels"]
        )
    ]
    return dedupe(found)


def resolve_bubble(box: list[float], bubbles: list[list[float]]):
    """The bubble box enclosing this text, or None if no bubble does.

    Conjoined bubbles are detected one lobe at a time and the lobes overlap, so
    where several enclose the text, the smallest is the lobe it sits in.
    """
    cx, cy = (box[0] + box[2]) / 2, (box[1] + box[3]) / 2
    holding = [b for b in bubbles if b[0] <= cx <= b[2] and b[1] <= cy <= b[3]]
    if not holding:
        return None
    return min(holding, key=lambda b: (b[2] - b[0]) * (b[3] - b[1]))


def page_file(page: Path, image: Image.Image, found, conf: float, imgsz: int) -> dict:
    """Build the page file.

    Only text-carrying detections become regions; a `bubble` detection carries
    no words, and numbering them alongside the text would double the ids the
    agent has to read. Each in-bubble region absorbs its own outline instead, so
    a region describes itself completely and no later stage repeats this match.

    The three ways the match can come out wrong are all reported here. Every one
    of them would otherwise surface two stages later as a bubble whose text was
    quietly left in place.
    """
    bubbles = [f[1] for f in found if f[0] == "bubble"]
    text = [f for f in found if f[0] in TEXT]
    text.sort(key=lambda f: (f[0], f[1][1]))  # placement, then down the page

    counters: dict[str, int] = {}
    regions = []
    holders: dict[tuple, list[str]] = {}
    for name, box, score in text:
        counters[name] = counters.get(name, 0) + 1
        region = {
            "id": f"{TEXT[name]['prefix']}{counters[name]}",
            "box": box,
            "placement": TEXT[name]["placement"],
            "score": score,
        }
        if name == "text_bubble":
            bubble = resolve_bubble(box, bubbles)
            if bubble is None:
                warn(f"{page.name} {region['id']}: in a bubble that was not detected")
            else:
                region["bubble"] = bubble
                holders.setdefault(tuple(bubble), []).append(region["id"])
        regions.append(region)

    for bubble, ids in holders.items():
        if len(ids) > 1:
            warn(f"{page.name} {', '.join(ids)}: share one bubble; masks will collide")
    for bubble in bubbles:
        if tuple(bubble) not in holders:
            warn(f"{page.name}: bubble at {[int(v) for v in bubble]} holds no text")

    return {
        "version": 1,
        "page": page.name,
        "img_width": image.width,
        "img_height": image.height,
        "detector": {"model": DETECTOR, "conf": conf, "imgsz": imgsz},
        "regions": regions,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("pages", nargs="+", type=Path)
    ap.add_argument("--work", type=Path, default=Path("work"))
    ap.add_argument("--conf", type=float, default=0.35)
    ap.add_argument("--imgsz", type=int, default=640)
    args = ap.parse_args()

    args.work.mkdir(parents=True, exist_ok=True)
    model, processor = load_detector()

    for page in args.pages:
        # Overwriting is safe: this file holds nothing but detector output. What
        # the agent works out lives in <page>.agent.json and is never written
        # here — see page.py for why they are separate.
        out = detector_path(args.work, page.stem)
        image = Image.open(page).convert("RGB")
        found = detect(image, model, processor, conf=args.conf, imgsz=args.imgsz)
        data = page_file(page, image, found, args.conf, args.imgsz)
        out.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")

        counts = {c: sum(1 for f in found if f[0] == c) for c in sorted({f[0] for f in found})}
        print(f"{page.name}  {out}  {counts}")


if __name__ == "__main__":
    main()
