"""Builds the site both ways (soft and full launch) in temporary folders and checks each form.
The checkout itself is not touched. Needs the June source folder, so it runs on the Mac.
Run: python3 -m unittest tools/test_build.py
"""
import html, os, re, shutil, subprocess, sys, tempfile, unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO/"tools"))
SRC = Path.home()/"Downloads/Marketing & Promotions/springlakes-site"
STANDING = ("heron-mark.png", "heron-mark-reverse.png", "favicon-64.png", "apple-touch-icon.png")
FLYING = ("heron-gold.png", "heron-navy.png", "heron-flying-icon-64.png", "heron-flying-touch.png")
# the live addresses that must keep working (README, project-website-relaunch)
ADDRESSES = ["", "golf", "golf-academy", "golf-camps", "memberships", "members", "events-spring-lakes",
             "food-beverage", "tournaments", "course-gallery", "contact-us",
             "junior-golf", "junior-golf/academy"]  # Junior Golf hub and Academy application (2026-11-20)

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

    def test_no_restaurant_menu_or_hours_in_public(self):
        # review 2026-10-16 item 4: dining is for members and guests, so no menu, prices or hours on public pages
        for out in (self.soft, self.full):
            dining = (out/"food-beverage/index.html").read_text()
            for bad in ("Restaurant-Menu", "Wine-List", "11am", 'class="hours"', "doc-links"):
                self.assertNotIn(bad, dining, bad)
            self.assertIn("social membership", dining)
            for f in ("Restaurant-Menu.pdf", "Wine-List.pdf"):
                self.assertFalse((out/"assets/docs"/f).exists(), f)
        for f in ("Restaurant-Menu.pdf", "Wine-List.pdf", "camp-2026.webp"):
            self.assertEqual(refs(self.soft_text, f), [], f)

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

    def test_members_events_section_has_club_events_and_event_planning(self):
        # the memarea line joins member_events() (soft launch pieces) and club_events() (events hub)
        import build as b
        for out in (self.soft, self.full):
            page = (out/"members/index.html").read_text()
            sec = page[page.index('<section id="events"'):]
            sec = sec[:sec.index("</section>")]
            self.assertEqual(page.count('id="events-box"'), 1, out.name)
            self.assertEqual(sec.count('<h2 class="reveal d1">Club Events</h2>'), 1, out.name)
            self.assertGreater(sec.count('class="evh-item'), 0, out.name)
            plan = 'id="ev-e"' if b.MEMBER_PIECES["event_inquiry"] else "905-640-3633"
            self.assertIn("Plan your event with us", sec, out.name)
            self.assertLess(sec.index('id="events-box"'), sec.index(plan), out.name)
            if b.MEMBER_PIECES["event_inquiry"]:
                form = sec[sec.index('<form class="inquiry-form"'):sec.index("</form>")]
                self.assertIn('name="website"', form, out.name)

    def test_league_hub_opens_the_app(self):
        # every league in the members League hub opens its own page in the club app (Cullen, 2026-11-21)
        import build as b
        for out in (self.soft, self.full):
            page = (out/"members/index.html").read_text()
            sec = page[page.index('<section id="leagues"'):]
            sec = sec[:sec.index("</section>")]
            hrefs = dict((re.sub(r"<[^>]+>", "", t).replace("&amp;", "&"), h)
                         for h, t in re.findall(r'<li><a href="([^"]+)"[^>]*>(.*?)</a></li>', sec))
            want = {name: f"{b.APP_URL}/e/{code}" if code else f"{b.APP_URL}/e" for name, code in b.LEAGUES}
            want["Events"] = f"{b.APP_URL}/app/events"
            self.assertEqual(hrefs, want, out.name)
            self.assertIn(f'href="{b.APP_URL}/app"', sec, out.name)
            self.assertIn(">Open the club app<", sec, out.name)
            self.assertIn("in the club app", sec, out.name)
            self.assertNotIn("Golf Genius", sec, out.name)
        for t in (self.soft_text, self.full_text):
            self.assertNotIn("golfgenius", t)

    def test_published_site_has_no_staff_dining_files(self):
        # the preview serves what tools/publish.py copies out, not the checkout: tools/dining/staff.html,
        # staff.js and cancel.html (staff only) stay out, and every public address stays in
        import publish
        for out in (self.soft, self.full):
            self.assertTrue((out/"tools/dining/staff.html").exists())  # in the build checkout ...
            site = publish.publish(out, Path(tempfile.mkdtemp(prefix="slg-site-")))
            try:
                for f in ("tools/dining/staff.html", "tools/dining/staff.js", "tools/dining/cancel.html"):
                    self.assertFalse((site/f).exists(), (out.name, f))  # ... and not in what is served
                self.assertFalse((site/"tools").exists(), out.name)
                self.assertEqual([p for p in site.rglob("*") if p.name in publish.STAFF_ONLY], [], out.name)
                for slug in ADDRESSES:
                    self.assertTrue((site/slug/"index.html" if slug else site/"index.html").exists(), (out.name, slug))
                for f in ("robots.txt", ".nojekyll", "assets/css/style.css", "assets/js/site.js"):
                    self.assertTrue((site/f).exists(), (out.name, f))
            finally:
                shutil.rmtree(site, ignore_errors=True)

    def test_every_page_has_a_link_preview_card(self):
        # og:title, og:description and an absolute https og:image on every built page, so a shared link shows a
        # card; the image file is in the build. The old-address redirect pages carry one too.
        import build as b
        self.assertIn("food-beverage", b.OG_DESCRIPTION)
        for out in (self.soft, self.full):
            pages = [p for p in sorted(out.glob("**/index.html")) if p.relative_to(out).parts[0] != "tools"]
            self.assertGreaterEqual(len(pages), len(ADDRESSES), out.name)
            for p in pages:
                rel = p.relative_to(out).parent.as_posix()
                s = p.read_text()
                title = re.search(r"<title>([^<]+)</title>", s).group(1)
                desc = re.search(r'<meta name="description" content="([^"]+)">', s).group(1)
                for prop in ("og:title", "og:description", "og:image"):
                    self.assertEqual(len(re.findall(rf'<meta property="{prop}" content="[^"]+">', s)), 1, (out.name, rel, prop))
                head = s[:s.index("</head>")] if "</head>" in s else s  # the redirect stubs have no head tags
                self.assertIn(f'<meta property="og:title" content="{title}">', head, (out.name, rel))
                card = html.escape(b.OG_DESCRIPTION[rel], quote=True) if rel in b.OG_DESCRIPTION else desc
                self.assertIn(f'<meta property="og:description" content="{card}">', head, (out.name, rel))
                img = re.search(r'<meta property="og:image" content="([^"]+)">', head).group(1)
                self.assertRegex(img, r"^https://[^\s\"'<>]+\.(jpg|jpeg|png)$", (out.name, rel))
                self.assertTrue(img.startswith(b.SITE_URL + "/"), (out.name, rel, img))
                self.assertTrue((out/img[len(b.SITE_URL) + 1:]).exists(), (out.name, rel, img))

    def test_every_content_page_has_one_h1(self):
        # one page heading per content page for screen readers and search; the home hero title is it, kept in its
        # June look. The two old-address redirect stubs have no heading by design.
        stubs = {"tournaments", "events-spring-lakes"}
        for out in (self.soft, self.full):
            pages = [p for p in sorted(out.glob("**/index.html")) if p.relative_to(out).parts[0] != "tools"]
            seen = set()
            for p in pages:
                rel = p.relative_to(out).parent.as_posix()
                n = len(re.findall(r"<h1[\s>]", p.read_text()))
                self.assertEqual(n, 0 if rel in stubs else 1, (out.name, rel))
                seen.add("" if rel == "." else rel)
            self.assertTrue(set(ADDRESSES) - stubs <= seen, (out.name, set(ADDRESSES) - stubs - seen))
            home = (out/"index.html").read_text()
            self.assertIn('<h1 class="hero-title reveal in d1">Spring Lakes</h1>', home, out.name)
            self.assertNotIn('<div class="hero-title', home, out.name)
            css = (out/"assets/css/style.css").read_text()
            self.assertEqual(css.count(".hero h1.hero-title{"), 1, out.name)  # one copy, from HERO_H1_CSS
            self.assertIn("color:var(--gold-soft)", css[css.index(".hero h1.hero-title{"):].split("}")[0], out.name)

    def test_no_dashes(self):
        for t in (self.soft_text, self.full_text):
            self.assertNotIn("—", t); self.assertNotIn("–", t)

    def test_house_rules_in_page_copy(self):
        # inquiry not enquiry; no prices; the only club address on a page is info@ (staff addresses stay internal)
        for t in (self.soft_text, self.full_text):
            self.assertIsNone(re.search(r"(?i)enquir", t))
            self.assertIsNone(re.search(r"\$\s?\d", re.sub(r"<script.*?</script>", "", t, flags=re.S)))
            self.assertEqual(set(re.findall(r"[\w.+-]+@springlakesgolf\.com", t)) - {"info@springlakesgolf.com"}, set())

    def test_contact_page_lists_departments_not_staff(self):
        # "our team", not a staff member's name. The academy coach bios are Cullen's open call (Setup-Audit item 17).
        for out in (self.soft, self.full):
            page = (out/"contact-us/index.html").read_text()
            for name in ("Piccione", "Pacas", "Roth", "Barker", "Yake", "McNeill", "Contois", "Woo"):
                self.assertNotIn(name, page, (out.name, name))
            self.assertIn("Departments", page)

    def test_no_staff_names_in_any_page_copy(self):
        # "our team", not a staff member's name, on every built page. golf-academy is left out only while
        # its coach cards wait on Cullen (council decision 1, Setup-Audit item 17); drop the skip once he decides.
        names = re.compile(r"\b(Braeden|Cullen|Rhys|Luke|Laura|Ashley|Piccione|Pacas|Barker|Roth|Yake|McNeill|Contois|Steve Woo)\b")
        for out in (self.soft, self.full):
            for p in sorted(out.rglob("*.html")):
                rel = p.relative_to(out)
                if rel.parts[0] in ("tools", "golf-academy"): continue
                copy = re.sub(r"<script.*?</script>|<style.*?</style>|<!--.*?-->", "", p.read_text(errors="ignore"), flags=re.S)
                self.assertIsNone(names.search(copy), (out.name, str(rel), (names.search(copy) or [None])[0]))

    def test_pages_workflow_publishes_every_address_and_no_tools(self):
        # the Pages workflow runs tools/publish.py; every live address goes out and tools/ never does
        self.assertIn("python3 tools/publish.py _site", (REPO/".github/workflows/pages.yml").read_text())
        import publish
        site = publish.publish(self.soft, Path(tempfile.mkdtemp(prefix="slg-site-")))
        try:
            for slug in ADDRESSES:
                self.assertTrue((site/slug/"index.html" if slug else site/"index.html").exists(), slug)
            self.assertFalse((site/"tools").exists())
        finally:
            shutil.rmtree(site, ignore_errors=True)

