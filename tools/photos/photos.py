"""Put the 2026 photos (tools/photos/img) on the built pages.

tools/build.py calls install(), apply(), css() and prune(), so a rebuild keeps the photos even
though the June source folder still has the old ones. Run on its own, it applies the same thing
to the pages already built in this checkout (the June source folder is on the Mac only):

    python tools/photos/photos.py

To change a photo: edit SLOTS or the gallery lists below (ids come from manifest.py), then run
this file or rebuild. To add a photo: add it to manifest.py, run export.py, then use its id here.
"""
import html, re, shutil, struct, sys
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from manifest import PHOTOS, name

IMG = HERE / "img"

HERO = "A"     # home page hero (Cullen picks): A morning ponds, B golden sun flare, C wide over the property, D dusk
GALLERY = "C"  # course gallery layout (Cullen picks): A masonry, B editorial grid, C three sections

# id, desktop object-position, phone object-position
HEROES = {
    "A": ("morning-ponds", "50% 22%", "36% 50%"),
    "B": ("golden-flare", "50% 8%", "34% 50%"),
    "C": ("property-wide", "50% 62%", "58% 50%"),
    "D": ("dusk-fairway", "50% 78%", "52% 50%"),
}

def slots(hero):
    """page folder -> [(old image file in the built page, photo id, size, alt or None, desktop position, phone position)]
    size "" is the 2000 px file (page heroes), "m" the 1200 px file (cards and figures).
    alt None uses the photo's own alt text from manifest.py."""
    h = HEROES[hero]
    golf = "morning-ponds" if hero == "C" else "property-wide"  # never the same aerial on home and golf
    return {
        "": [
            ("hero-aerial.jpg", h[0], "", None, h[1], h[2]),
            ("g18.webp", "island-green", "m", None, "50% 55%", "50% 55%"),
            ("course-east.webp", "green-big-sky", "m", None, "50% 70%", "50% 70%"),
            ("g25.webp", "golden-fairways", "m", None, "50% 50%", "50% 50%"),
            ("g05.webp", "chip-shot", "m", None, "60% 45%", "60% 45%"),
            ("g26.webp", "bunker-blue-sky", "m", None, "50% 55%", "50% 55%"),
        ],
        "golf": [
            ("golf-aerial.jpg", golf, "", None, "50% 55%" if golf == "property-wide" else "50% 30%", "56% 50%" if golf == "property-wide" else "36% 50%"),
            ("course-east.webp", "green-big-sky", "m", None, "50% 70%", "50% 70%"),
        ],
        "golf-academy": [("g05.webp", "bunker-shot", "", None, "50% 47%", "42% 50%")],
        "golf-camps": [("g26.webp", "bunker-blue-sky", "", None, "50% 60%", "30% 50%")],
        "memberships": [("g15.webp", "clubhouse-green", "", None, "50% 42%", "52% 50%")],
        "contact-us": [("g04.webp", "clubhouse-aerial", "", None, "50% 55%", "58% 50%")],
        "food-beverage": [
            ("g25.webp", "clubhouse-fountain", "", None, "50% 35%", "8% 50%"),
            ("clubhouse.jpg", "clubhouse-gardens", "m", None, "60% 50%", "60% 50%"),
        ],
        "members": [
            ("g17.webp", "members-putting", "", None, "50% 63%", "40% 50%"),
            ("g12.webp", "teams-clubhouse", "m", None, "50% 70%", "50% 70%"),
            ("g28.webp", "banquet-room", "m", None, "50% 60%", "50% 60%"),
            ("member-leagues.webp", "handshake-green", "m", None, "50% 45%", "50% 45%"),
        ],
        "course-gallery": [("g03.webp", "ponds-wide", "", None, "50% 72%", "62% 60%")],
    }

# course gallery: 33 photos, the land first
LAND = ["morning-ponds", "storm-fairway", "island-green", "bunker-big-sky", "pond-pines", "flag-green-pond",
        "green-big-sky", "swan", "ponds-above", "fescue", "bunker-blue-sky", "figure-eight-pond", "pond-channel",
        "pond-reflection", "sun-rays", "golden-flare", "green-bunker", "dusk-fairway", "golden-fairways"]
CLUB = ["clubhouse-fountain", "clubhouse-gardens", "heron-sculpture", "white-chairs", "clubhouse-green",
        "stone-lettering", "teams-clubhouse"]
PLAY = ["members-putting", "tee-shot-maple", "foursome-tee", "walking-bags", "driver-swing", "handshake-green",
        "bunker-shot"]
