import PIL, sys
from PIL import features, ImageFont
print("platform", sys.platform, "| Pillow", PIL.__version__,
      "| raqm", features.check("raqm"))
f = ImageFont.truetype("fonts/iannnnnJPG/2005_iannnnnJPG.ttf", 100)
print("layout_engine", f.layout_engine)
for word in ["ที่", "เนี่ย", "กก", "สวัสดีครับ"]:
    parts = sum(f.getlength(c) for c in word)
    print(f"  {word}  whole={f.getlength(word):.1f}  sum-of-chars={parts:.1f}")
