"""Stage `detect`: find text regions on a page and write work/<page>.json.

Geometry only. What each region says, who says it and in what order are the
agent's job, and the fields for them are left absent rather than guessed at.

Derived from meangrinch/MangaTranslator (Apache-2.0); see NOTICE.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

import torch
from PIL import Image
from transformers import RTDetrImageProcessor, RTDetrV2ForObjectDetection

# The weights are referenced, never vendored. Set this to a local directory to
# reuse a copy you already have instead of filling the Hugging Face cache again.
DETECTOR = os.environ.get(
    "MANGA_HONYAKU_DETECTOR", "ogkalu/comic-text-and-bubble-detector"
)

# RT-DETR's post-processing runs a float64 operation that the MPS backend does
# not implement, and the failure surfaces as an empty result rather than an
# error. The model is small and runs once per page, so it is pinned to CPU.
DEVICE = torch.device("cpu")

# Region ids carry a per-class prefix. Deriving the prefix from the class name
# would give text_bubble and text_free the same letter and collide.
PREFIX = {"text_bubble": "B", "text_free": "F"}


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
    """Return [(class_name, [x1, y1, x2, y2], score)] for every class, unsorted."""
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


def page_file(page: Path, image: Image.Image, found, conf: float, imgsz: int) -> dict:
    """Build the page file.

    Only text-carrying detections become regions; a `bubble` detection carries
    no words and numbering them alongside the text would double the ids the
    agent has to read. They are still kept, unnumbered, because `clean` needs
    the outline to find a bubble's interior and detect is the only stage that
    is allowed to load the model.
    """
    text = [f for f in found if f[0] in PREFIX]
    text.sort(key=lambda f: (f[0], f[1][1]))  # class, then down the page

    counters: dict[str, int] = {}
    regions = []
    for name, box, score in text:
        counters[name] = counters.get(name, 0) + 1
        regions.append(
            {
                "id": f"{PREFIX[name]}{counters[name]}",
                "box": box,
                "detector_class": name,
                "score": score,
            }
        )

    return {
        "version": 1,
        "page": page.name,
        "img_width": image.width,
        "img_height": image.height,
        "detector": {"model": DETECTOR, "conf": conf, "imgsz": imgsz},
        "regions": regions,
        "bubbles": [f[1] for f in found if f[0] == "bubble"],
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("pages", nargs="+", type=Path)
    ap.add_argument("--work", type=Path, default=Path("work"))
    ap.add_argument("--conf", type=float, default=0.35)
    ap.add_argument("--imgsz", type=int, default=640)
    ap.add_argument(
        "--force",
        action="store_true",
        help="re-detect pages that already have a page file, discarding the "
        "reading order, speakers and translations written into it",
    )
    args = ap.parse_args()

    args.work.mkdir(parents=True, exist_ok=True)
    model, processor = load_detector()

    for page in args.pages:
        out = args.work / f"{page.stem}.json"
        # The page file is the one artifact that is not derived: everything the
        # agent works out about the page is written into it, and detect would
        # otherwise overwrite that on the next run.
        if out.exists() and not args.force:
            print(f"{page.name}  {out} exists, skipping")
            continue

        image = Image.open(page).convert("RGB")
        found = detect(image, model, processor, conf=args.conf, imgsz=args.imgsz)
        data = page_file(page, image, found, args.conf, args.imgsz)
        out.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")

        counts = {c: sum(1 for f in found if f[0] == c) for c in sorted({f[0] for f in found})}
        print(f"{page.name}  {out}  {counts}")


if __name__ == "__main__":
    main()