# layout C: (heading, line under it, feature photo, the rest)
SECTIONS = [
    ("The Land", "Ponds, pines and fescue across the Oak Ridges Moraine.", "morning-ponds", [p for p in LAND if p != "morning-ponds"]),
    ("The Clubhouse", "The veranda, the gardens and the fountain.", "clubhouse-fountain", [p for p in CLUB if p != "clubhouse-fountain"]),
    ("Members at Play", "Club events through the summer of 2026.", "members-putting", [p for p in PLAY if p != "members-putting"]),
]
# layouts A and B: one mixed run. In B the "*" photos are the large tiles (one, eight small, one, eight small, one, the rest)
MIXED = ["*morning-ponds", "storm-fairway", "island-green", "bunker-big-sky", "pond-pines", "flag-green-pond",
         "green-big-sky", "swan", "ponds-above",
         "*clubhouse-fountain", "fescue", "clubhouse-gardens", "heron-sculpture", "white-chairs", "bunker-blue-sky",
         "figure-eight-pond", "clubhouse-green", "pond-channel",
         "*members-putting", "tee-shot-maple", "foursome-tee", "walking-bags", "driver-swing", "handshake-green",
         "bunker-shot", "pond-reflection", "sun-rays", "stone-lettering", "golden-flare", "green-bunker",
         "dusk-fairway", "teams-clubhouse", "golden-fairways"]
# object-position for tiles that are cropped to 3:2 (default is the centre)
TILE_POS = {"sun-rays": "50% 62%", "morning-ponds": "50% 68%", "clubhouse-fountain": "50% 40%",
            "members-putting": "50% 68%", "dusk-fairway": "50% 70%", "golden-flare": "50% 30%"}

def dims(pid, size):
    b = (IMG / name(pid, size)).read_bytes()[:32]
    if b[12:16] == b"VP8 ":
        w, h = struct.unpack("<HH", b[26:30]); return w & 0x3FFF, h & 0x3FFF
    if b[12:16] == b"VP8X":
        return int.from_bytes(b[24:27], "little") + 1, int.from_bytes(b[27:30], "little") + 1
    raise ValueError(name(pid, size))

def alt(pid):
    a = PHOTOS[pid][2]
    for bad in ("—", "–"):
        assert bad not in a, pid
    return html.escape(a, quote=True)

def tile(pid, prefix, cls="", big=False):
    src, sizes = name(pid, "t"), ""
    if big:  # feature tiles get the larger files
        src = name(pid, "m")
        sizes = (f' srcset="{prefix}assets/img/{name(pid, "t")} 800w, {prefix}assets/img/{name(pid, "m")} 1200w, '
                 f'{prefix}assets/img/{name(pid)} 2000w" sizes="{big}"')
    w, h = dims(pid, "m" if big else "t")
    pos = f' style="--pos:{TILE_POS[pid]}"' if pid in TILE_POS else ""
    return (f'<a class="gal-i{" " + cls if cls else ""}" href="{prefix}assets/img/{name(pid)}" target="_blank" rel="noopener" data-gal>'
            f'<img src="{prefix}assets/img/{src}"{sizes} alt="{alt(pid)}" width="{w}" height="{h}" loading="lazy" decoding="async"{pos}></a>')

def gallery(layout, prefix="../"):
    if layout == "A":
        body = '<div class="gal gal-a">' + "".join(tile(p.lstrip("*"), prefix) for p in MIXED) + "</div>"
    elif layout == "B":
        out, n = [], 0
        for p in MIXED:
            if p.startswith("*"):
                n += 1
                out.append(tile(p[1:], prefix, "gal-f" + (" r" if n % 2 == 0 else ""), "(max-width:700px) 100vw, 800px"))
            else:
                out.append(tile(p, prefix))
        body = '<div class="gal gal-b">' + "".join(out) + "</div>"
    else:
        body = '<div class="gal gal-c">' + "".join(
            f'<div class="gal-sec"><div class="gal-head"><h3>{html.escape(t)}</h3><p>{html.escape(line)}</p></div>'
            f'{tile(feat, prefix, "gal-f", "(max-width:700px) 100vw, 1150px")}'
            f'<div class="gal-grid">{"".join(tile(p, prefix) for p in rest)}</div></div>'
            for t, line, feat, rest in SECTIONS) + "</div>"
    return "<!--gallery-->" + body + "<!--/gallery-->"

