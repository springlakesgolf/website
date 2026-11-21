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
            self.assertGreaterEqual(len(self.data[slot]["options"]), 3, slot)

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
            if any(o["id"] == "banquet-room" for o in s["options"]):
                self.assertTrue(slot.startswith("members:"), slot)

    def test_current_photo_not_offered(self):
        for slot, s in self.data.items():
            self.assertNotIn(s["current"], {photos.src(o["id"], sz) for o in s["options"] for sz in ("", "m", "t")}, slot)

    def test_alt_text_plain(self):
        for s in self.data.values():
            self.assertNotRegex(s["label"], "[–—]")
            for o in s["options"]:
                self.assertEqual(o["alt"], PHOTOS[o["id"]][2])
                self.assertNotRegex(o["alt"], "[–—]")

    def test_edit_mode_reads_the_candidates(self):
        js = (ROOT / "assets/js/edit-mode.js").read_text(encoding="utf-8")
        self.assertIn("photo-candidates/candidates.json", js)
        self.assertIn("Photo pick: ", js)

class Groups(unittest.TestCase):
    def test_every_photo_has_a_group(self):
        g = candidates.groups()
        self.assertEqual(set(g), set(PHOTOS))
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

if __name__ == "__main__":
    unittest.main()
