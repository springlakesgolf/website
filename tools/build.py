"""Turn the June 2026 redesign into a review build with the live site's URLs."""
import html, json, os, re, shutil, sys
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

# members page "This Week" band: 7-day ECCC forecast and the latest club
# Mailchimp campaigns, both rendered by tools/members/weather.js; the emails come
# from assets/data/club-emails.json, refreshed hourly by a GitHub Action
sys.path.insert(0, str(OUT/"tools/members"))
import club_emails

def this_week(mails):
    li = "".join(f'<li><a href="{html.escape(m["link"])}" target="_blank" rel="noopener"><span class="mc-date">'
                 f'{m["label"]}</span><span class="mc-title">{html.escape(m["title"])}</span></a></li>' for m in mails)
    news = (f'<div id="mc-col"><h3>Latest club emails</h3><ul id="mc-list" class="mc-list">{li}</ul>'
            f'<a class="mc-all" href="{club_emails.HOME}" target="_blank" rel="noopener">See all club emails</a></div>') if li else ""
    side = ('<div id="side-col" class="reveal d2"><div id="hours-wrap" hidden><h3>Club hours</h3>'
            '<div id="hours-box" class="hr-list" data-scope="members" aria-live="polite"></div></div>' + news + '</div>')
    return ('<section id="this-week" class="week-band"><div class="container"><div class="reveal">'
      '<span class="eyebrow">This Week</span><h2>Weather and club news</h2></div>'
      '<div class="week-grid"><div id="wx-col" class="reveal d1"><h3>7-day forecast</h3>'
      '<div id="wx-days" class="wx-days" aria-busy="true" aria-live="polite"></div>'
      '<p class="wx-src">Forecast for the Markham area. Data Source: Environment and Climate Change Canada.</p></div>'
      f'{side}</div></div></section>'
      '<section id="lost-found" class="bg-cream"><div class="container narrow"><div class="section-head center">'
      '<span class="eyebrow reveal">Lost &amp; Found</span><h2 class="reveal d1">Lost something at the club?</h2>'
      '<p class="reveal d2">Clubs and other items turned in to the pro shop and clubhouse. If one is yours, call the pro shop at '
      '<a href="tel:9056403633" style="color:var(--gold)">905-640-3633</a> or stop in to pick it up.</p></div>'
      '<ul id="lost-box" class="lf-list reveal d2" aria-live="polite"><li class="lf-empty">Checking the list</li></ul></div></section>')

NAV_CSS = """
/* top menu without a dropdown, and the golf pages' tab row */
.nav-links{gap:30px}
.subnav{background:#fff;border-bottom:1px solid var(--line);position:relative;z-index:5}
.subnav .container{display:flex;gap:36px;overflow-x:auto;scrollbar-width:none}
.subnav .container::-webkit-scrollbar{display:none}
.subnav a{flex:none;padding:18px 0 16px;font-size:.92rem;font-weight:500;color:var(--muted);border-bottom:2px solid transparent;transition:color .2s,border-color .2s}
.subnav a:hover{color:var(--navy)}
.subnav a[aria-current="page"]{color:var(--navy);font-weight:600;border-bottom-color:var(--gold)}
@media(max-width:700px){.subnav .container{gap:24px}.subnav a{font-size:.88rem;padding:15px 0 13px}}
/* text no longer fades in on scroll; photos and the home page opening keep a quiet entrance */
.reveal{opacity:1;transform:none;transition:none}
@media(prefers-reduced-motion:no-preference){
.figure-wrap.reveal,.course-card.reveal,.pro-card.reveal,.gallery.reveal{opacity:0;transform:translateY(14px);transition:opacity .9s var(--ease),transform .9s var(--ease)}
.hero-mark.reveal,.hero-title.reveal,.hero-place.reveal,.hero-cta.reveal{opacity:0;transform:translateY(18px);transition:opacity .8s var(--ease),transform .8s var(--ease)}
.figure-wrap.reveal.in,.course-card.reveal.in,.pro-card.reveal.in,.gallery.reveal.in,.hero-mark.reveal.in,.hero-title.reveal.in,.hero-place.reveal.in,.hero-cta.reveal.in{opacity:1;transform:none}
.reveal.d1{transition-delay:.08s}.reveal.d2{transition-delay:.16s}.reveal.d3{transition-delay:.24s}}
"""

