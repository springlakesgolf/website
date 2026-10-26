"""Offline tests for staff_edits.py: guardrails, page lookup, a dry run with a fake Claude, the build
replay, and the bot endpoint through mock_server.py. No API key, git or network needed.
Run: python3 -m unittest tools/edit-mode/test_staff_edits.py
"""
import importlib.util, json, os, subprocess, sys, tempfile, time, unittest
from pathlib import Path
from types import SimpleNamespace

HERE = Path(__file__).parent
spec = importlib.util.spec_from_file_location("staff_edits", HERE/"staff_edits.py")
se = importlib.util.module_from_spec(spec); spec.loader.exec_module(se)
ROWS = json.loads((HERE/"fixtures/rows.json").read_text())
ROW = {r["id"]: r for r in ROWS}

PAGE = ('<html><head><title>Golf | Spring Lakes Golf Club</title><meta name="description" content="Three courses">'
        '<style>.x{color:red}</style></head><body><main><h2 class="script">Member Favourite</h2>'
        '<p>Strategy beats raw distance.</p><p>Call the pro shop at 905-640-3633.</p>'
        '<a class="btn" href="../contact-us/">Make an inquiry</a><p>Our staff directory: Rhys, golf operations.</p>'
        '<form><label>Name</label></form><script>var a = "raw distance";</script></main></body></html>')

def ed(find, rep): return [{"find": find, "replace": rep}]

class Guardrails(unittest.TestCase):
    def ok(self, edits, page="golf"):
        new, problems = se.check(PAGE, page, edits)
        self.assertEqual(problems, []); return new
    def held(self, edits, why, page="golf"):
        _, problems = se.check(PAGE, page, edits)
        self.assertTrue(any(why in p for p in problems), problems)

    def test_plain_text_edit(self):
        new = self.ok(ed("Strategy beats raw distance.", "Strategy beats power."))
        self.assertIn("<p>Strategy beats power.</p>", new)
    def test_text_across_tags_kept(self):
        self.ok(ed("Make an inquiry</a><p>Our", "Send an inquiry</a><p>Our"))
    def test_link_change(self): self.held(ed('href="../contact-us/">Make', 'href="https://evil.example/">Make'), "tags, links")
    def test_new_tag(self): self.held(ed("raw distance.</p>", "raw distance.</p><script>x()</script>"), "tags, links")
    def test_inside_attribute(self): self.held(ed("Three courses", "Four courses"), "inside a tag")
    def test_inside_script(self): self.held(ed('"raw distance"', '"power"'), "script, form")
    def test_inside_form(self): self.held(ed("<label>Name</label>", "<label>Full name</label>"), "script, form")
    def test_inside_style(self): self.held(ed("color:red", "color:blue"), "script, form")
    def test_title_allowed(self): self.ok(ed("<title>Golf |", "<title>Our Courses |"))
    def test_not_unique(self): self.held(ed("raw distance", "power"), "exactly one")
    def test_missing(self): self.held(ed("Not on the page", "x"), "exactly one")
    def test_em_dash(self): self.held(ed("Strategy beats raw distance.", "Strategy — not distance."), "dash")
    def test_spaced_hyphen(self): self.held(ed("Strategy beats raw distance.", "Strategy - not distance."), "hyphen")
    def test_enquiry(self): self.held(ed("Make an inquiry", "Make an enquiry"), "enquiry")
    def test_emoji(self): self.held(ed("Strategy beats raw distance.", "Strategy beats raw distance. ⛳"), "emoji")
    def test_price(self): self.held(ed("Strategy beats raw distance.", "Green fees from $95."), "dollar")
    def test_tiers_on_memberships(self):
        self.held(ed("Strategy beats raw distance.", "Three membership tiers."), "membership page", page="memberships")
        self.ok(ed("Strategy beats raw distance.", "Three membership tiers."), page="golf")
    def test_staff_name_added(self): self.held(ed("Strategy beats raw distance.", "Ask Laura about it."), "our team")
    def test_staff_name_already_there(self): self.ok(ed("Rhys, golf operations.", "Rhys, golf operations and leagues."))
    def test_new_phone(self): self.held(ed("905-640-3633", "416-555-0199"), "phone")
    def test_same_phone(self): self.ok(ed("Call the pro shop at 905-640-3633.", "Call our pro shop at 905-640-3633."))
    def test_new_email(self): self.held(ed("Strategy beats raw distance.", "Write to someone@example.com."), "email")
    def test_public_dining(self): self.held(ed("Strategy beats raw distance.", "Our restaurant is open to the public."), "public")
    def test_club_name_in_script_font(self):
        self.held(ed("Member Favourite", "Spring Lakes Golf Club"), "script font")
    def test_too_many(self): self.held([ed("Strategy", "Plan")[0]] * 7, "too many")
    def test_empty(self): self.held([], "no change")

class Pages(unittest.TestCase):
    def test_lookup(self):
        f = lambda url: se.page_for({"url": url})
        self.assertEqual(f("https://springlakesgolf.github.io/website/golf/"), "golf")
        self.assertEqual(f("https://springlakesgolf.github.io/website/"), "")
        self.assertEqual(f("http://127.0.0.1:8744/memberships/index.html"), "memberships")
        self.assertEqual(f("http://127.0.0.1:8744/"), "")
        self.assertIsNone(f("https://springlakesgolf.github.io/website/dining-staff/"))
        self.assertIsNone(f("https://springlakesgolf.github.io/website/tools/edit-mode/"))
        self.assertIsNone(f(""))
    def test_branch_page(self):
        self.assertEqual(se.page_of("staff-edit/E12-golf-academy"), "golf-academy")
        self.assertEqual(se.page_of("staff-edit/E7-home"), "home")
        self.assertIsNone(se.page_of("main"))
    def test_allowlist_is_pages_only(self):
        for f in se.PAGES.values():
            self.assertTrue(f.endswith("index.html") and (se.ROOT/f).exists(), f)

