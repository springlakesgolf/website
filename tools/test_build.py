"""Builds the site both ways (soft and full launch) in temporary folders and checks each form.
The checkout itself is not touched. Needs the June source folder, so it runs on the Mac.
Run: python3 -m unittest tools/test_build.py
"""
import os, re, shutil, subprocess, sys, tempfile, unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO/"tools"))
SRC = Path.home()/"Downloads/Marketing & Promotions/springlakes-site"
STANDING = ("heron-mark.png", "heron-mark-reverse.png", "favicon-64.png", "apple-touch-icon.png")
FLYING = ("heron-gold.png", "heron-navy.png", "heron-flying-icon-64.png", "heron-flying-touch.png")
# the live addresses that must keep working (README, project-website-relaunch)
ADDRESSES = ["", "golf", "golf-academy", "golf-camps", "memberships", "members", "events-spring-lakes",
             "food-beverage", "tournaments", "course-gallery", "contact-us"]

def build(form):
    out = Path(tempfile.mkdtemp(prefix=f"slg-{form}-"))
    shutil.copytree(REPO/"tools", out/"tools", ignore=shutil.ignore_patterns("design-options", "__pycache__", "node_modules"))
    env = dict(os.environ, SLG_LAUNCH=form)
    for k in ("SLG_EDIT_EXEC", "SLG_DINING_EXEC", "SLG_SHOP"): env.pop(k, None)
    r = subprocess.run([sys.executable, str(out/"tools/build.py")], env=env, capture_output=True, text=True, timeout=300)
    if r.returncode: raise AssertionError(f"{form} build failed:\n{r.stdout}\n{r.stderr}")
    return out

def site_text(out):
    """Every built page, script and style sheet (not tools/), joined, with each file's path in front."""
    parts = []
    for p in sorted(out.rglob("*")):
        rel = p.relative_to(out)
        if rel.parts[0] == "tools" or p.suffix not in {".html", ".css", ".js", ".json"}: continue
        parts.append(f"\n=== {rel}\n" + p.read_text(encoding="utf-8", errors="ignore"))
    return "".join(parts)

def refs(text, name):
    return re.findall(rf"[\w./-]*(?<![\w-]){re.escape(name)}", text)

@unittest.skipUnless(SRC.exists(), "needs the June source folder (Mac only)")
class LaunchForms(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import build as b
        cls.shop = b.SHOP_URL
        cls.soft, cls.full = build("soft"), build("full")
        cls.soft_text, cls.full_text = site_text(cls.soft), site_text(cls.full)

    @classmethod
    def tearDownClass(cls):
        for d in (cls.soft, cls.full): shutil.rmtree(d, ignore_errors=True)

    def test_soft_has_no_shop_link(self):
        self.assertNotIn(self.shop, self.soft_text)
        self.assertNotIn("myshopify", self.soft_text)
        self.assertNotIn("Pro Shop Online", self.soft_text)
        self.assertIsNone(re.search(r">\s*Shop\s*<", self.soft_text))
        self.assertNotIn("shop-band", self.soft_text)

    def test_soft_has_no_standing_heron(self):
        for f in STANDING:
            self.assertEqual(refs(self.soft_text, f), [], f)
            self.assertFalse((self.soft/"assets/img"/f).exists(), f)
        self.assertIn("assets/img/heron-gold.png", self.soft_text)          # header and footer mark
        self.assertIn("assets/img/heron-flying-icon-64.png", self.soft_text)  # browser tab icon

    def test_soft_hides_reservations_by_default(self):
        self.assertFalse((self.soft/"dining-staff").exists())
        self.assertFalse((self.soft/"food-beverage/cancel").exists())
        self.assertNotIn("dining.js", (self.soft/"food-beverage/index.html").read_text())

    def test_full_has_shop_and_standing_heron(self):
        home = (self.full/"index.html").read_text()
        self.assertIn(self.shop, home)
        self.assertRegex(home, r'<nav[^>]*>.*?Shop<span class="sr-only">.*?</nav>')
        self.assertIn("Pro Shop Online", home)  # footer
        for f in ("heron-mark-reverse.png", "favicon-64.png"):
            self.assertIn(f"assets/img/{f}", home)
        for f in FLYING:
            self.assertEqual(refs(self.full_text, f), [], f)

    def test_both_forms_keep_every_address(self):
        for out in (self.soft, self.full):
            for slug in ADDRESSES:
                self.assertTrue((out/slug/"index.html" if slug else out/"index.html").exists(), (out.name, slug))

    def test_no_dashes(self):
        for t in (self.soft_text, self.full_text):
            self.assertNotIn("—", t); self.assertNotIn("–", t)

class MemberPieces(unittest.TestCase):
    """Each piece's off form, checked on the parts build.py writes (no full build needed)."""
    def setUp(self):
        import importlib, build as b
        self.b = importlib.reload(b)

    def test_event_inquiry_off_leaves_a_phone_line(self):
        self.b.MEMBER_PIECES["event_inquiry"] = False
        html = self.b.member_events()
        self.assertNotIn("<form", html)
        self.assertIn("905-640-3633", html)
        self.b.MEMBER_PIECES["event_inquiry"] = True
        self.assertIn("<form", self.b.member_events())
        self.assertNotIn("<!--", self.b.member_events())

    def test_reservations_off_builds_no_panel(self):
        self.b.MEMBER_PIECES["reservations"] = False
        self.assertIsNone(self.b.dining_exec())

    def test_reservations_off_is_the_default(self):
        self.assertFalse(self.b.MEMBER_PIECES["reservations"])

    @unittest.skipUnless(SRC.exists(), "needs the June source folder (Mac only)")
    def test_renewal_form_off_keeps_dates_and_a_phone_line(self):
        self.b.MAILS, self.b.WEEK = [], None
        page = (SRC/"members.html").read_text().replace('src="assets/', 'src="../assets/')
        self.b.MEMBER_PIECES["renewal_form"] = False
        html = self.b.edit("members.html", page)
        renew = html[html.find('<section id="renew">'):]
        renew = renew[:renew.find("</section>")]
        self.assertNotIn("<form", renew)
        self.assertIn("January 15, 2027", renew)
        self.assertIn("905-640-3633", renew)
        self.b.MEMBER_PIECES["renewal_form"] = True
        self.assertIn("<form", self.b.edit("members.html", page).split('<section id="renew">')[1])

    def test_launch_setting(self):
        self.assertIn(self.b.LAUNCH, ("soft", "full"))

if __name__ == "__main__":
    unittest.main()