class MemberPieces(unittest.TestCase):
    """Each piece's off form, checked on the parts build.py writes (no full build needed)."""
    def setUp(self):
        import importlib, build as b
        self.b = importlib.reload(b)

    def test_forecast_is_a_strip_under_the_club_news(self):
        # the 7-day forecast runs along the bottom of the Club news band, outside the sidebar, so the
        # email and the sidebar fill the width with no empty space under the email (Cullen, 2026-11-21)
        mails = [{"link": "https://mailchi.mp/x/a", "title": "A", "label": "Nov 20", "date": "2026-11-20"}]
        band = self.b.this_week(mails, None)
        side = band[band.index('<aside id="side-col"'):band.index("</aside>")]
        self.assertNotIn("wx-", side)
        self.assertEqual(band.count('id="wx-days"'), 1)
        self.assertIn('</aside></div><div id="wx-col" class="wx-strip"><h3>7-day forecast</h3>', band)
        self.assertTrue(band.endswith("Environment and Climate Change Canada.</p></div></div></section>"))
        self.assertIn('<div class="week-grid">', band)
        self.assertIn('<div class="week-grid one">', self.b.this_week([], None))
        # days side by side; on a phone the strip scrolls inside itself, never the page
        self.assertIn(".wx-days{display:grid;grid-template-columns:repeat(7,minmax(0,1fr))", self.b.WEEK_CSS)
        phone = self.b.WEEK_CSS[self.b.WEEK_CSS.index("@media(max-width:900px){.week-grid"):]
        phone = phone[:phone.index("}}")]
        self.assertIn(".week-grid{grid-template-columns:1fr", phone)
        self.assertIn(".wx-days{display:flex;overflow-x:auto", phone)
        # the email stretches to the sidebar's height and never below its 640px floor (500px on a phone)
        css = self.b.WEEK_CSS
        self.assertIn(".week-grid{display:grid;grid-template-columns:1.6fr 1fr;gap:44px;align-items:stretch}", css)
        self.assertIn("#mc-col{display:flex;flex-direction:column}", css)
        self.assertIn(".mc-frame{border:1px solid var(--line);height:640px;background:#fff;position:relative;flex:1 0 auto}", css)
        self.assertIn(".mc-frame iframe{position:absolute;inset:0;width:100%;height:100%", css)
        self.assertIn("@media(max-width:900px){.mc-frame{height:500px}}", css)

    def test_event_inquiry_off_leaves_a_phone_line(self):
        self.b.MEMBER_PIECES["event_inquiry"] = False
        html = self.b.member_events()
        self.assertNotIn("<form", html)
        self.assertIn("905-640-3633", html)
        self.b.MEMBER_PIECES["event_inquiry"] = True
        self.assertIn("<form", self.b.member_events())
        self.assertNotIn("<!--", self.b.member_events())

    def test_event_inquiry_form_has_the_hidden_website_field(self):
        # same honeypot as the membership and academy forms: hidden off screen, skipped by tab and autofill
        self.b.MEMBER_PIECES["event_inquiry"] = True
        html = self.b.member_events()
        form = html[html.index('<form class="inquiry-form"'):html.index("</form>")]
        self.assertIn('name="website"', form)
        self.assertIn('<div class="hp" aria-hidden="true"><label for="ev-w">Website</label><input name="website" id="ev-w" type="text" tabindex="-1" autocomplete="off"></div>', form)
        self.assertLess(form.index('name="website"'), form.index('id="ev-n"'))

    def test_reservations_off_builds_no_panel(self):
        self.b.MEMBER_PIECES["reservations"] = False
        self.assertIsNone(self.b.dining_exec())

    def test_dining_pages_get_the_soft_heron_when_reservations_are_on(self):
        # cancel.html and staff.html are written for the standing heron; marks() points them at the soft files
        self.b.SOFT, self.b.MARK = True, self.b.MARKS["soft"]
        for p in sorted((REPO/"tools/dining").iterdir()):
            if p.suffix not in {".html", ".js"} or p.name.endswith(".test.js"): continue
            out = self.b.marks(p.read_text())
            for f in STANDING:
                self.assertEqual(refs(out, f), [], (p.name, f))

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

