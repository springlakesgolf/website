"""Photo picker candidates: the photos that fit each image slot, for the staff edit mode.

tools/build.py calls write() after the page loop. It copies the 800 px file of every candidate
(sl26-<id>-t.webp) into photo-candidates/ and writes photo-candidates/candidates.json:

    {slot: {"label": "...", "current": "<file now in the slot>", "options": [{"id", "file", "alt"}]}}

Slot ids are photos.py's "<page or home>:<old file stem>", the data-photo value on the built pages.
Groups come from the comment headings in manifest.py (drone, the land, the clubhouse and grounds,
members at play), so a photo added to manifest.py under a heading becomes a candidate on its own.
Junior slots are left out until photo consent is confirmed.
"""
import json, re, shutil, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import photos
from manifest import PHOTOS, name

OUT_DIR = "photo-candidates"
HEADINGS = {"drone": "drone", "the land": "land", "the clubhouse and grounds": "clubhouse", "members at play": "play"}

# slot -> (label staff see, the groups that fit it)
SLOTS = {
    "home:hero-aerial":         ("Home page, top photo", ["drone"]),
    "home:g18":                 ("Home page, about the club", ["drone", "land"]),
    "home:course-east":         ("Home page, East Course card", ["land", "drone"]),
    "home:g25":                 ("Home page, clubhouse and dining", ["clubhouse"]),
    "home:g05":                 ("Home page, Golf Academy card", ["play"]),
    "golf:golf-aerial":         ("Golf page, top photo", ["drone"]),
    "golf:course-east":         ("Golf page, East Course card", ["land", "drone"]),
    "golf-academy:g05":         ("Golf Academy page, top photo", ["play"]),
    "memberships:g15":          ("Memberships page, top photo", ["clubhouse", "drone", "land"]),
    "contact-us:g04":           ("Contact page, top photo", ["clubhouse", "drone"]),
    "food-beverage:g25":        ("Dining page, top photo", ["clubhouse"]),
    "food-beverage:clubhouse":  ("Dining page, clubhouse photo", ["clubhouse"]),
    "members:g17":              ("Member's Area, top photo", ["play", "land"]),
    "members:g12":              ("Member's Area, corporate and golf days card", ["play"]),
    "members:g28":              ("Member's Area, social celebrations card", ["play", "clubhouse"]),
    "members:member-leagues":   ("Member's Area, leagues photo", ["play"]),
    "course-gallery:g03":       ("Course Gallery, top photo", ["drone", "land"]),
}
# junior photos wait on the consent check: no picker on these
JUNIOR = {"home:g26", "golf-camps:g26"}
MEMBERS_ONLY = {"banquet-room"}   # members area pages only
HERO_MIN_RATIO = 1.25             # top photos are wide: portrait and near square files are left out

def groups():
    """photo id -> group, read from the comment headings in manifest.py."""
    out, group = {}, None
    for line in (HERE / "manifest.py").read_text(encoding="utf-8").splitlines():
        m = re.match(r"\s*#\s*(.+?)\s*$", line)
        if m and m.group(1).lower() in HEADINGS:
            group = HEADINGS[m.group(1).lower()]
            continue
        m = re.match(r'\s*"([\w-]+)"\s*:\s*\(', line)
        if m and m.group(1) in PHOTOS and group:
            out[m.group(1)] = group
    return out

def junior(slot):
    return slot in JUNIOR or slot.startswith("junior-golf:")

def current():
    """slot -> (photo id or file, size) as photos.py sets it now."""
    return {f"{slug or 'home'}:{Path(old).stem}": (pid, size)
            for slug, page in photos.slots(photos.HERO).items() for old, pid, size, *_ in page}

def ratio(pid):
    w, h = photos.dims(pid, "t")
    return w / h

def options(slot, now, hero):
    by_group = groups()
    page = slot.split(":")[0]
    out = []
    for g in SLOTS[slot][1]:
        for pid, pg in by_group.items():
            if pg != g or pid == now or any(o["id"] == pid for o in out):
                continue
            if pid in MEMBERS_ONLY and page != "members":
                continue
            if hero and ratio(pid) < HERO_MIN_RATIO:
                continue
            out.append({"id": pid, "file": name(pid, "t"), "alt": PHOTOS[pid][2]})
    return out

def candidates():
    now = current()
    out = {}
    for slot, (label, _) in SLOTS.items():
        if junior(slot) or slot not in now:
            continue
        pid, size = now[slot]
        out[slot] = {"label": label, "current": photos.src(pid, size),
                     "options": options(slot, pid, hero=size == "")}
    return out

def write(out):
    """Copy the candidate files into <out>/photo-candidates/ and write candidates.json there."""
    data = candidates()
    d = Path(out) / OUT_DIR
    if d.exists():
        shutil.rmtree(d)
    d.mkdir(parents=True)
    for f in sorted({o["file"] for s in data.values() for o in s["options"]}):
        shutil.copy(photos.IMG / f, d / f)
    (d / "candidates.json").write_text(json.dumps(data, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    return data

if __name__ == "__main__":
    data = write(HERE.parents[1])
    print(f"{len(data)} slots, {len({o['file'] for s in data.values() for o in s['options']})} photos in {OUT_DIR}/")
