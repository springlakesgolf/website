"""Export the picks in manifest.py from the photo drive to WebP in tools/photos/img/.

    python tools/photos/export.py            export anything missing
    python tools/photos/export.py --force    export everything again
    python tools/photos/export.py id [id..]  export just those ids again

Needs the drive (E:/Spring Lakes Photos) and Pillow. The exported files are committed, so a
rebuild never needs the drive.
"""
import io, sys
from pathlib import Path
from PIL import Image, ImageOps, ImageFile, ImageCms
from manifest import PHOTOS, name

ImageFile.LOAD_TRUNCATED_IMAGES = True
Image.MAX_IMAGE_PIXELS = None
DRIVE = Path("E:/Spring Lakes Photos/01 By Event")
IMG = Path(__file__).resolve().parent / "img"
SIZES = {"": (2000, 400), "m": (1200, 190), "t": (800, 100)}  # long edge px, max KB

def index():
    idx = {}
    for f in DRIVE.rglob("*.jpg"):
        if "Sneak Peak" in str(f) and f.stem in idx: continue
        idx.setdefault(f.stem, f)
    return idx

def srgb(im):
    icc = im.info.get("icc_profile")
    if icc:
        try:
            src = ImageCms.ImageCmsProfile(io.BytesIO(icc))
            if "sRGB" not in ImageCms.getProfileDescription(src):
                im = ImageCms.profileToProfile(im, src, ImageCms.createProfile("sRGB"), outputMode="RGB")
        except Exception:
            pass
    return im.convert("RGB")

def export(pid, idx):
    stem, crop, _ = PHOTOS[pid]
    if "|" in stem:  # "event folder words|stem" when two events share a file number
        hint, stem = stem.split("|")
        src = next(f for f in DRIVE.rglob(stem + ".jpg") if hint in str(f))
    else:
        src = idx[stem]
    im = srgb(ImageOps.exif_transpose(Image.open(src)))
    if crop:
        w, h = im.size
        im = im.crop((int(crop[0]*w), int(crop[1]*h), int(crop[2]*w), int(crop[3]*h)))
    for size, (edge, kb) in SIZES.items():
        t = im.copy(); t.thumbnail((edge, edge), Image.LANCZOS)
        for q in range(84, 30, -4):
            buf = io.BytesIO(); t.save(buf, "WEBP", quality=q, method=6)
            if buf.tell() <= kb * 1024: break
        (IMG / name(pid, size)).write_bytes(buf.getvalue())
        print(f"{name(pid, size):44} {t.size[0]}x{t.size[1]}  q{q}  {buf.tell()//1024} KB")

if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    IMG.mkdir(exist_ok=True)
    idx = index()
    for pid in (args or PHOTOS):
        if args or "--force" in sys.argv or not (IMG / name(pid)).exists():
            export(pid, idx)