class FakeClient:
    """Answers like messages.create with a fixed JSON decision; records every call."""
    def __init__(self, answers): self.answers, self.calls = answers, []
    @property
    def beta(self): return SimpleNamespace(messages=SimpleNamespace(create=self.create))
    def create(self, **kw):
        self.calls.append(kw)
        rid = next(r["id"] for r in ROWS if r["change"] in kw["messages"][0]["content"])
        a = self.answers[rid]
        if a == "refusal": return SimpleNamespace(stop_reason="refusal", content=[])
        return SimpleNamespace(stop_reason="end_turn", content=[SimpleNamespace(type="text", text=json.dumps(a))])

class DryRun(unittest.TestCase):
    def test_fixture_rows(self):
        golf = (se.ROOT/"golf/index.html").read_text()
        find = "plenty of bodies of water"
        self.assertEqual(golf.count(find), 1)
        answers = {
            "E901": {"decision": "edit", "reason": "", "summary": "North Course blurb says ponds and creeks.", "edits": ed(find, "ponds and creeks")},
            "E902": {"decision": "needs_cullen", "reason": "Prices never go on the membership page.", "summary": "", "edits": []},
            # a model that slips is still caught by the code
            "E903": {"decision": "edit", "reason": "", "summary": "x", "edits": ed("Member Favourite", "Member Favourite \N{EM DASH} Since 1983")},
            "E904": {"decision": "edit", "reason": "", "summary": "x", "edits": ed("Signature Layout</", "Signature Layout<script>alert(1)</script></")},
            "E907": "refusal"}
        client = FakeClient(answers)
        with open(os.devnull, "w") as quiet:
            old, sys.stdout = sys.stdout, quiet
            try: results, failed = se.run(ROWS, client, dry=True)
            finally: sys.stdout = old
        got = {r["id"]: r for r in results}
        self.assertEqual(failed, 0)
        self.assertEqual(got["E901"]["status"], "PR open")
        for rid in ("E902", "E903", "E904", "E905", "E906", "E907"): self.assertEqual(got[rid]["status"], "Needs Cullen", rid)
        self.assertIn("dash", got["E903"]["note"]); self.assertIn("tags", got["E904"]["note"])
        self.assertIn("photo", got["E905"]["note"]); self.assertIn("page", got["E906"]["note"])
        # photo and unknown page never reach Claude
        self.assertEqual(len(client.calls), 5)
        kw = client.calls[0]
        self.assertEqual(kw["model"], "claude-sonnet-5-5")
        self.assertEqual(kw["output_config"]["format"]["type"], "json_schema")
        self.assertEqual((se.ROOT/"golf/index.html").read_text(), golf, "dry run leaves the page alone")

class Replay(unittest.TestCase):
    def test_build_replays_edits(self):
        sys.path.insert(0, str(se.ROOT/"tools"))
        try: import build
        except Exception as e: self.skipTest(f"build.py needs the June source: {e}")
        with tempfile.TemporaryDirectory() as d:
            build.STAFF_EDITS = Path(d)
            Path(d, "E3.json").write_text(json.dumps({"id": "E3", "file": "golf/index.html", "changes": ed("raw", "pure")}))
            Path(d, "E10.json").write_text(json.dumps({"id": "E10", "file": "golf/index.html", "changes": ed("pure distance", "power")}))
            Path(d, "E4.json").write_text(json.dumps({"id": "E4", "file": "index.html", "changes": ed("raw", "x")}))
            self.assertEqual(build.staff_edits("golf/index.html", "<p>Strategy beats raw distance.</p>"), "<p>Strategy beats power.</p>")
            # already in the source: nothing to do
            self.assertEqual(build.staff_edits("index.html", "<p>x marks it</p>"), "<p>x marks it</p>")
            with self.assertRaises(SystemExit): build.staff_edits("golf/index.html", "<p>Something else.</p>")

class Endpoint(unittest.TestCase):
    def test_pending_and_result_via_mock(self):
        port = "8746"
        with tempfile.TemporaryDirectory() as d:
            env = {**os.environ, "SLG_MOCK_RESULTS": str(Path(d)/"results.json")}
            srv = subprocess.Popen([sys.executable, str(HERE/"mock_server.py"), port], env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            try:
                time.sleep(0.6)
                os.environ.update(SLG_EDIT_EXEC=f"http://127.0.0.1:{port}/exec", EDITS_BOT_SECRET="testsecret")
                rows = se.endpoint({"action": "pending"})["rows"]
                self.assertEqual([r["id"] for r in rows], [r["id"] for r in ROWS][:5])
                self.assertNotIn("name", rows[0])
                se.endpoint({"action": "result", "id": "E901", "status": "PR open", "pr": "https://github.com/springlakesgolf/website/pull/1", "note": "ok"})
                self.assertEqual(json.loads((Path(d)/"results.json").read_text())[0]["status"], "PR open")
                os.environ["EDITS_BOT_SECRET"] = "wrong"
                with self.assertRaises(RuntimeError): se.endpoint({"action": "pending"})
            finally:
                srv.terminate(); srv.wait()
                for k in ("SLG_EDIT_EXEC", "EDITS_BOT_SECRET"): os.environ.pop(k, None)

if __name__ == "__main__":
    unittest.main()