class LeagueHub(unittest.TestCase):
    """The League hub settings: the app address and each league's event code (no full build needed)."""
    def setUp(self):
        import importlib, build as b
        self.b = importlib.reload(b)

    def test_app_address_and_codes(self):
        self.assertTrue(self.b.APP_URL.startswith("https://"))
        self.assertFalse(self.b.APP_URL.endswith("/"))
        names = [n for n, _ in self.b.LEAGUES]
        self.assertEqual(len(names), len(set(names)))
        for name, code in self.b.LEAGUES:
            self.assertTrue(code is None or re.fullmatch(r"[A-Z0-9]{6}", code), (name, code))

    def test_a_league_without_a_code_opens_the_code_page(self):
        self.assertEqual(self.b.league_href(None), self.b.APP_URL + "/e")
        self.assertEqual(self.b.league_href("WCZ7ZX"), self.b.APP_URL + "/e/WCZ7ZX")

    @unittest.skipUnless(SRC.exists(), "needs the June source folder (Mac only)")
    def test_a_bad_code_stops_the_build(self):
        page = (SRC/"members.html").read_text()
        self.b.LEAGUES = [("Ladies League", "wcz7zx")]
        with self.assertRaises(AssertionError):
            self.b.league_hub(page, "members.html")
        self.b.LEAGUES = [("Ladies League", "WCZ7ZX")]
        out = self.b.league_hub(page, "members.html")
        self.assertIn(f'href="{self.b.APP_URL}/e/WCZ7ZX"', out)
        self.assertNotIn("golfgenius", out)

class AssetsHaveNoStaffNames(unittest.TestCase):
    """Public copy says "our team": no staff names in the text of anything under assets/ (comments included).
    Runs on the committed assets, so rebuild with tools/build.py after changing a source in tools/."""
    STAFF = re.compile(r"\b(Laura|Piccione|Braeden|Cullen|Pacas|Rhys|Luke|Ashley|Steve|Woo)\b")

    def test_assets_text_has_no_staff_names(self):
        hits = []
        for p in sorted((REPO/"assets").rglob("*")):
            if p.suffix not in {".html", ".css", ".js", ".json", ".svg", ".txt", ".md"}: continue
            for n, line in enumerate(p.read_text(encoding="utf-8", errors="ignore").splitlines(), 1):
                hits += [f"{p.relative_to(REPO)}:{n}: {m}" for m in self.STAFF.findall(line)]
        self.assertEqual(hits, [])

if __name__ == "__main__":
    unittest.main()
