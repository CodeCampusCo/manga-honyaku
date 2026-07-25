"""Run the RT-DETR detector alone and draw numbered boxes, colour-coded by class.

Prototypes the "code annotates, Claude reads the numbers" step and checks whether
free-floating text outside bubbles is detected at all.
"""

import sys

import cv2
import torch
from PIL import Image, ImageDraw, ImageFont
from transformers import RTDetrImageProcessor, RTDetrV2ForObjectDetection

from core.ml.model_manager import ModelType, get_model_manager
from core.ml.rtdetr_adapter import RTDetrYOLOAdapter

img_path = sys.argv[1]
out_path = sys.argv[2]
conf = float(sys.argv[3]) if len(sys.argv) > 3 else 0.35

COLORS = {"bubble": (0, 200, 0), "text_free": (255, 40, 40), "text_bubble": (60, 120, 255)}

mgr = get_model_manager()
path = mgr.model_paths[ModelType.RTDETR_CONJOINED_BUBBLE]
mgr._ensure_hf_repo(mgr.model_hf_repos[ModelType.RTDETR_CONJOINED_BUBBLE]["repo_id"], path)

cpu = torch.device("cpu")
model = RTDetrV2ForObjectDetection.from_pretrained(str(path)).to(cpu).eval()
adapter = RTDetrYOLOAdapter(
    model=model,
    processor=RTDetrImageProcessor.from_pretrained(str(path)),
    device=cpu,
    names=getattr(model.config, "id2label", None),
)

res = adapter(cv2.imread(img_path), conf=conf, device=cpu, imgsz=640)[0]
boxes = res.boxes.xyxy.tolist()
cls = [adapter.names[int(c)] for c in res.boxes.cls.tolist()]
scores = [float(s) for s in res.boxes.conf.tolist()]

img = Image.open(img_path).convert("RGB")
draw = ImageDraw.Draw(img)
font = ImageFont.truetype(
    "/Users/tama/app/MangaTranslator/fonts/Sarabun/Sarabun-Bold.ttf", 26
)

# Only the text classes carry words. Drawing the enclosing bubble too doubles
# the box count for no gain when the point is to read the text.
# "text_bubble" and "text_free" both start with 't', so an initial-letter prefix
# gives two different regions the same id.
PREFIX = {"text_bubble": "B", "text_free": "F"}

counters = {}
for box, name, score in sorted(zip(boxes, cls, scores), key=lambda t: (t[1], t[0][1])):
    if name not in PREFIX:
        continue
    counters[name] = counters.get(name, 0) + 1
    label = f"{PREFIX[name]}{counters[name]}"
    x1, y1, x2, y2 = [int(v) for v in box]
    colour = COLORS.get(name, (128, 128, 128))
    draw.rectangle([x1, y1, x2, y2], outline=colour, width=3)

    # The label must sit outside the box: inside, it covers the first character
    # of the very text this annotation exists to make readable.
    tw, th = draw.textbbox((0, 0), label, font=font)[2:]
    lx, ly = x1, y1 - th - 8
    if ly < 0:
        ly = y2 + 2
    if lx + tw + 8 > img.width:
        lx = img.width - tw - 8
    draw.rectangle([lx, ly, lx + tw + 8, ly + th + 6], fill=colour)
    draw.text((lx + 4, ly + 2), label, fill=(255, 255, 255), font=font)

img.save(out_path)

print(f"conf={conf}  total={len(boxes)}")
for name in sorted(set(cls)):
    print(f"  {name:12} {sum(1 for c in cls if c == name)}   colour={COLORS.get(name)}")
print("saved:", out_path)