def apply(slug, s, hero=None, layout=None):
    """Rewrite one built page. Safe to run twice: swapped images carry data-photo."""
    hero, layout = hero or HERO, layout or GALLERY
    prefix = "../" if slug else ""
    if slug == "course-gallery":
        s, n = re.subn(r'<!--gallery-->.*?<!--/gallery-->|<div class="gallery reveal">.*?</div>',
                       lambda m: gallery(layout, prefix), s, count=1, flags=re.S)
        assert n == 1, (slug, "gallery block")
        s = s.replace("through the seasons. Tap any image", "photographed through the 2026 season. Tap any image")
        assert "photographed through the 2026 season" in s, (slug, "gallery intro")
        if "assets/js/gallery.js" not in s:
            s = s.replace("</body>", f'<script src="{prefix}assets/js/gallery.js" defer></script></body>', 1)
    for i, (old, pid, size, a, pos, pos_m) in enumerate(slots(hero).get(slug, [])):
        sid = f"{slug or 'home'}:{Path(old).stem}"
        first = i == 0 and size == ""  # the page hero loads first; everything else is lazy
        tag = (f'<img src="{prefix}assets/img/{name(pid, size)}" alt="{html.escape(a, quote=True) if a else alt(pid)}" '
               f'data-photo="{sid}" style="--pos:{pos};--pos-m:{pos_m}"'
               + (' fetchpriority="high"' if first else ' loading="lazy" decoding="async"') + ">")
        s, n = re.subn(rf'<img\b[^>]*\bdata-photo="{re.escape(sid)}"[^>]*>', lambda m: tag, s)
        if n == 0:
            s, n = re.subn(rf'<img\b[^>]*\bsrc="[^"]*assets/img/{re.escape(old)}"[^>]*>', lambda m: tag, s)
        assert n == 1, (slug, old, n)
    return s

CSS = """
/* 2026 photos: crop positions (set per image in tools/photos/photos.py), course gallery and photo viewer */
img[data-photo],.hero-bg img[data-photo],.page-hero .ph-bg img[data-photo]{object-position:var(--pos,center)}
@media(max-width:700px){img[data-photo],.hero-bg img[data-photo],.page-hero .ph-bg img[data-photo]{object-position:var(--pos-m,var(--pos,center))}}
.gal-i{position:relative;display:block;overflow:hidden;border-radius:var(--radius);background:#1f2740}
.gal-i img{width:100%;height:100%;display:block;object-fit:cover;object-position:var(--pos,center)}
.gal-i:focus-visible{outline:3px solid var(--gold);outline-offset:3px}
@media(prefers-reduced-motion:no-preference){.gal-i img{transition:transform .7s var(--ease)}.gal-i:hover img{transform:scale(1.03)}}
.gal-a{column-count:3;column-gap:14px}
.gal-a .gal-i{margin:0 0 14px;break-inside:avoid}.gal-a .gal-i img{height:auto}
.gal-b,.gal-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:14px}
.gal-b{grid-auto-flow:dense}
.gal-b .gal-i,.gal-grid .gal-i{aspect-ratio:3/2}
.gal-b .gal-f{grid-column:1/span 2;grid-row:span 2;aspect-ratio:auto}.gal-b .gal-f.r{grid-column:2/span 2}
.gal-b .gal-f img{position:absolute;inset:0}
.gal-sec+.gal-sec{margin-top:clamp(48px,7vw,84px)}
.gal-head{display:flex;align-items:baseline;justify-content:space-between;gap:8px 24px;flex-wrap:wrap;border-bottom:1px solid var(--line);padding-bottom:14px;margin-bottom:22px}
.gal-head h3{font-size:clamp(1.7rem,3.2vw,2.3rem);margin:0}.gal-head p{margin:0;color:var(--muted);font-size:.98rem}
.gal-c .gal-f{aspect-ratio:16/7;margin-bottom:14px}
@media(max-width:900px){.gal-a{column-count:2}}
@media(max-width:700px){.gal-a{column-gap:8px}.gal-a .gal-i{margin-bottom:8px}
.gal-b,.gal-grid{grid-template-columns:1fr 1fr;gap:8px}
.gal-b .gal-f,.gal-b .gal-f.r{grid-column:1/-1;grid-row:auto;aspect-ratio:3/2}
.gal-c .gal-f{aspect-ratio:3/2;margin-bottom:8px}.gal-head{margin-bottom:14px}}
.lb{position:fixed;inset:0;width:100vw;height:100vh;height:100dvh;max-width:none;max-height:none;margin:0;padding:0;border:0;background:rgba(20,26,48,.96);color:#fff}
.lb::backdrop{background:rgba(20,26,48,.96)}
.lb-fig{position:absolute;inset:0;margin:0;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:14px;padding:64px 84px 22px}
.lb-fig img{max-width:100%;max-height:calc(100vh - 150px);max-height:calc(100dvh - 150px);width:auto;height:auto;object-fit:contain;box-shadow:0 18px 60px rgba(0,0,0,.45)}
.lb figcaption{display:flex;gap:6px 18px;flex-wrap:wrap;justify-content:center;align-items:baseline;text-align:center;font-family:var(--sans);font-size:.95rem;line-height:1.5;color:rgba(255,255,255,.92);max-width:820px}
.lb-n{font-size:.74rem;font-weight:600;letter-spacing:.14em;text-transform:uppercase;color:var(--gold-soft);white-space:nowrap}
.lb button{position:absolute;width:48px;height:48px;display:grid;place-items:center;padding:0;background:transparent;color:#fff;border:1px solid rgba(255,255,255,.55);border-radius:0;cursor:pointer;transition:background .2s,color .2s}
.lb button:hover{background:#fff;color:var(--navy)}.lb button:focus-visible{outline:2px solid var(--gold-soft);outline-offset:3px}
.lb-x{top:14px;right:18px}.lb-p{left:18px;top:50%;margin-top:-24px}.lb-nx{right:18px;top:50%;margin-top:-24px}.lb-p svg{transform:scaleX(-1)}
@media(max-width:700px){.lb-fig{padding:70px 10px 86px}.lb-fig img{max-height:calc(100vh - 230px);max-height:calc(100dvh - 230px)}
.lb-p,.lb-nx{top:auto;bottom:18px;margin:0}.lb-p{left:calc(50% - 58px)}.lb-nx{right:calc(50% - 58px)}}
"""
MARK = ("/* photos:start */", "/* photos:end */")

