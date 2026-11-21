"""Club Events list in the Member's Area (Braeden, 2026-11-20).

Checks the built members page against the seed (tools/members/events.json), that the
baked rows match what content.js draws from the sheet, and the house rules.
Run: python3 -m unittest tools/members/test_events.py  (after python3 tools/build.py)
"""
import json, re, shutil, subprocess, sys, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/"tools"))
import build  # noqa: E402  (importing does not build)

SEED = json.loads((ROOT/"tools/members/events.json").read_text())
PAGE = (ROOT/"members/index.html").read_text()
STATUSES = {"Sign-up open", "Opens soon", "Details to come"}

def block():
    m = re.search(r'<div class="evh">.*?</ul></div>', PAGE, re.S)
    assert m, "no Club Events block on members/index.html"
    return m.group(0)

class Seed(unittest.TestCase):
    def test_twelve_rows_every_field(self):
        self.assertEqual(len(SEED), 12)
        for r in SEED:
            self.assertEqual(set(r), {"name", "date", "course", "status", "link", "photo"}, r)
            self.assertTrue(r["name"].strip() and r["date"].strip(), r)

    def test_nothing_confirmed_yet(self):
        # the Event Book has not been read, so no row claims more than "Details to come"
        for r in SEED:
            self.assertEqual(r["status"], "Details to come", r["name"])
            self.assertEqual((r["link"], r["photo"]), ("", ""), r["name"])

class Page(unittest.TestCase):
    def test_top_of_the_events_section(self):
        i = PAGE.find('<section id="events"')
        self.assertGreater(i, 0)
        self.assertTrue(PAGE.startswith('<div class="container"><div class="evh">', i + len('<section id="events" class="bg-cream">')))
        b = block()
        for words in ("2027 Season", "<h2 class=\"reveal d1\">Club Events</h2>", "Every club event in one place.",
                      'id="events-box"', 'aria-live="polite"'):
            self.assertIn(words, b)

    def test_every_seed_row_in_order(self):
        names = re.findall(r'<h3 class="evh-name">(.*?)</h3>', block())
        self.assertEqual(names, [build.esc(r["name"]) for r in SEED])
        for r in SEED:
            self.assertIn(build.esc(r["date"]), block())
            self.assertIn(build.esc(r["course"] or "Course to come"), block())

    def test_statuses_are_the_three(self):
        found = re.findall(r'<span class="evh-pill [a-z-]+">(.*?)</span>', block())
        self.assertEqual(len(found), 12)
        self.assertTrue(set(found) <= STATUSES, found)

    def test_house_rules(self):
        b = block()
        for bad in ("$", "\u2014", "\u2013", "&mdash;", "&ndash;", "enquir"):
            self.assertNotIn(bad, b)
        self.assertIsNone(re.search(r"\b(fees?|price[sd]?|cost|HST|per player|entry)\b", b, re.I))
        self.assertNotRegex(b, r"(braeden|cullen|laura|rhys|luke|ashley)", "staff names in member copy")

    def test_content_js_ships_with_the_events_box(self):
        js = (ROOT/"assets/js/content.js").read_text()
        self.assertIn("events-box", js)
        self.assertNotIn("__EXEC_URL__", js)
        self.assertIn("assets/js/content.js", PAGE)

class Renderer(unittest.TestCase):
    def test_python_bake_matches_content_js(self):
        node = shutil.which("node")
        if not node: self.skipTest("node not installed")
        rows = SEED + [
            {"name": "Open <b>", "date": "", "course": "", "status": "Sign-up open", "link": "https://example.com/a?b=1&c=2", "photo": "https://example.com/p.jpg"},
            {"name": "Odd", "date": "x", "course": "y", "status": "Confirmed", "link": "javascript:x", "photo": "http://x"},
            {"name": "Soon", "date": "x", "course": "y", "status": "Opens soon", "link": "https://example.com/s", "photo": ""}]
        js = ("const {eventsHTML} = require(process.argv[1]); let s = ''; process.stdin.on('data', d => s += d)"
              ".on('end', () => process.stdout.write(eventsHTML(JSON.parse(s))));")
        for case in (rows, []):
            out = subprocess.run([node, "-e", js, str(ROOT/"tools/members/content.js")], input=json.dumps(case),
                                 capture_output=True, text=True, check=True).stdout
            self.assertEqual(out, build.events_html(case))

    def test_baked_list_is_the_seed(self):
        self.assertIn(build.events_html(SEED), PAGE)

if __name__ == "__main__":
    unittest.main()
