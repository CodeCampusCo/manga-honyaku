import PIL, sys
from PIL import features, ImageFont
print("platform", sys.platform, "| Pillow", PIL.__version__)
print("freetype", features.version("freetype2"), "| raqm", features.check("raqm"))
f = ImageFont.truetype("fonts/iannnnnJPG/2005_iannnnnJPG.ttf", 100)
print("layout_engine", f.layout_engine)
for c in "ัิี่้ก฻":
    print(f"  U+{ord(c):04X} advance={f.getlength(c)}")
