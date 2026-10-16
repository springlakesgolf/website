"""Turn the June 2026 redesign into a review build with the live site's URLs."""
import json, os, re, shutil, sys
from pathlib import Path

SRC = Path.home()/"Downloads/Marketing & Promotions/springlakes-site"
OUT = Path.home()/"Projects/springlakes-website"

SLUG = {  # June file -> live URL folder ('' = home)
    "index.html": "", "golf.html": "golf", "golf-academy.html": "golf-academy",
    "golf-camps.html": "golf-camps", "memberships.html": "memberships",
    "members.html": "members", "events.html": "events-spring-lakes",
    "dining.html": "food-beverage", "course-gallery.html": "course-gallery",
    "contact.html": "contact-us",
}
# member-only or pricing documents never go on a public preview
PRIVATE_DOCS = {"2026-JI-Renewal.pdf", "2026-Junior-Renewal.pdf",
                "2026-Member-Calendar.pdf", "2026-Renewal-Form.pdf"}

PREVIEW_HEAD = ('<meta name="robots" content="noindex,nofollow">'
  '<style>.preview-pill{position:fixed;left:12px;bottom:12px;z-index:9999;background:#B89A2D;color:#323C60;'
  'font:600 11px/1 Montserrat,sans-serif;letter-spacing:.12em;text-transform:uppercase;padding:9px 12px;'
  'border-radius:4px;box-shadow:0 2px 10px rgba(0,0,0,.25)}.preview-note{background:#f6f1e3;border-left:3px solid #B89A2D;'
  'padding:12px 16px;margin:0 0 24px;font-size:.92rem;color:#323C60}</style>')
PREVIEW_PILL = '<div class="preview-pill" aria-hidden="true">Staff preview</div>'
# "Suggest an edit" mode: Apps Script URL from tools/edit-mode/config.json,
# or SLG_EDIT_EXEC to point a test build at a mock
EDIT_DIR = OUT/"tools/edit-mode"

def edit_exec():
    if os.environ.get("SLG_EDIT_EXEC"): return os.environ["SLG_EDIT_EXEC"]
    cfg = EDIT_DIR/"config.json"
    return json.loads(cfg.read_text()).get("exec") if cfg.exists() else None

def rel(prefix, m):
    page, frag = m.group(1), m.group(2) or ""
    if page not in SLUG: return m.group(0)
    s = SLUG[page]
    return f'href="{prefix}{s + "/" if s else ""}{frag}"' if (s or frag) else f'href="{prefix or "./"}"'

def build():
    if OUT.joinpath("index.html").exists():
        for p in OUT.iterdir():
            if p.name not in {".git", ".gitignore", "README.md", "tools", ".claude"}:
                shutil.rmtree(p) if p.is_dir() else p.unlink()
    shutil.copytree(SRC/"assets", OUT/"assets", ignore=shutil.ignore_patterns(".DS_Store", "video", *PRIVATE_DOCS))
    exec_url = edit_exec()
    if exec_url:
        (OUT/"assets/js/edit-mode.js").write_text((EDIT_DIR/"edit-mode.js").read_text().replace("__EXEC_URL__", exec_url))
    for f, slug in SLUG.items():
        prefix = "../" if slug else ""
        s = (SRC/f).read_text()
        s = re.sub(r'href="([a-z-]+\.html)(#[^"]*)?"', lambda m: rel(prefix, m), s)
        s = s.replace('src="assets/', f'src="{prefix}assets/').replace('href="assets/', f'href="{prefix}assets/')
        s = s.replace('poster="assets/', f'poster="{prefix}assets/')
        s = s.replace("<head>", "<head>" + PREVIEW_HEAD, 1)
        tail = PREVIEW_PILL + (f'<script src="{prefix}assets/js/edit-mode.js" defer></script>' if exec_url else "")
        s = s.replace("</body>", tail + "</body>", 1)
        s = re.sub(r' data-to="[^"]*"', "", s)
        s = edit(f, s)
        for bad in ("—", "–", "SLGC2026", "Renewal-Form.pdf", "Member-Calendar.pdf", "b-num"):
            assert bad not in s, (f, bad)
        dest = OUT/slug/"index.html" if slug else OUT/"index.html"
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(s)
    # the live /tournaments/ page is leftover template copy; send it to events
    (OUT/"tournaments").mkdir(exist_ok=True)
    (OUT/"tournaments/index.html").write_text(
        '<!doctype html><meta charset="utf-8"><meta name="robots" content="noindex">'
        '<meta http-equiv="refresh" content="0; url=../events-spring-lakes/">'
        '<link rel="canonical" href="../events-spring-lakes/"><a href="../events-spring-lakes/">Events</a>')
    # preview forms send nothing; they get wired to the inquiry sheet at launch
    js = OUT/"assets/js/site.js"; t = js.read_text()
    a = t.find("document.querySelectorAll('.inquiry-form')"); b = t.find("\n", a)
    assert a > 0, "site.js forms"
    t = t[:a] + ("document.querySelectorAll('.inquiry-form').forEach(function(f){f.addEventListener('submit',function(e){"
        "e.preventDefault();var n=f.querySelector('.form-note');if(n){n.style.display='block';"
        "n.textContent='Preview only. This form is not connected yet, so nothing was sent.';}})});") + t[b:]
    js.write_text(t)
    # June CSS: the mobile .btn padding squeezed the menu icon to 4px wide
    css = OUT/"assets/css/style.css"
    css.write_text(css.read_text() + "\n.btn.menu-toggle{padding:8px;gap:0}.menu-toggle svg{flex-shrink:0}\n")
    (OUT/".nojekyll").write_text("")
    (OUT/"robots.txt").write_text("User-agent: *\nDisallow: /\n")

