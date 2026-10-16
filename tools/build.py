"""Turn the June 2026 redesign into a review build with the live site's URLs."""
import email.utils, html, json, os, re, shutil, sys, urllib.request
import xml.etree.ElementTree as ET
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

# members page "This Week" band: club Mailchimp campaigns (public archive feed)
# and a 7-day ECCC forecast loaded in the browser by tools/members/weather.js
MC_FEED = "https://us13.campaign-archive.com/feed?u=40d74683558e83493d58aafed&id=1872afdeb6"
MC_HOME = "https://us13.campaign-archive.com/home/?u=40d74683558e83493d58aafed&id=1872afdeb6"

def club_emails(n=5):
    """Latest campaigns, newest first. Mailchimp lists resends and test splits
    as separate items with the same title, so keep only the newest of each."""
    try:
        with urllib.request.urlopen(MC_FEED, timeout=20) as r:
            items = ET.fromstring(r.read()).findall(".//item")
    except Exception as e:
        print("club emails: feed unavailable,", e); return []
    out, seen = [], set()
    for it in items:
        title = (it.findtext("title") or "").strip()
        if not title or title.lower() in seen: continue
        seen.add(title.lower())
        when = email.utils.parsedate_to_datetime(it.findtext("pubDate"))
        out.append((when, title, it.findtext("link")))
    return sorted(out, reverse=True)[:n]

def this_week():
    mails = club_emails()
    li = "".join(f'<li><a href="{html.escape(link)}" target="_blank" rel="noopener"><span class="mc-date">'
                 f'{w.strftime("%b")} {w.day}</span><span class="mc-title">{html.escape(t)}</span></a></li>' for w, t, link in mails)
    news = f'<ul class="mc-list">{li}</ul>' if li else '<p class="wx-off">Club emails are not loading right now.</p>'
    return ('<section id="this-week" class="week-band"><div class="container"><div class="reveal">'
      '<span class="eyebrow">This Week</span><h2>Weather and club news</h2></div>'
      '<div class="week-grid"><div class="reveal d1"><h3>7-day forecast</h3>'
      '<div id="wx-days" class="wx-days" aria-busy="true" aria-live="polite"><p class="wx-off">Loading the forecast</p></div>'
      '<p class="wx-src">Forecast for the Markham area. Data Source: Environment and Climate Change Canada.</p></div>'
      f'<div class="reveal d2"><h3>Latest club emails</h3>{news}'
      f'<a class="mc-all" href="{MC_HOME}" target="_blank" rel="noopener">See all club emails</a></div>'
      '</div></div></section>')