def css(text):
    """style.css with the photo rules added (or refreshed, when run on a page set that already has them)."""
    block = MARK[0] + CSS + MARK[1] + "\n"
    if MARK[0] in text:
        return text[:text.find(MARK[0])] + block + text[text.find(MARK[1]) + len(MARK[1]):].lstrip("\n")
    return text.rstrip("\n") + "\n" + block

def needed(hero=None):
    """The web files the pages use: slot images, gallery tiles, and each gallery photo at full size."""
    files = {name(pid, size) for page in slots(hero or HERO).values() for _, pid, size, *_ in page}
    return files | set(re.findall(r"sl26-[\w-]+\.webp", gallery(GALLERY)))

def install(out):
    for f in sorted(needed()):
        shutil.copy(IMG / f, out / "assets/img" / f)
    shutil.copy(HERE / "gallery.js", out / "assets/js/gallery.js")

def prune(out, trash=None):
    """Drop images in assets/img that nothing on the site uses. A rebuild deletes its own fresh copies;
    run by hand (trash given) the files are moved there instead, never deleted."""
    text = ""
    for p in out.rglob("*"):
        if p.suffix in {".html", ".css", ".js", ".json"} and not ({"tools", ".git", ".claude", ".superpowers"} & set(p.relative_to(out).parts)):
            text += p.read_text(encoding="utf-8", errors="ignore")
    gone = [f for f in sorted((out / "assets/img").iterdir()) if f.is_file() and f.name not in text]
    for f in gone:
        if trash:
            trash.mkdir(parents=True, exist_ok=True); shutil.move(str(f), str(trash / f.name))
        else:
            f.unlink()
    return [f.name for f in gone]

PAGES = ["", "golf", "golf-academy", "golf-camps", "memberships", "members", "food-beverage", "course-gallery", "contact-us"]

if __name__ == "__main__":
    out = HERE.parents[1]
    install(out)
    for slug in PAGES:
        p = out / slug / "index.html" if slug else out / "index.html"
        p.write_text(apply(slug, p.read_text(encoding="utf-8")), encoding="utf-8", newline="")
    sheet = out / "assets/css/style.css"
    sheet.write_text(css(sheet.read_text(encoding="utf-8")), encoding="utf-8", newline="")
    gone = prune(out, Path.home() / "_to_delete" / f"springlakes-website-old-images-{date.today()}")
    print("photos applied: hero", HERO, "gallery", GALLERY, "| unused images moved to ~/_to_delete:", len(gone))
