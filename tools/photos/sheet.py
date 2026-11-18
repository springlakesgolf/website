"""contact sheets: python sheet.py name cols thumbw perpage listfile  -> sheets/name-N.jpg + sheets/name.map"""
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageOps, ImageFile
ImageFile.LOAD_TRUNCATED_IMAGES = True
name, cols, tw, per = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4])
files = [l.strip() for l in open(sys.argv[5], encoding="utf-8") if l.strip()]
th = int(tw * 2 / 3); pad = 4; lab = 14; errs = 0
Path("sheets").mkdir(exist_ok=True)
open(f"sheets/{name}.map", "w", encoding="utf-8").write("\n".join(f"{i+1}\t{f}" for i, f in enumerate(files)))
for p in range(0, len(files), per):
    chunk = files[p:p+per]; rows = (len(chunk) + cols - 1) // cols
    sheet = Image.new("RGB", (cols*(tw+pad)+pad, rows*(th+lab+pad)+pad), "white"); d = ImageDraw.Draw(sheet)
    for j, f in enumerate(chunk):
        i = p + j
        try:
            im = Image.open(f); im.draft("RGB", (tw*2, th*2)); im = ImageOps.exif_transpose(im); im.thumbnail((tw, th))
        except Exception as e:
            errs += 1; continue
        x = pad + (j % cols)*(tw+pad); y = pad + (j // cols)*(th+lab+pad)
        sheet.paste(im, (x + (tw-im.width)//2, y + (th-im.height)//2))
        d.text((x, y+th+1), f"{i+1} {Path(f).stem[-20:]}", fill="black")
    o = f"sheets/{name}-{p//per+1}.jpg"; sheet.save(o, quality=58, optimize=True); print(o, sheet.size)
print("files", len(files), "errors", errs)