WEEK_CSS = """
.week-band{background:var(--navy);color:#fff}
.week-band h2{color:#fff;font-size:clamp(2rem,4vw,2.8rem);margin-bottom:1.6rem}
.week-band h3{color:#fff;font-size:1.45rem;margin:0 0 1rem}
.week-grid{display:grid;grid-template-columns:1.55fr 1fr;gap:40px;align-items:start}
.wx-days{display:grid;grid-template-columns:repeat(7,minmax(0,1fr));gap:8px}
.wx-day{background:rgba(255,255,255,.06);border:1px solid rgba(255,255,255,.12);border-radius:var(--radius);padding:14px 6px;text-align:center}
.wx-name{font-size:.7rem;font-weight:600;letter-spacing:.14em;text-transform:uppercase;color:var(--gold-soft)}
.wx-ico{width:34px;height:34px;margin:10px auto;color:#fff;display:block}
.wx-temp b{font-size:1.15rem;font-weight:600;margin-right:6px}.wx-temp span{color:rgba(255,255,255,.62);font-size:.92rem}
.wx-text{font-size:.72rem;line-height:1.35;color:rgba(255,255,255,.78);margin-top:6px}.wx-text em{font-style:normal;color:var(--gold-soft)}
.wx-src{font-size:.74rem;color:rgba(255,255,255,.55);margin:12px 0 0}
.wx-off{color:rgba(255,255,255,.75);font-size:.92rem}.wx-off a{color:var(--gold-soft);text-decoration:underline}
.mc-list{list-style:none;margin:0;padding:0;border-top:1px solid rgba(255,255,255,.14)}
.mc-list li{border-bottom:1px solid rgba(255,255,255,.14)}
.mc-list a{display:flex;gap:16px;padding:13px 0;align-items:baseline}
.mc-list a:hover .mc-title{color:var(--gold-soft)}
.mc-date{flex:0 0 52px;font-size:.72rem;font-weight:600;letter-spacing:.12em;text-transform:uppercase;color:var(--gold-soft)}
.mc-title{font-size:.95rem;line-height:1.45;transition:color .2s}
.mc-all{display:inline-block;margin-top:16px;font-size:.78rem;font-weight:600;letter-spacing:.12em;text-transform:uppercase;color:var(--gold-soft);border-bottom:1px solid currentColor}
@media(max-width:900px){.week-grid{grid-template-columns:1fr;gap:32px}
.wx-days{grid-template-columns:none;grid-auto-flow:column;grid-auto-columns:minmax(96px,1fr);overflow-x:auto;padding-bottom:6px;scroll-snap-type:x mandatory}
.wx-day{scroll-snap-align:start}}
"""

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
    css.write_text(css.read_text() + "\n.btn.menu-toggle{padding:8px;gap:0}.menu-toggle svg{flex-shrink:0}\n" + WEEK_CSS)
    shutil.copy(OUT/"tools/members/weather.js", OUT/"assets/js/weather.js")
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
        # 2027 forms: categories differ by tier, so no blanket "unlimited golf" claim
        s = sub(s, "Unlimited golf across three courses, a clubhouse built for the whole family, and a calendar that fills the season, with no hidden minimums.",
                "Three championship courses, a clubhouse built for the whole family, and a calendar that fills the season, with no clubhouse minimums.", f)
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
        s = sub(s, '</section><section><div class="container split"><div class="figure-wrap reveal"><div class="figure-frame ratio-54"><img src="../assets/img/member-leagues.webp"',
                '</section>' + this_week() + '<section><div class="container split"><div class="figure-wrap reveal"><div class="figure-frame ratio-54"><img src="../assets/img/member-leagues.webp"', f)
        s = s.replace("</body>", '<script src="../assets/js/weather.js" defer></script></body>', 1)
        k = s.find("Member Documents"); i = s.rfind("<section", 0, k); j = s.find("</section>", k) + len("</section>")
        assert k > 0 and i > 0, f
        s = s[:i] + s[j:]
        s = re.sub(r'<p class="note"[^>]*>Prefer a paper form\?.*?</p>', "", s, flags=re.S)
        s = re.sub(r'<select([^>]*id="[^"]*")[^>]*>(?:(?!</select>).)*?Junior Intermediate.*?</select>',
                   lambda m: '<input type="text"' + m.group(1) + '>', s, count=1, flags=re.S)
        assert "Junior Intermediate" not in s, f
        # match the final 2027 membership forms
        s = sub(s, "<li>Juniors are 17 and under and may only play accompanied by an adult member.</li>",
                "<li>Junior memberships are for golfers 18 and under and must be linked to an adult membership. Junior tee times start from 11 am and juniors may not use carts, unless approved by management.</li>"
                "<li>Junior and junior intermediate members may bring up to two guests per visit, unless approved by management.</li>", f)
        s = sub(s, "One form for every category. Send it through and the office will confirm your renewal and arrange payment by e-transfer, cheque or another method.",
                "One form for every category. Renewals are due by January 15, 2027, and payment by January 31, 2027. Send it through and the office will confirm your renewal and arrange payment.", f)
        s = sub(s, "<option>E-transfer</option><option>Cheque</option><option>Call me to arrange</option><option>Other</option>",
                "<option>E-transfer</option><option>One cheque (by January 31)</option><option>Two cheques (January 31 and March 31)</option>"
                "<option>Credit card (service fee applies)</option><option>Call me to arrange</option>", f)
    return s

if __name__ == "__main__":
    build(); print("built", OUT)