def sub(s, old, new, f):
    assert old in s, (f, old[:60])
    return s.replace(old, new)

def cut(s, start, end, new, f):
    i = s.find(start); j = s.find(end, i)
    assert i >= 0 and j > i, (f, start[:50])
    return s[:i] + new + s[j:]

def edit(f, s):
    if f == "index.html":
        s = sub(s, '<div class="badge"><div class="b-num">10</div><div class="b-txt">Years of Spring Lakes</div></div>', "", f)
        s = re.sub(r'<video src="assets/video/[^"]*"[^>]*poster="([^"]*)"[^>]*></video>',
                   r'<img src="\1" alt="Aerial view over Spring Lakes">', s)
        assert "<video" not in s, f
        s = cut(s, '<section class="cta-band">', "<footer", "", f)
        s = sub(s, "2026 weeks are now sold out.", "2027 dates are coming soon.", f)
    if f == "memberships.html":
        i = s.find('<main id="main">') + len('<main id="main">')
        j = s.find('<section><div class="container narrow"><div class="section-head center"><span class="eyebrow reveal">Inquire')
        assert i > 20 and j > i, f
        s = s[:i] + ('<section><div class="container narrow center"><span class="eyebrow reveal">Membership</span>'
          '<h2 class="reveal d1" style="font-size:clamp(2rem,4vw,3rem)">Membership by inquiry</h2>'
          '<p class="lead-text reveal d2" style="margin:1rem auto 0">Spring Lakes is a private club. Tell us a little about how you '
          'like to play and our team will be in touch with current availability and the details for the membership that suits you.</p>'
          '<div class="reveal d3" style="margin-top:1.6rem"><a class="btn btn-gold" href="#inquire">Make an Inquiry</a></div>'
          '</div></section>') + s[j:]
        s = sub(s, '<div class="field"><label for="if-m">Message</label>',
          '<div class="field"><label for="if-t">What are you interested in?</label><select name="interest" id="if-t">'
          '<option value="">Choose one</option><option>Playing membership</option><option>Junior golf</option>'
          '<option>Social membership (clubhouse)</option><option>Not sure yet</option></select></div>'
          '<div class="field"><label for="if-y">When would you like to join?</label><select name="year" id="if-y">'
          '<option value="">Choose one</option><option>2027 season</option><option>2028 or later</option></select></div>'
          '<div class="field"><label for="if-r">Referred by a member? (optional)</label><input name="referral" id="if-r" type="text"></div>'
          '<div class="field"><label for="if-m">Message</label>', f)
    if f == "golf-camps.html":
        s = sub(s, "All 2026 camp weeks are sold out", "2027 camp dates are coming soon", f)
        s = re.sub(r"Thank you\. Every week of our 2026 junior camps has been filled\. To join the waitlist or to hear first when 2027 dates open,",
                   "Our 2026 camps were a full house. To hear first when 2027 dates and registration open,", s)
        s = s.replace("Join the Waitlist", "Get on the List")
    if f == "contact.html":
        s = re.sub(r' ·\s*<a href="mailto:[a-z]+@springlakesgolf\.com"[^>]*>[a-z]+@springlakesgolf\.com</a>', "", s)
        assert not re.search(r'(braeden|luke|cullen|rhys|laura|ashley|kelly|chris)@', s), f
    if f == "golf.html":
        s = re.sub(r'<a [^>]*href="assets/docs/[A-Za-z]+-Scorecard\.pdf"[^>]*>.*?</a>', "", s)
        s = re.sub(r'<a [^>]*href="\.\./assets/docs/[A-Za-z]+-Scorecard\.pdf"[^>]*>.*?</a>', "", s)
        assert "Scorecard.pdf" not in s, f
    if f == "members.html":
        s = re.sub(r'<script>\(function\(\)\{var fm=document\.getElementById\("memform"\).*?</script>', "", s, flags=re.S)
        s = cut(s, '<div id="memgate"', '<div id="memarea"', '<p class="preview-note">Preview: at launch this page sits behind the '
                'member password, checked on the server. Member documents (calendar, renewal forms) are added then.</p>', "members")
        s = sub(s, '<div id="memarea" hidden>', '<div id="memarea">', f)
        k = s.find("Member Documents"); i = s.rfind("<section", 0, k); j = s.find("</section>", k) + len("</section>")
        assert k > 0 and i > 0, f
        s = s[:i] + s[j:]
        s = re.sub(r'<p class="note"[^>]*>Prefer a paper form\?.*?</p>', "", s, flags=re.S)
        s = re.sub(r'<select([^>]*id="[^"]*")[^>]*>(?:(?!</select>).)*?Junior Intermediate.*?</select>',
                   lambda m: '<input type="text"' + m.group(1) + '>', s, count=1, flags=re.S)
        assert "Junior Intermediate" not in s, f
    return s

if __name__ == "__main__":
    build(); print("built", OUT)
