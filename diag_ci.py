from PIL import ImageFont
f = ImageFont.truetype("fonts/iannnnnJPG/2005_iannnnnJPG.ttf", 100)
base = "ก"; alone = f.getlength(base)
print(f"base alone = {alone!r}")
for c in "ัิีึื็์ํ๎่้":
    with_mark = f.getlength(base + c)
    print(f"  U+{ord(c):04X}  base+mark={with_mark!r}  delta={with_mark - alone!r}")