WEEK_CSS = """
.week-band{background:var(--navy);color:#fff}
.week-band h2{color:#fff;font-size:clamp(2rem,4vw,2.8rem);margin-bottom:1.6rem}
.week-band h3{color:#fff;font-size:1.45rem;margin:0 0 1rem}
.week-grid{display:grid;grid-template-columns:1.55fr 1fr;gap:40px;align-items:start}.week-grid.one{grid-template-columns:1fr}
.wx-days{display:grid;grid-template-columns:repeat(7,minmax(0,1fr));gap:8px}
.wx-day{background:rgba(255,255,255,.06);border:1px solid rgba(255,255,255,.12);border-radius:var(--radius);padding:14px 6px;text-align:center}
.wx-name{font-size:.7rem;font-weight:600;letter-spacing:.14em;text-transform:uppercase;color:var(--gold-soft)}
.wx-ico{width:34px;height:34px;margin:10px auto;color:#fff;display:block}
.wx-temp b{font-size:1.15rem;font-weight:600;margin-right:6px}.wx-temp span{color:rgba(255,255,255,.62);font-size:.92rem}
.wx-text{font-size:.72rem;line-height:1.35;color:rgba(255,255,255,.78);margin-top:6px}.wx-text em{font-style:normal;color:var(--gold-soft)}
.wx-src{font-size:.74rem;color:rgba(255,255,255,.55);margin:12px 0 0}
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

#side-col h3{margin-top:0}#hours-wrap{margin-bottom:30px}
.hr-list{border-top:1px solid rgba(255,255,255,.14)}
.hr-row{display:flex;justify-content:space-between;gap:16px;padding:12px 0;border-bottom:1px solid rgba(255,255,255,.14);align-items:baseline}
.hr-what{font-size:.95rem}.hr-note{font-size:.76rem;color:rgba(255,255,255,.6);margin-top:2px}
.hr-time{font-size:.9rem;font-weight:600;color:var(--gold-soft);text-align:right;white-space:nowrap}
.hours-public{margin-top:30px}.hours-public .hr-list{border-color:var(--line)}
.hours-public .hr-row{border-color:var(--line)}.hours-public .hr-what{color:var(--navy);font-weight:600}
.hours-public .hr-note{color:var(--muted)}.hours-public .hr-time{color:var(--gold)}
.lf-list{list-style:none;margin:0 auto;padding:0;max-width:720px;background:#fff;border:1px solid var(--line);border-radius:var(--radius)}
.lf-item,.lf-empty{display:flex;gap:18px;align-items:baseline;padding:16px 20px;border-bottom:1px solid var(--line)}
.lf-list li:last-child{border-bottom:0}
.lf-empty{justify-content:center;color:var(--muted);font-size:.95rem}
.lf-date{flex:0 0 60px;font-size:.72rem;font-weight:600;letter-spacing:.12em;text-transform:uppercase;color:var(--gold)}
.lf-what{flex:1;color:var(--navy);font-weight:600}.lf-where{display:block;font-weight:400;color:var(--muted);font-size:.88rem}
.lf-photo{font-size:.74rem;font-weight:600;letter-spacing:.12em;text-transform:uppercase;color:var(--gold);border-bottom:1px solid currentColor}
"""

# no dropdown in the top menu: Golf is one link, and the four golf pages share a
# tab row under the page header; the logo is the way home
GOLF_PAGES = [("golf", "Courses"), ("golf-academy", "Golf Academy"), ("golf-camps", "Golf Camps"), ("course-gallery", "Course Gallery")]

def flat_nav(s, slug, prefix):
    golf = slug in dict(GOLF_PAGES)
    cur = ' aria-current="page"'
    s, n = re.subn(r'<li class="has-sub"><a href="([^"]*golf/)"[^>]*>Golf <svg.*?</svg></a><ul class="submenu">.*?</ul></li>',
                   lambda m: f'<li><a href="{m.group(1)}"{cur if golf else ""}>Golf</a></li>', s, count=1, flags=re.S)
    assert n == 1, (slug, "golf menu")
    s, n = re.subn(r'<li><a href="[^"]*"( aria-current="page")?>Home</a></li>', "", s, count=1)
    assert n == 1, (slug, "home link")
    if golf:
        tabs = "".join(f'<a href="{prefix}{g}/"{cur if g == slug else ""}>{label}</a>' for g, label in GOLF_PAGES)
        i = s.find('class="page-hero"'); j = s.find("</section>", i) + len("</section>")
        assert i > 0 and j > i, (slug, "page hero")
        s = s[:j] + f'<nav class="subnav" aria-label="Golf pages"><div class="container">{tabs}</div></nav>' + s[j:]
    return s

def rel(prefix, m):
    page, frag = m.group(1), m.group(2) or ""
    if page not in SLUG: return m.group(0)
    s = SLUG[page]
    return f'href="{prefix}{s + "/" if s else ""}{frag}"' if (s or frag) else f'href="{prefix or "./"}"'

def build():
    if OUT.joinpath("index.html").exists():
        for p in OUT.iterdir():
            if p.name not in {".git", ".github", ".gitignore", ".impeccable", "README.md", "PRODUCT.md", "DESIGN.md", "tools", ".claude"}:
                shutil.rmtree(p) if p.is_dir() else p.unlink()
    shutil.copytree(SRC/"assets", OUT/"assets", ignore=shutil.ignore_patterns(".DS_Store", "video", *PRIVATE_DOCS))
    global MAILS
    MAILS = club_emails.write()
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
        s = flat_nav(s, slug, prefix)
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
    css.write_text(css.read_text() + "\n.btn.menu-toggle{padding:8px;gap:0}.menu-toggle svg{flex-shrink:0}\n" + WEEK_CSS + NAV_CSS)
    shutil.copy(OUT/"tools/members/weather.js", OUT/"assets/js/weather.js")
    if exec_url:
        (OUT/"assets/js/content.js").write_text((OUT/"tools/members/content.js").read_text().replace("__EXEC_URL__", exec_url))
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
        s = sub(s, '<h3 style="font-size:1.5rem;margin:34px 0 6px">Staff Directory</h3>',
                '<div id="hours-wrap" class="hours-public" hidden><h3 style="font-size:1.5rem;margin:0 0 6px">Hours</h3>'
                '<div id="hours-box" class="hr-list" data-scope="public" aria-live="polite"></div></div>'
                '<h3 style="font-size:1.5rem;margin:34px 0 6px">Staff Directory</h3>', f)
        s = s.replace("</body>", '<script src="../assets/js/content.js" defer></script></body>', 1)
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
                '</section>' + this_week(MAILS) + '<section><div class="container split"><div class="figure-wrap reveal"><div class="figure-frame ratio-54"><img src="../assets/img/member-leagues.webp"', f)
        s = s.replace("</body>", '<script src="../assets/js/weather.js" defer></script><script src="../assets/js/content.js" defer></script></body>', 1)
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
