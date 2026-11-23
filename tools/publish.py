"""Copy only the public website out of a built checkout, for GitHub Pages.

The build writes the pages into the checkout itself, next to tools/ and the notes, so serving the
checkout as it is also serves tools/dining/staff.html, staff.js and cancel.html (staff-only dining
files) and every other source file. This copies an allow-list instead: the home page, robots.txt,
.nojekyll, assets/, the photo picker thumbnails, and each top-level folder that holds an index.html.
tools/ and dot folders never go out. Needs nothing but Python, so the Pages workflow runs it.

Run: python3 tools/publish.py _site
"""
import shutil, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILES = ("index.html", "robots.txt", ".nojekyll")
EXTRA_DIRS = ("assets", "photo-candidates")  # no index.html of their own
NEVER = {"tools", "_site", "node_modules"}
# staff-only dining sources; the built /dining-staff/ page (reservations on) is the only way they go out
STAFF_ONLY = ("staff.html", "staff.js", "cancel.html")

def public_dirs(root):
    for d in sorted(root.iterdir()):
        if not d.is_dir() or d.name.startswith(".") or d.name in NEVER: continue
        if d.name in EXTRA_DIRS or (d/"index.html").exists():
            yield d

def publish(root=ROOT, dest=None):
    root = Path(root); dest = Path(dest or root/"_site")
    if dest.exists(): shutil.rmtree(dest)
    dest.mkdir(parents=True)
    for f in FILES:
        if (root/f).exists(): shutil.copy(root/f, dest/f)
    for d in public_dirs(root):
        shutil.copytree(d, dest/d.name, ignore=shutil.ignore_patterns(".DS_Store"))
    # the guard: nothing from tools/, and no dining source file under its own name
    for p in dest.rglob("*"):
        rel = p.relative_to(dest)
        assert rel.parts[0] != "tools", rel
        assert p.name not in STAFF_ONLY, rel
    return dest

if __name__ == "__main__":
    out = publish(dest=sys.argv[1] if len(sys.argv) > 1 else None)
    print("published", out)
