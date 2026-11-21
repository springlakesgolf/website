"""Junior Golf hub and Junior Academy application (Braeden, 2026-11-20).
Builds the site in temporary folders (closed, as shipped, and open against a mock address) and checks
the pages. The checkout itself is not touched. Needs the June source folder, so it runs on the Mac.
Run: python3 -m unittest tools/test_junior.py
"""
import os, re, shutil, subprocess, sys, tempfile, unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SRC = Path.home()/"Downloads/Marketing & Promotions/springlakes-site"
# the live addresses that must keep working (README, project-website-relaunch)
ADDRESSES = ["", "golf", "golf-academy", "golf-camps", "memberships", "members", "events-spring-lakes",
             "food-beverage", "tournaments", "course-gallery", "contact-us"]
FIELDS = ["player", "age", "years", "handicap", "tournaments", "parent", "email", "phone"]

def build(**env_extra):
    out = Path(tempfile.mkdtemp(prefix="slg-junior-"))
    shutil.copytree(REPO/"tools", out/"tools", ignore=shutil.ignore_patterns("design-options", "__pycache__", "node_modules"))
    env = dict(os.environ, **env_extra)
    for k in ("SLG_EDIT_EXEC", "SLG_DINING_EXEC", "SLG_SHOP", "SLG_ACADEMY_EXEC", "SLG_ACADEMY_OPEN"):
        if k not in env_extra: env.pop(k, None)
    r = subprocess.run([sys.executable, str(out/"tools/build.py")], env=env, capture_output=True, text=True, timeout=300)
    if r.returncode: raise AssertionError(f"build failed:\n{r.stdout}\n{r.stderr}")
    return out

def page(out, slug):
    return (out/slug/"index.html" if slug else out/"index.html").read_text(encoding="utf-8")

def main(s):
    return s[s.index('<main id="main">'):s.index("</main>")]

