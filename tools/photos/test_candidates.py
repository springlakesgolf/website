"""Photo picker candidates: python3 -m unittest tools/photos/test_candidates.py

Checks the built site in this checkout (run python3 tools/build.py first) and candidates.py itself.
"""
import json, re, sys, unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import candidates, photos
from manifest import PHOTOS
from library import LIBRARY, MEMBERS_ONLY

def built_slots():
    """data-photo slot -> page file, from every built page."""
    out = {}
    for p in ROOT.rglob("index.html"):
        if {"tools", ".git", ".claude", "photo-candidates"} & set(p.relative_to(ROOT).parts):
            continue
        for slot in re.findall(r'data-photo="([^"]+)"', p.read_text(encoding="utf-8")):
            out[slot] = p.relative_to(ROOT).as_posix()
    return out

class Built(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        f = ROOT / candidates.OUT_DIR / "candidates.json"
        if not f.exists():
            raise unittest.SkipTest("no photo-candidates/candidates.json: run python3 tools/build.py")
        cls.data = json.loads(f.read_text(encoding="utf-8"))
        cls.slots = built_slots()

    def test_every_non_junior_slot_has_options(self):
        self.assertTrue(self.slots)
        for slot in self.slots:
            if candidates.junior(slot):
                continue
            self.assertIn(slot, self.data, slot)
            self.assertGreaterEqual(len(self.data[slot]["options"]), 12, slot)

    def test_no_slot_that_is_not_on_a_page(self):
        self.assertEqual(set(self.data) - set(self.slots), set())

    def test_option_files_exist(self):
        for slot, s in self.data.items():
            for o in s["options"]:
                self.assertEqual(o["file"], f"sl26-{o['id']}-t.webp")
                self.assertTrue((ROOT / candidates.OUT_DIR / o["file"]).is_file(), o["file"])

    def test_no_stray_files(self):
        used = {o["file"] for s in self.data.values() for o in s["options"]} | {"candidates.json"}
        self.assertEqual({p.name for p in (ROOT / candidates.OUT_DIR).iterdir()}, used)

    def test_no_junior_slot(self):
        for slot in self.data:
            self.assertFalse(candidates.junior(slot), slot)
        self.assertNotIn("home:g26", self.data)
        self.assertNotIn("golf-camps:g26", self.data)

    def test_no_wrong_shape_photo_on_a_top_photo(self):
        heroes = {f"{slug or 'home'}:{Path(old).stem}" for slug, page in photos.slots(photos.HERO).items()
                  for old, _, size, *_ in page if size == ""}
        for slot in heroes & set(self.data):
            ids = {o["id"] for o in self.data[slot]["options"]}
            for pid in ("sun-rays", "golden-flare", "golden-fairways"):
                self.assertNotIn(pid, ids, slot)

    def test_banquet_room_only_in_the_members_area(self):
        for slot, s in self.data.items():
            if any(o["id"] in {"banquet-room"} | MEMBERS_ONLY for o in s["options"]):
                self.assertTrue(slot.startswith("members:"), slot)

    def test_many_photos_offered(self):
        self.assertGreaterEqual(len({o["file"] for s in self.data.values() for o in s["options"]}), 150)

    def test_options_carry_their_group_in_runs(self):
        for slot, s in self.data.items():
            seen, last = [], None
            for o in s["options"]:
                self.assertIn(o["group"], candidates.HEADINGS.values(), slot)
                if o["group"] != last:
                    self.assertNotIn(o["group"], seen, slot)   # one heading per group
                    seen.append(o["group"]); last = o["group"]

    def test_current_photo_not_offered(self):
        for slot, s in self.data.items():
            self.assertNotIn(s["current"], {photos.src(o["id"], sz) for o in s["options"] for sz in ("", "m", "t")}, slot)

    def test_alt_text_plain(self):
        for s in self.data.values():
            self.assertNotRegex(s["label"], "[–—]")
            for o in s["options"]:
                self.assertEqual(o["alt"], candidates.alt(o["id"]))
                self.assertNotRegex(o["alt"], "[–—]")

    def test_edit_mode_reads_the_candidates(self):
        js = (ROOT / "assets/js/edit-mode.js").read_text(encoding="utf-8")
        self.assertIn("photo-candidates/candidates.json", js)
        self.assertIn("Photo pick: ", js)

class Groups(unittest.TestCase):
    def test_every_photo_has_a_group(self):
        g = candidates.groups()
        self.assertEqual(set(g), set(PHOTOS) | set(LIBRARY))
        self.assertEqual(set(g.values()), {"drone", "land", "clubhouse", "play"})
        self.assertEqual(g["island-green"], "drone")
        self.assertEqual(g["swan"], "land")
        self.assertEqual(g["stone-lettering"], "clubhouse")
        self.assertEqual(g["banquet-room"], "play")

    def test_slot_groups_are_known(self):
        for slot, (label, gs) in candidates.SLOTS.items():
            self.assertTrue(label)
            self.assertFalse(candidates.junior(slot), slot)
            for g in gs:
                self.assertIn(g, candidates.HEADINGS.values(), slot)

    def test_junior_golf_slots_left_out(self):
        self.assertTrue(candidates.junior("junior-golf:g26"))
        self.assertTrue(candidates.junior("home:g26"))
        self.assertFalse(candidates.junior("home:g25"))

class Library(unittest.TestCase):
    """The picker only photos in library.py keep the PICKS.md rules."""
    def test_ids_are_new_and_files_exist(self):
        self.assertGreaterEqual(len(LIBRARY), 120)
        self.assertEqual(set(LIBRARY) & set(PHOTOS), set())
        for pid in LIBRARY:
            self.assertRegex(pid, r"^[a-z0-9]+(-[a-z0-9]+)*$")
            self.assertTrue((photos.IMG / f"sl26-{pid}-t.webp").is_file(), pid)

    def test_sources_are_unique_and_named_by_event(self):
        srcs = [v[0] for v in LIBRARY.values()]
        self.assertEqual(len(srcs), len(set(srcs)))
        used = {v[0].split("|")[-1] + ("|" + v[0].split("|")[0] if "|" in v[0] else "") for v in PHOTOS.values()}
        for src in srcs:
            hint, stem = src.split("|")
            self.assertIn(hint, {"Club Championship", "Ryder Cup", "Canada Day"}, src)   # never the junior camp
            self.assertNotIn(f"{stem}|{hint}", used, src)

    def test_nothing_from_the_do_not_use_list(self):
        txt = (HERE / "PICKS.md").read_text(encoding="utf-8")
        banned = set(re.findall(r"_?RSN\d+", txt.split("## Do not use")[1].split("## Checked clean")[0]))
        for a, b in [(5871, 5878), (9458, 9467)]:
            banned |= {f"_RSN{i:04d}" for i in range(a, b + 1)}
        self.assertGreater(len(banned), 40)
        for pid, (src, *_) in LIBRARY.items():
            self.assertNotIn(src.split("|")[1], banned, pid)

    def test_alt_text_and_groups(self):
        for pid, (src, crop, alt, group) in LIBRARY.items():
            self.assertIn(group, candidates.HEADINGS.values(), pid)
            self.assertTrue(alt and alt[0].isupper() and not alt.endswith("."), pid)
            self.assertNotRegex(alt, r"[–—-]|\b(his|her|he|she)\b", pid)
            if crop:
                self.assertTrue(0 <= crop[0] < crop[2] <= 1 and 0 <= crop[1] < crop[3] <= 1, pid)
        self.assertTrue(MEMBERS_ONLY <= set(LIBRARY))

if __name__ == "__main__":
    unittest.main()