@unittest.skipUnless(SRC.exists(), "needs the June source folder (Mac only)")
class JuniorGolf(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.out = build()
        cls.hub, cls.academy = page(cls.out, "junior-golf"), page(cls.out, "junior-golf/academy")

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.out, ignore_errors=True)

    def test_hub_has_three_program_cards(self):
        m = main(self.hub)
        cards = re.findall(r'<article id="([^"]+)" class="course-card', m)
        self.assertEqual(cards, ["junior-camps", "operation-36", "junior-academy"])
        self.assertIn('href="../golf-camps/"', m)
        self.assertIn('href="academy/"', m)
        self.assertIn("Sign-up opens in February", m)
        self.assertIn("By application, so we can group players by level", m)
        self.assertIn("<h1>Junior Golf</h1>", self.hub)
        self.assertIn("<title>Junior Golf | Spring Lakes Golf Club</title>", self.hub)

    def test_hub_images_exist(self):
        for src in re.findall(r'<img src="\.\./([^"]+)"', main(self.hub)):
            self.assertTrue((self.out/src).exists(), src)

    def test_academy_form_has_every_field_and_is_closed(self):
        s = self.academy
        self.assertIn('id="academy-form"', s)
        self.assertIn("data-live", s)
        self.assertIn('data-open="0"', s)
        # player and parent groups each in their own fieldset, both disabled while closed
        self.assertEqual(s.count("<fieldset disabled>"), 2)
        self.assertEqual(s.count("<fieldset"), 2)
        self.assertEqual(s.count("<legend>"), 2)
        self.assertIn("Applications open in February 2027.", s)
        self.assertRegex(s, r'<button class="btn btn-gold" type="submit">Applications open in February</button>')
        for f in FIELDS:
            self.assertRegex(s, rf'name="{f}" id="ac-{f}"', f)
        self.assertIn('name="website"', s)  # honeypot
        self.assertIn('../../assets/js/academy.js', s)
        self.assertTrue((self.out/"assets/js/academy.js").exists())
        self.assertNotIn('="../assets', s)  # two folders deep, every link fixed

    def test_academy_links_resolve(self):
        base = self.out/"junior-golf/academy"
        for href in re.findall(r'(?:href|src)="(\.\./[^"#?]*)', self.academy):
            target = (base/href).resolve()
            self.assertTrue(target.exists() or (target/"index.html").exists(), href)

    def test_all_eleven_addresses_still_work(self):
        for slug in ADDRESSES:
            self.assertTrue((self.out/slug/"index.html" if slug else self.out/"index.html").exists(), slug or "home")

    def test_no_prices_or_dashes_on_junior_pages(self):
        for name, s in (("hub", self.hub), ("academy", self.academy)):
            self.assertNotIn("$", s, name)
            self.assertNotIn("camp-2027-flyer", s, name)
            for bad in ("—", "–"):
                self.assertNotIn(bad, s, name)
        camps = main(page(self.out, "golf-camps"))
        for bad in ("—", "–"):
            self.assertNotIn(bad, camps)

    def test_menu_links_point_at_the_hub(self):
        for slug in ("", "golf", "golf-camps", "members", "junior-golf", "junior-golf/academy"):
            s = page(self.out, slug)
            links = re.findall(r'href="([^"]*)"[^>]*>Junior Golf', s)
            # top menu, phone menu and footer, plus the breadcrumb on the two pages under the hub
            self.assertEqual(len(links), 4 if slug in ("golf-camps", "junior-golf/academy") else 3, slug)
            for h in links: self.assertTrue(h.endswith("junior-golf/"), (slug, h))
            self.assertNotRegex(s, r'href="[^"]*golf-camps/"[^>]*>Junior Golf')

    def test_camps_page_points_back(self):
        s = page(self.out, "golf-camps")
        self.assertIn("<h1>Junior Camps</h1>", s)
        self.assertIn('<a href="../junior-golf/">Junior Golf</a> &nbsp;/&nbsp; Junior Camps', s)
        self.assertIn("More Junior Golf", s)
        self.assertIn('href="../junior-golf/">See all junior golf</a>', s)

    def test_photo_slot_renamed(self):
        self.assertIn('data-photo="junior-golf:g26"', self.hub)
        self.assertNotIn('data-photo="golf-camps:', self.hub)

    def test_no_new_junior_photos(self):
        # only the two junior photos already public before 2026-11-20 (consent check for any new one)
        allowed = {"member-junior.webp", "junior-lesson.jpg", "sl26-flag-green-pond-m.webp", "sl26-bunker-blue-sky.webp"}
        for s in (self.hub, self.academy):
            imgs = {Path(p).name for p in re.findall(r'<img src="([^"]+)"', main(s) + s[s.index('class="page-hero"'):s.index('<main id="main">')])}
            self.assertLessEqual(imgs, allowed, imgs - allowed)

    def test_shipped_config_is_closed(self):
        import json
        cfg = json.loads((REPO/"tools/forms/academy.json").read_text())
        self.assertEqual(cfg, {"exec": "", "open": False})

@unittest.skipUnless(SRC.exists(), "needs the June source folder (Mac only)")
class AcademyOpen(unittest.TestCase):
    def test_open_build_takes_entries(self):
        out = build(SLG_ACADEMY_EXEC="http://127.0.0.1:8756/exec", SLG_ACADEMY_OPEN="1")
        try:
            s = page(out, "junior-golf/academy")
            self.assertIn('data-open="1"', s)
            self.assertIn('data-exec="http://127.0.0.1:8756/exec"', s)
            self.assertEqual(s.count("<fieldset>"), 2)
            self.assertNotIn("<fieldset disabled>", s)
            self.assertIn(">Send application</button>", s)
            self.assertNotIn("Applications open in February 2027.", s)
        finally:
            shutil.rmtree(out, ignore_errors=True)

    def test_shipped_exec_must_be_apps_script(self):
        out = Path(tempfile.mkdtemp(prefix="slg-junior-cfg-"))
        try:
            shutil.copytree(REPO/"tools", out/"tools", ignore=shutil.ignore_patterns("__pycache__", "node_modules"))
            (out/"tools/forms/academy.json").write_text('{"exec": "http://localhost:1/exec", "open": true}')
            env = {k: v for k, v in os.environ.items() if not k.startswith("SLG_")}
            r = subprocess.run([sys.executable, str(out/"tools/build.py")], env=env, capture_output=True, text=True, timeout=300)
            self.assertNotEqual(r.returncode, 0)
            self.assertIn("academy.json exec", r.stderr + r.stdout)
        finally:
            shutil.rmtree(out, ignore_errors=True)

if __name__ == "__main__":
    unittest.main()
