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
                "2026-Member-Calendar.pdf", "2026-Renewal-Form.pdf",
                # menu and wine list are members only (review 2026-10-16 item 4)
                "Restaurant-Menu.pdf", "Wine-List.pdf"}
# winter lessons are no longer offered (Braeden, 2026-10-16, E4/E5)
RETIRED_DOCS = {"Winter-Lessons-Rhys.pdf", "Winter-Programming-Braeden.pdf"}

PREVIEW_HEAD = ('<meta name="robots" content="noindex,nofollow">'
  '<style>.preview-pill{position:fixed;left:12px;bottom:12px;z-index:9999;background:#B89A2D;color:#323C60;'
  'font:600 11px/1 Montserrat,sans-serif;letter-spacing:.12em;text-transform:uppercase;padding:9px 12px;'
  'border-radius:4px;box-shadow:0 2px 10px rgba(0,0,0,.25)}.preview-note{background:#f6f1e3;border-left:3px solid #B89A2D;'
  'padding:12px 16px;margin:0 0 24px;font-size:.92rem;color:#323C60}</style>')
PREVIEW_PILL = '<div class="preview-pill" aria-hidden="true">Staff preview</div>'
# "Suggest an edit" mode: Apps Script URL from tools/edit-mode/config.json,
# or SLG_EDIT_EXEC to point a test build at a mock
EDIT_DIR = OUT/"tools/edit-mode"

# text edits opened as PRs by the staff-edits Action (W2), one file per sheet row; replayed after
# the fixes below so a rebuild keeps them. Delete a file once the June source has the change.
STAFF_EDITS = EDIT_DIR/"staff-edits"

def staff_edits(page, s):
    for p in sorted(STAFF_EDITS.glob("E*.json"), key=lambda p: int(p.stem[1:])):
        e = json.loads(p.read_text())
        if e["file"] != page: continue
        for c in e["changes"]:
            if s.count(c["find"]) == 1: s = s.replace(c["find"], c["replace"])
            elif c["replace"] not in s:
                raise SystemExit(f"{p.name}: its old text is no longer on {page}; redo the edit or delete the file")
    return s

def edit_exec():
    if os.environ.get("SLG_EDIT_EXEC"): return os.environ["SLG_EDIT_EXEC"]
    cfg = EDIT_DIR/"config.json"
    return json.loads(cfg.read_text()).get("exec") if cfg.exists() else None

# "Reserve a table" panel on the Dining page: Apps Script URL from
# tools/dining/config.json, or SLG_DINING_EXEC to point a test build at a mock.
# With neither set, the panel is not built or injected.
DINING_DIR = OUT/"tools/dining"

def dining_exec():
    # A mock build passes SLG_DINING_EXEC. config.json is what ships, so it can never
    # point at a local or plain http address.
    if os.environ.get("SLG_DINING_EXEC"): return os.environ["SLG_DINING_EXEC"]
    cfg = DINING_DIR/"config.json"
    url = json.loads(cfg.read_text()).get("exec") if cfg.exists() else None
    if url and (url.lower().startswith("http:") or "localhost" in url.lower()):
        raise SystemExit("tools/dining/config.json exec must be the live https address, not http or localhost "
                         "(use SLG_DINING_EXEC for a mock build)")
    return url

def nodash(name):
    t = (DINING_DIR/name).read_text()
    for bad in ("—", "–"):
        assert bad not in t, (name, bad)
    return t

# Google Forms the site links to (staff edits E6 and E8), built by tools/forms/build_forms.gs.
# Until a link is in tools/forms/config.json the page keeps its phone or inquiry fallback.
FORMS = OUT/"tools/forms/config.json"

def forms():
    return json.loads(FORMS.read_text()) if FORMS.exists() else {}

# membership inquiries post to the Apps Script that writes the "Membership Inquiries" sheet,
# the same endpoint as springlakesgolf.github.io/membership (staff edit E7)
INQUIRY_EXEC = "https://script.google.com/macros/s/AKfycbztt-0KQKXHHbw0jHFwxzUqiNxbCPboNhR5qOKorbzOHpJEfpjUCQMus26GyOLJExzv/exec"

# members page "This Week" band: 7-day ECCC forecast and the latest club
# Mailchimp campaigns, both rendered by tools/members/weather.js; the emails come
# from assets/data/club-emails.json, refreshed hourly by a GitHub Action
sys.path.insert(0, str(OUT/"tools/members"))
import club_emails

def club_items(mails, week):
    # newest first, with the week at a glance tagged where it falls by date
    items = [dict(m, week=False) for m in mails]
    if week: items.append(dict(week, week=True))
    return sorted(items, key=lambda m: m["date"], reverse=True)

def this_week(mails, week):
    # option A (Cullen, 2026-11-01, E11): the latest club email shown right in the page, the recent ones beside it to
    # switch between, club hours and the forecast under them; weather.js swaps in the hourly-refreshed list
    items = club_items(mails, week)
    TAG = '<span class="mc-tag">Week at a glance</span>'
    li = "".join(f'<li><button type="button" data-link="{html.escape(m["link"])}" aria-current="{"true" if i == 0 else "false"}">'
                 f'<span class="mc-date">{m["label"]}</span><span class="mc-title">{html.escape(m["title"])}</span>'
                 f'{TAG if m["week"] else ""}</button></li>' for i, m in enumerate(items))
    first = items[0] if items else None
    news = (f'<div id="mc-col"><div class="mc-frame"><iframe id="mc-frame" src="{html.escape(first["link"])}" '
            f'title="Club email: {html.escape(first["title"])}" loading="lazy"></iframe></div>'
            f'<a id="mc-open" class="mc-all" href="{html.escape(first["link"])}" target="_blank" rel="noopener">Open this email in a new tab</a></div>') if first else ""
    pick = (f'<div id="mc-pick"><h3>Recent emails</h3><ul id="mc-list" class="mc-list">{li}</ul>'
            f'<a class="mc-all" href="{club_emails.HOME}" target="_blank" rel="noopener">See all club emails</a></div>') if first else ""
    side = (f'<aside id="side-col" class="news-side">{pick}<div id="hours-wrap" hidden><h3>Club hours</h3>'
            '<div id="hours-box" class="hr-list" data-scope="members" aria-live="polite"></div></div>'
            '<div id="wx-col"><h3>7-day forecast</h3><div id="wx-days" class="wx-days" aria-busy="true" aria-live="polite"></div>'
            '<p class="wx-src">Forecast for the Markham area. Data Source: Environment and Climate Change Canada.</p></div></aside>')
    return ('<section id="this-week" class="news-band"><div class="container">'
      '<span class="eyebrow">From the Club</span><h2>Club news</h2>'
      f'<div class="week-grid">{news}{side}</div></div></section>')

# tee times first on the members page (E13); the header button jumps here
TEE_BAND = ('<section id="book" class="tee-band"><div class="container"><div><span class="eyebrow">Tee Times</span><h2>Book a tee time</h2>'
  '<p>All three courses, the live tee sheet and your member rates, with your Chronogolf member login. Trouble booking? '
  'Call the pro shop at <a href="tel:9056403633">905-640-3633</a>.</p></div><div class="tee-btns">'
  '<a class="btn btn-gold tee-link" href="https://chronogolf.com/club/18694" target="_blank" rel="noopener">Book a tee time</a>'
  '<a class="btn btn-ghost-navy" href="#leagues">Sign up for leagues</a></div></div></section>')

# events and functions are for members only (Cullen, 2026-10-28, E12): the Events page content moves here
MEMBER_EVENTS = (
  '<section id="events" class="bg-cream"><div class="container"><div class="section-head center"><span class="eyebrow reveal">Events and Functions</span>'
  '<h2 class="reveal d1">Host your event at the club</h2><p class="reveal d2">Corporate days, golf tournaments and celebrations of every size, '
  'with versatile spaces and a team that handles the details. Every event inquiry is handled personally, from the first idea to the day itself.</p></div>'
  '<div class="card-grid two"><article class="course-card reveal"><div class="course-art"><img src="../assets/img/g12.webp" alt=""></div>'
  '<div class="course-body"><h3 style="font-size:1.6rem">Corporate and golf days</h3><p>Adaptable spaces and three championship courses make for a seamless corporate outing or tournament.</p></div></article>'
  '<article class="course-card reveal d2"><div class="course-art"><img src="../assets/img/g28.webp" alt=""></div>'
  '<div class="course-body"><h3 style="font-size:1.6rem">Social celebrations</h3><p>Birthdays, anniversaries and gatherings of every size, with food and service handled by our team.</p></div></article></div>'
  '<div class="ev-form"><h3 id="event-inquiry">Plan your event with us</h3><p>Tell us what you have in mind and we will put together the right space, menu and quote for your occasion.</p>'
  '<form class="inquiry-form" data-subject="Spring Lakes member event inquiry"><div class="field"><label for="ev-n">Name</label><input name="name" id="ev-n" type="text" autocomplete="name" required></div>'
  '<div class="field"><label for="ev-e">Email</label><input name="email" id="ev-e" type="email" autocomplete="email" required></div>'
  '<div class="field"><label for="ev-p">Phone</label><input name="phone" id="ev-p" type="tel" autocomplete="tel"></div>'
  '<div class="field"><label for="ev-m">Message</label><textarea name="message" id="ev-m"></textarea></div>'
  '<button class="btn btn-gold" type="submit">Send inquiry</button><p class="form-note note" style="display:none"></p></form></div></div></section>')

def lost_found():
    # members report what they lost; reception sees the reports, and no items are listed here (staff edit E8)
    url = forms().get("lost")
    btn = (f'<div class="reveal d3" style="margin-top:1.4rem"><a class="btn btn-gold" href="{html.escape(url)}" target="_blank" rel="noopener">'
           'Report a lost item</a></div>') if url else ""
    how = "Tell us what you lost and where you last had it" if url else "Call the pro shop at 905-640-3633 and tell us what you lost and where"
    return ('<section id="lost-found" class="bg-cream"><div class="container narrow"><div class="section-head center" style="margin-bottom:0">'
      '<span class="eyebrow reveal">Lost &amp; Found</span><h2 class="reveal d1">Lost something at the club?</h2>'
      f'<p class="reveal d2">{how}. Our team checks every report against items turned in to the pro shop and clubhouse, and will call you if it turns up.</p>'
      f'{btn}</div></div></section>')

NAV_CSS = """
/* golf camps: sign-up card beside the 2027 flyer */
.camp-card{background:#fff;border:1px solid var(--line);padding:30px;max-width:560px}
.camp-card h2{font-size:2rem;margin-bottom:6px}.camp-card p{color:var(--muted)}
.camp-btns{display:flex;gap:12px;flex-wrap:wrap;margin-top:18px}
.camp-pdf{display:inline-block;margin-top:14px;color:var(--navy);font-weight:600;border-bottom:1px solid var(--gold);padding-bottom:2px;font-size:.92rem}

/* button style A: square, sentence case, no lift on hover */
.btn{font-size:.95rem;letter-spacing:0;text-transform:none;border-radius:0;border-width:1px;transition:background .2s,color .2s,border-color .2s}
.btn:hover{transform:none}
.btn-gold:hover{background:#a3881f;transform:none}
.btn-navy:hover{transform:none}
.btn-ghost{background:transparent;color:#fff;border-color:#fff}
.btn-ghost:hover{background:#fff;color:var(--navy);border-color:#fff}
.btn-ghost-navy{border-color:var(--navy)}
.nav-cta .btn{font-size:.9rem;padding:11px 20px}
/* top menu in normal capitals, and the white dropdown panel */
.nav-links>li>a{font-size:.9rem;letter-spacing:0;text-transform:none}
.submenu{left:-22px;margin:0;min-width:250px;padding:10px 0;background:#fff;border:0;border-radius:0;box-shadow:0 14px 34px rgba(20,26,48,.18),0 2px 6px rgba(20,26,48,.08);transform:none;transition:opacity .15s,visibility .15s}
.has-sub:hover .submenu,.has-sub:focus-within .submenu{transform:none}
.submenu li a{display:flex;justify-content:space-between;align-items:center;gap:16px;padding:11px 22px;color:var(--navy);font-size:.92rem;font-weight:500;letter-spacing:0;text-transform:none}
.submenu li a:hover,.submenu li a:focus-visible,.submenu li a[aria-current]{background:var(--cream);color:var(--navy)}
.submenu .sub-arrow{color:var(--gold);opacity:0;transform:translateX(-4px);transition:opacity .15s,transform .15s}
.submenu li a:hover .sub-arrow,.submenu li a:focus-visible .sub-arrow{opacity:1;transform:none}
.submenu li a:focus-visible{outline:2px solid var(--gold);outline-offset:-2px}
/* text no longer fades in on scroll; photos and the home page opening keep a quiet entrance */
.reveal{opacity:1;transform:none;transition:none}
@media(prefers-reduced-motion:no-preference){
.figure-wrap.reveal,.course-card.reveal,.pro-card.reveal,.gallery.reveal{opacity:0;transform:translateY(14px);transition:opacity .9s var(--ease),transform .9s var(--ease)}
.hero-mark.reveal,.hero-title.reveal,.hero-place.reveal,.hero-cta.reveal{opacity:0;transform:translateY(18px);transition:opacity .8s var(--ease),transform .8s var(--ease)}
.figure-wrap.reveal.in,.course-card.reveal.in,.pro-card.reveal.in,.gallery.reveal.in,.hero-mark.reveal.in,.hero-title.reveal.in,.hero-place.reveal.in,.hero-cta.reveal.in{opacity:1;transform:none}
.reveal.d1{transition-delay:.08s}.reveal.d2{transition-delay:.16s}.reveal.d3{transition-delay:.24s}}
"""

WEEK_CSS = """
.news-band{background:#fff;padding:56px 0 48px}
.news-band h2{font-size:clamp(2rem,4vw,2.8rem);margin:0 0 1.4rem}
.news-band h3{font-size:1.35rem;margin:0 0 .8rem;color:var(--navy)}
.week-grid{display:grid;grid-template-columns:1.6fr 1fr;gap:44px;align-items:start}.week-grid.one{grid-template-columns:1fr}.week-grid>*{min-width:0}
.mc-list{list-style:none;margin:0;padding:0;border-top:1px solid var(--line)}
.mc-list li{border-bottom:1px solid var(--line)}
.mc-list a{display:flex;gap:16px;padding:12px 0;align-items:baseline;color:var(--ink)}
.mc-list a:hover .mc-title{color:var(--gold)}
.mc-date{flex:0 0 52px;font-size:.72rem;font-weight:600;letter-spacing:.12em;text-transform:uppercase;color:var(--gold)}
.mc-title{font-size:.95rem;line-height:1.45;transition:color .2s}
.mc-all{display:inline-block;margin-top:14px;font-size:.78rem;font-weight:600;letter-spacing:.12em;text-transform:uppercase;color:var(--navy);border-bottom:1px solid var(--gold)}
.news-side{background:var(--cream);padding:24px}
.news-side:not(:has(>:not([hidden]))){display:none}
#hours-wrap{margin-bottom:28px}.news-side h3{border-bottom:1px solid rgba(50,60,96,.12);padding-bottom:10px;margin-bottom:0}
.wx-row{display:grid;grid-template-columns:52px 22px 1fr auto;gap:10px;align-items:center;padding:8px 0;border-bottom:1px solid rgba(50,60,96,.12)}
.wx-name{font-size:.72rem;font-weight:600;letter-spacing:.12em;text-transform:uppercase;color:var(--gold)}
.wx-ico{width:22px;height:22px;color:var(--navy);display:block}
.wx-text{font-size:.82rem;color:var(--muted);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.wx-text em{font-style:normal;color:var(--navy)}
.wx-temp{font-size:.88rem;color:var(--muted);white-space:nowrap}.wx-temp b{color:var(--navy);font-weight:600;margin-right:4px}
.wx-src{font-size:.72rem;color:var(--muted);margin:10px 0 0}
@media(max-width:900px){.week-grid{grid-template-columns:1fr;gap:30px}}
.hr-row{display:flex;justify-content:space-between;gap:16px;padding:12px 0;border-bottom:1px solid rgba(50,60,96,.12);align-items:baseline}
.hr-what{font-size:.95rem;font-weight:600;color:var(--navy)}.hr-note{font-size:.78rem;color:var(--muted);margin-top:2px}
.hr-time{font-size:.9rem;font-weight:600;color:var(--gold);text-align:right;white-space:nowrap}
.hours-public{margin-top:30px}.hours-public .hr-list{border-top:1px solid var(--line)}
.hours-public .hr-row{border-color:var(--line)}.hours-public .hr-what{color:var(--navy);font-weight:600}
.hours-public .hr-note{color:var(--muted)}.hours-public .hr-time{color:var(--gold)}
.lf-list{list-style:none;margin:0 auto;padding:0;max-width:720px;background:#fff;border:1px solid var(--line);border-radius:var(--radius)}
.lf-item,.lf-empty{display:flex;gap:18px;align-items:baseline;padding:16px 20px;border-bottom:1px solid var(--line)}
.lf-list li:last-child{border-bottom:0}
.lf-empty{justify-content:center;color:var(--muted);font-size:.95rem}
.lf-date{flex:0 0 60px;font-size:.72rem;font-weight:600;letter-spacing:.12em;text-transform:uppercase;color:var(--gold)}
.lf-what{flex:1;color:var(--navy);font-weight:600}.lf-where{display:block;font-weight:400;color:var(--muted);font-size:.88rem}
.lf-photo{font-size:.74rem;font-weight:600;letter-spacing:.12em;text-transform:uppercase;color:var(--gold);border-bottom:1px solid currentColor}
/* members page option A (E11, E13) */
.tee-band{background:var(--cream);padding:36px 0;scroll-margin-top:90px}#events{scroll-margin-top:90px}
.tee-band .container{display:flex;gap:28px;align-items:center;justify-content:space-between;flex-wrap:wrap}
.tee-band h2{font-size:clamp(1.9rem,3.4vw,2.5rem);margin:.25rem 0 .35rem}.tee-band p{margin:0;color:var(--muted);max-width:640px}
.tee-band p a{color:var(--navy);font-weight:600}.tee-btns{display:flex;gap:12px;flex-wrap:wrap}
.mc-frame{border:1px solid var(--line);height:640px;background:#fff}.mc-frame iframe{width:100%;height:100%;border:0;display:block}
#mc-pick{margin-bottom:28px}#mc-pick .mc-list{border-top:0}
.mc-list button{all:unset;box-sizing:border-box;cursor:pointer;display:flex;flex-wrap:wrap;gap:2px 16px;width:100%;padding:12px 8px;align-items:baseline}
.mc-list button:hover .mc-title{color:var(--gold)}.mc-list button:focus-visible{outline:2px solid var(--gold);outline-offset:-2px}
.mc-list button[aria-current=true]{background:#fff;box-shadow:inset 3px 0 0 var(--gold)}
.mc-tag{flex-basis:100%;padding-left:68px;font-size:.66rem;font-weight:600;letter-spacing:.12em;text-transform:uppercase;color:var(--gold)}
.ev-form{max-width:640px;margin:48px auto 0;text-align:center}.ev-form h3{font-size:1.8rem;margin-bottom:.4rem}.ev-form>p{color:var(--muted)}
.ev-form form{text-align:left;margin-top:20px}
@media(max-width:900px){.mc-frame{height:500px}}
/* week at a glance card (E9 option A), on the white news band */
.wk-feat{display:block;border:1px solid var(--gold);border-left-width:4px;padding:20px 22px;margin-bottom:26px;background:var(--cream)}
.wk-k{display:block;font-size:.72rem;font-weight:600;letter-spacing:.14em;text-transform:uppercase;color:var(--gold)}
.wk-t{display:block;font-family:var(--serif);font-size:1.5rem;line-height:1.25;color:var(--navy);margin:6px 0;transition:color .2s}
.wk-d{display:block;font-size:.82rem;color:var(--muted)}
.wk-go{display:inline-block;margin-top:12px;font-size:.9rem;font-weight:600;color:var(--navy);border-bottom:1px solid var(--gold)}
.wk-feat:hover .wk-t{color:var(--gold)}#mc-h:not(:first-child){font-size:1.1rem}
/* restaurant reservations, panel A */
.rv{margin:1.6rem 0}
/* the page grid item must be allowed to shrink, or the day strip widens the whole page on a phone */
.split>:has(>.rv){min-width:0}
.rv-panel{background:var(--cream);padding:28px;margin-top:16px}
.rv-head h3{font-size:1.7rem;margin-bottom:2px}.rv-sub{color:var(--muted);font-size:.92rem;margin:0}
.rv-lbl{display:block;font-size:.8rem;font-weight:600;color:var(--navy);margin:16px 0 8px}
.rv-days{display:flex;gap:8px;overflow-x:auto;padding-bottom:4px}
.rv-day{flex:none;width:68px;border:1px solid var(--line);background:#fff;text-align:center;padding:10px 0;cursor:pointer;font:inherit}
.rv-day small{display:block;font-size:.68rem;font-weight:600;color:var(--muted);letter-spacing:.08em}
.rv-day b{display:block;font-family:var(--serif);font-size:1.6rem;color:var(--navy);line-height:1.1}
.rv-day.on{background:var(--navy);border-color:var(--navy)}.rv-day.on small,.rv-day.on b{color:#fff}
.rv-day.closed{opacity:.5;border-style:dashed}
.rv-party{display:flex;align-items:center;border:1px solid var(--line);width:max-content;background:#fff}
.rv-party button{width:44px;height:44px;border:0;background:#fff;font-size:1.2rem;color:var(--navy);cursor:pointer}
.rv-party span{min-width:110px;text-align:center;font-weight:600;color:var(--navy)}
.rv-times{display:grid;grid-template-columns:repeat(auto-fill,minmax(88px,1fr));gap:8px}
.rv-time{border:1px solid var(--line);background:#fff;color:var(--navy);font:500 .9rem var(--sans);padding:11px 8px;cursor:pointer}
.rv-time.on{background:var(--navy);color:#fff;border-color:var(--navy)}
.rv-time.off{color:#b9bccb;text-decoration:line-through;cursor:default}
.rv-next{margin-top:22px}
.rv-form{display:grid;gap:2px;max-width:520px}
.rv-form input{width:100%;border:1px solid var(--line);padding:12px 14px;font:inherit;color:var(--ink);background:#fff}
.rv-pick{font-family:var(--serif);font-size:1.35rem;font-weight:600;color:var(--navy);margin:12px 0 0}
.rv-row{display:flex;gap:10px;margin-top:20px;flex-wrap:wrap}
.rv-msg{margin:14px 0 0;font-size:.95rem;color:var(--navy)}.rv-msg.bad{color:#a3261d}
.rv-link{color:var(--navy);font-weight:600;border-bottom:1px solid var(--gold)}
.rv-note{color:var(--muted);font-size:.92rem}
.rv-done{font-family:var(--serif);font-size:1.5rem;font-weight:600;color:var(--navy);margin:14px 0 4px}
.rv-loading{color:var(--muted);font-size:.9rem}
.rv-day:focus-visible,.rv-time:focus-visible,.rv-party button:focus-visible{outline:2px solid var(--gold);outline-offset:2px}
@media(max-width:600px){.rv-panel{padding:20px}.rv-times{grid-template-columns:repeat(3,1fr)}}
"""

# unused since 2026-10-16: Cullen kept the Golf dropdown; flat_nav() stays for reference
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

# button style A (Cullen, 2026-10-16): sentence case labels, square, no lift
BTN_LABELS = {
    "Book a Tee Time": "Book a tee time", "Send Inquiry": "Send inquiry", "Explore Membership": "Explore membership",
    "Open the League Hub": "Open the league hub", "Membership Inquiry": "Membership inquiry", "Make an Inquiry": "Make an inquiry",
    "Contact the Pro Shop": "Contact the pro shop", "Explore All Three Courses": "Explore all three courses",
    "Send Renewal Request": "Send renewal request", "Send Message": "Send message", "Get on the List": "Get on the list",
    "Renew Membership": "Renew membership", "Explore Dining": "Explore dining", "About Membership": "About membership",
    "Discover the Courses": "Discover the courses",
}
ARROW = ('<svg class="sub-arrow" width="14" height="10" viewBox="0 0 16 10" fill="none" stroke="currentColor" '
         'stroke-width="1.5" aria-hidden="true"><path d="M0 5h14M10 1l4 4-4 4"/></svg>')

def restyle(s):
    s = re.sub(r'(<(?:a|button)[^>]*class="[^"]*\bbtn\b[^"]*"[^>]*>)([^<]+)(<)',
               lambda m: m.group(1) + BTN_LABELS.get(m.group(2), m.group(2)) + m.group(3), s)
    # white dropdown: a small arrow slides in beside the hovered link
    s = re.sub(r'(<ul class="submenu">.*?</ul>)', lambda m: re.sub(r'(<a [^>]*>)([^<]+)(</a>)',
               lambda a: a.group(1) + a.group(2) + ARROW + a.group(3), m.group(1)), s, count=1, flags=re.S)
    return s

def rel(prefix, m):
    page, frag = m.group(1), m.group(2) or ""
    if page not in SLUG: return m.group(0)
    s = SLUG[page]
    return f'href="{prefix}{s + "/" if s else ""}{frag}"' if (s or frag) else f'href="{prefix or "./"}"'

def build():
    if OUT.joinpath("index.html").exists():
        for p in OUT.iterdir():
            if p.name not in {".git", ".github", ".gitignore", ".impeccable", ".superpowers", "README.md", "PRODUCT.md", "DESIGN.md", "tools", ".claude"}:
                shutil.rmtree(p) if p.is_dir() else p.unlink()
    shutil.copytree(SRC/"assets", OUT/"assets", ignore=shutil.ignore_patterns(".DS_Store", "video", "camp-2026.webp", *PRIVATE_DOCS, *RETIRED_DOCS))
    # 2027 camp flyer (Braeden, 2026-10-16): image on the camps page plus the printable PDF
    shutil.copy(OUT/"tools/camps/camp-2027-flyer.jpg", OUT/"assets/img/camp-2027-flyer.jpg")
    shutil.copy(OUT/"tools/camps/2027-Camp-Flyer.pdf", OUT/"assets/docs/2027-Camp-Flyer.pdf")
    shutil.copy(OUT/"tools/camps/junior-lesson.jpg", OUT/"assets/img/junior-lesson.jpg")
    global MAILS, WEEK
    MAILS, WEEK = club_emails.write()
    exec_url = edit_exec()
    if exec_url:
        (OUT/"assets/js/edit-mode.js").write_text((EDIT_DIR/"edit-mode.js").read_text().replace("__EXEC_URL__", exec_url))
    dining = dining_exec()
    if dining:
        (OUT/"assets/js/dining-rules.js").write_text(nodash("rules.js"))
        (OUT/"assets/js/dining-api.js").write_text((DINING_DIR/"api.js").read_text().replace("__DINING_EXEC__", dining))
        (OUT/"assets/js/dining.js").write_text(nodash("panel.js"))
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
        # Golf Camps is now Junior Golf: camps, Operation 36 and the junior academy (E10 option A, Cullen 2026-10-17)
        s = s.replace(">Golf Camps<", ">Junior Golf<")
        s = restyle(s)
        s, n = re.subn(r'<li><a href="[^"]*events-spring-lakes/"[^>]*>Events</a></li>|<a href="[^"]*events-spring-lakes/">Events</a>', "", s)
        assert n == 3, (f, "events links", n)
        s, n = re.subn(r'(<a class="btn btn-gold" href="[^"]*members/)(">Book a tee time</a>)', r"\1#book\2", s)
        assert n == 2, (f, "tee time buttons", n)
        s = staff_edits(f"{slug}/index.html" if slug else "index.html", s)
        for bad in ("—", "–", "SLGC2026", "Renewal-Form.pdf", "Member-Calendar.pdf", "b-num", "Winter-", "Golf Camps",
                    "Restaurant-Menu.pdf", "Wine-List.pdf"):
            assert bad not in s, (f, bad)
        dest = OUT/slug/"index.html" if slug else OUT/"index.html"
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(s)
    if dining:
        # after the page loop: food-beverage/ is created there
        (OUT/"food-beverage/cancel").mkdir(parents=True, exist_ok=True)
        (OUT/"food-beverage/cancel/index.html").write_text(nodash("cancel.html"))
        (OUT/"dining-staff").mkdir(exist_ok=True)
        (OUT/"dining-staff/index.html").write_text(nodash("staff.html"))
        (OUT/"assets/js/dining-staff.js").write_text(nodash("staff.js"))
    # the live /tournaments/ page is leftover template copy, and events are members only (E12): both old
    # addresses keep working and land on the events section of the Member's Area
    for old in ("tournaments", "events-spring-lakes"):
        (OUT/old).mkdir(exist_ok=True)
        (OUT/old/"index.html").write_text(
            '<!doctype html><meta charset="utf-8"><meta name="robots" content="noindex">'
            '<meta http-equiv="refresh" content="0; url=../members/#events">'
            '<link rel="canonical" href="../members/"><a href="../members/#events">Member events</a>')
    # preview forms send nothing; they get wired to the inquiry sheet at launch
    js = OUT/"assets/js/site.js"; t = js.read_text()
    a = t.find("document.querySelectorAll('.inquiry-form')"); b = t.find("\n", a)
    assert a > 0, "site.js forms"
    t = t[:a] + ("document.querySelectorAll('.inquiry-form:not([data-live])').forEach(function(f){f.addEventListener('submit',function(e){"
        "e.preventDefault();var n=f.querySelector('.form-note');if(n){n.style.display='block';"
        "n.textContent='Preview only. This form is not connected yet, so nothing was sent.';}})});") + t[b:]
    js.write_text(t)
    # June CSS: the mobile .btn padding squeezed the menu icon to 4px wide
    css = OUT/"assets/css/style.css"
    css.write_text(css.read_text() + "\n.btn.menu-toggle{padding:8px;gap:0}.menu-toggle svg{flex-shrink:0}\n.hp{position:absolute;left:-9999px}\n" + WEEK_CSS + NAV_CSS)
    shutil.copy(OUT/"tools/members/weather.js", OUT/"assets/js/weather.js")
    shutil.copy(OUT/"tools/forms/inquiry.js", OUT/"assets/js/inquiry.js")
    if exec_url:
        (OUT/"assets/js/content.js").write_text((OUT/"tools/members/content.js").read_text().replace("__EXEC_URL__", exec_url))
    (OUT/".nojekyll").write_text("")
    (OUT/"robots.txt").write_text("User-agent: *\nDisallow: /\n")

JUNIOR_PROGRAMS = (
  '<section><div class="container"><div class="card-grid two">'
  '<article id="operation-36" class="course-card reveal"><div class="course-art"><img src="../assets/img/member-junior.webp" alt="Two junior golfers walking a fairway at Spring Lakes"></div>'
  '<div class="course-body"><h3 class="script" style="font-size:1.9rem">Operation 36</h3><p>Our development program for newer junior golfers. '
  'Weekly coaching with our professionals, plus nine-hole rounds on the East Course that start 25 yards from the green. '
  'Shoot 36 or better and you move back to the next distance.</p>'
  '<a class="link-arrow" href="../contact-us/">Inquire about Operation 36 <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M5 12h14M13 6l6 6-6 6"/></svg></a></div></article>'
  '<article id="junior-academy" class="course-card reveal d1"><div class="course-art"><img src="../assets/img/junior-lesson.jpg" alt="A Spring Lakes professional coaching a junior on the range"></div>'
  '<div class="course-body"><h3 class="script" style="font-size:1.9rem">Junior Academy</h3><p>Our performance program for committed juniors ready to compete. '
  'Weekly guided practice, on-course coaching on the East Course, and a path into junior tournaments.</p>'
  '<a class="link-arrow" href="../contact-us/">Inquire about the academy <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M5 12h14M13 6l6 6-6 6"/></svg></a></div></article>'
  '</div></div></section>')

def camp_button():
    # E6: waitlist form now; in December set "registration_open": true in tools/forms/config.json
    c = forms()
    if c.get("registration_open") and c.get("registration"):
        return f'<a class="btn btn-gold" href="{html.escape(c["registration"])}" target="_blank" rel="noopener">Register for camp</a>'
    if c.get("waitlist"):
        return f'<a class="btn btn-gold" href="{html.escape(c["waitlist"])}" target="_blank" rel="noopener">Join the 2027 waitlist</a>'
    return '<a class="btn btn-gold" href="../contact-us/">Inquire about camp</a>'

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
        # E10: the camps card becomes Junior Golf
        s = sub(s, "<p>Junior camps each season, a real pathway for young golfers. 2026 weeks are now sold out.</p>",
                "<p>Summer camp, Operation 36 and the junior academy, a real pathway for young golfers.</p>", f)
        s = sub(s, 'href="golf-camps/">Camp Info <svg', 'href="golf-camps/">Junior golf <svg', f)
        # E1: weddings are no longer offered
        s = sub(s, "From junior pathways to weddings on the moraine,", "From junior pathways to golf days on the moraine,", f)
        s = sub(s, ">Weddings &amp; Events</h3><p>Weddings, corporate days and celebrations, framed by 45 lakes and open sky.</p>",
                ">Events &amp; Golf Days</h3><p>Corporate days, golf tournaments and celebrations, framed by 45 lakes and open sky.</p>", f)
        assert "edding" not in s, f
        s, n = re.subn(r'<article class="course-card reveal d2"><div class="course-art"><img src="assets/img/g15\.webp" alt=""></div><div class="course-body">'
                       r'<h3 class="script"[^>]*>Events &amp; Golf Days</h3>.*?</article>', "", s, count=1, flags=re.S)
        assert n == 1, (f, "events card")
        s = sub(s, '<span class="eyebrow reveal">Events &amp; Academy</span>', '<span class="eyebrow reveal">Academy &amp; Juniors</span>', f)
        s = sub(s, "From junior pathways to golf days on the moraine, Spring Lakes hosts the moments that matter.</p></div><div class=\"card-grid\">",
                "From first lessons to a real junior pathway, our PGA of Canada professionals teach golfers of every age.</p></div><div class=\"card-grid two\">", f)
        # 2027 forms: categories differ by tier, so no blanket "unlimited golf" claim
        s = sub(s, "Unlimited golf across three courses, a clubhouse built for the whole family, and a calendar that fills the season, with no hidden minimums.",
                "Three championship courses, a clubhouse built for the whole family, and a calendar that fills the season, with no clubhouse minimums.", f)
        # review item 16 + perks note (2026-10-16): dining is for members and their guests; no feature list in public copy
        s = sub(s, '<span class="eyebrow reveal">Clubhouse &amp; Dining</span>', '<span class="eyebrow reveal">The Clubhouse</span>', f)
        s = sub(s, '>Patios, Plates &amp; Long Summer Evenings</h2>', '>Long Summer Evenings on the Back Patio</h2>', f)
        s = sub(s, 'A relaxed clubhouse for members and their guests, with classic flavours and a few creative twists from the kitchen. Wind down after a round or settle in on the patio for the evening.',
                'A relaxed clubhouse for members and their guests. Wind down after a round or settle in on the back patio for the evening.', f)
        s = sub(s, '<a class="btn btn-ghost-navy" href="food-beverage/">Explore Dining</a>',
                '<a class="btn btn-ghost-navy" href="memberships/?interest=social#inquire">Make a membership inquiry</a>', f)
        s, n = re.subn(r'<div class="perks">.*?</p></div></div>(?=<div style="display:flex)', "", s, count=1, flags=re.S)
        assert n == 1 and "Zero Clubhouse Minimums" not in s, (f, "perks")
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
        # E7: the form posts to the Membership Inquiries sheet, which keeps name, email, interest, year and referral,
        # so phone and message come off rather than being dropped silently
        s, n = re.subn(r'<div class="field"><label for="if-p">Phone</label>.*?</div>', "", s, count=1, flags=re.S)
        assert n == 1, (f, "phone field")
        s, n = re.subn(r'<div class="field"><label for="if-m">Message</label><textarea[^>]*></textarea></div>', "", s, count=1)
        assert n == 1, (f, "message field")
        s = sub(s, '<form class="inquiry-form" data-subject="Spring Lakes membership inquiry">',
                f'<form class="inquiry-form" id="mem-inquiry" data-live data-exec="{INQUIRY_EXEC}">'
                '<div class="hp" aria-hidden="true"><label for="if-w">Website</label><input name="website" id="if-w" type="text" tabindex="-1" autocomplete="off"></div>', f)
        s = s.replace("</body>", '<script src="../assets/js/inquiry.js" defer></script></body>', 1)
    if f == "dining.html":
        # E14 (Cullen, 2026-10-28): social membership goes through the membership inquiry form, not its own form here
        s = sub(s, "Get in touch and we will share the details.",
                '<a href="../memberships/?interest=social#inquire" style="color:var(--gold)">Make a membership inquiry</a> and our team will share the details.', f)
        s, n = re.subn(r'<div class="perk reveal d2"><div class="ic">(.*?)</div><h3>Social Membership</h3><p>.*?</p></div>',
                       r'<div class="perk reveal d2"><div class="ic">\1</div><h3>On the Course</h3><p>The beverage cart runs daily, so a cold drink is never far from the next tee.</p></div>',
                       s, count=1, flags=re.S)
        assert n == 1, (f, "social perk")
        s = cut(s, '<section><div class="container narrow"><div class="section-head center"><span class="eyebrow reveal">Inquire', "</main>", "", f)
        assert "Ask about social membership" not in s, f
    if f == "dining.html" and dining_exec():
        s = sub(s, '<div class="hours">', '<div id="reserve" class="rv"><p class="rv-note">To reserve a table, call the clubhouse at 905-640-3633.</p></div><div class="hours">', f)
        s = s.replace("</body>", '<script src="../assets/js/dining-rules.js" defer></script>'
                      '<script src="../assets/js/dining-api.js" defer></script>'
                      '<script src="../assets/js/dining.js" defer></script></body>', 1)
    if f == "dining.html":
        # review 2026-10-16 item 4: no public restaurant hours, menu or wine list; they go to /members/ at launch
        s, n = re.subn(r'<div class="hours">.*?</div></div></div>', "", s, count=1, flags=re.S); assert n == 1, (f, "hours strip")
        s, n = re.subn(r'<div class="doc-links">.*?</div>', "", s, count=1, flags=re.S); assert n == 1, (f, "menu links")
        # review item 17: dining is for members and their guests
        s = sub(s, "Dining is reserved for members.", "Dining is for members and their guests.", f)
    if f == "golf-camps.html":
        s = sub(s, "All 2026 camp weeks are sold out", "2027 camp dates are coming soon", f)
        s = re.sub(r"Thank you\. Every week of our 2026 junior camps has been filled\. To join the waitlist or to hear first when 2027 dates open,",
                   "Our 2026 camps were a full house. To hear first when 2027 dates and registration open,", s)
        s = s.replace("Join the Waitlist", "Get on the List")
        # E10 option A (Cullen, 2026-10-17): this page is Junior Golf, with camp, Operation 36 and the junior academy
        s = sub(s, "<h1>Spring Lakes Camps 2026</h1>", "<h1>Junior Golf</h1>", f)
        s = sub(s, "<title>Golf Camps | Spring Lakes Golf Club</title>", "<title>Junior Golf | Spring Lakes Golf Club</title>", f)
        s = sub(s, "&nbsp;/&nbsp; Golf Camps</div>", "&nbsp;/&nbsp; Junior Golf</div>", f)
        s = re.sub(r'<meta name="description" content="[^"]*">',
                   '<meta name="description" content="Junior golf at Spring Lakes: summer camp for ages 6 to 14, Operation 36 and the junior academy, taught by PGA of Canada professionals.">', s, count=1)
        # option A (Cullen, 2026-10-16): the 2027 flyer in place of the old poster, with a sign-up card
        s = sub(s, '<div class="figure-frame" style="aspect-ratio:3/4;max-width:430px"><img src="../assets/img/camp-2026.webp" alt="Spring Lakes Camp 2026 poster">',
                '<div class="figure-frame" style="aspect-ratio:4/5;max-width:460px"><img src="../assets/img/camp-2027-flyer.jpg" alt="Spring Lakes Summer Camp 2027 flyer: ages 6 to 14, 9 am to 4 pm, four weeks in July and August">', f)
        s, n = re.subn(r'<div class="gate reveal".*?Call 905-640-3633</a></div></div>',
                       '<div class="camp-card reveal"><h2>Summer camp 2027</h2><p>Four weeks for golfers aged 6 to 14, taught by our PGA of Canada professionals. '
                       f'Spots are first come, first served.</p><div class="camp-btns">{camp_button()}'
                       '<a class="btn btn-ghost-navy" href="tel:9056403633">Call 905-640-3633</a></div>'
                       '<a class="camp-pdf" href="../assets/docs/2027-Camp-Flyer.pdf" target="_blank" rel="noopener">Download the flyer (PDF)</a></div>', s, count=1, flags=re.S)
        assert n == 1, (f, "camp gate")
        s = sub(s, '<main id="main"><section><div class="container split"', '<main id="main"><section class="jg-intro"><div class="container narrow center">'
                '<span class="eyebrow reveal">Three Programs</span><h2 class="reveal d1" style="font-size:clamp(2rem,4vw,3rem)">A pathway for young golfers</h2>'
                '<p class="lead-text reveal d2" style="margin:1rem auto 0">Summer camp, Operation 36 and the junior academy, all taught by our PGA of Canada professionals.</p>'
                '</div></section><section id="camp" style="padding-top:0"><div class="container split"', f)
        s = sub(s, "</div></div></section></main>", "</div></div></section>" + JUNIOR_PROGRAMS + "</main>", f)
        s = sub(s, "<h2>Looking for Year-Round Junior Golf?</h2><p>Beyond summer camps, our academy runs junior development programs and a performance pathway all season long.</p>",
                "<h2>Looking for Private Lessons?</h2><p>Our professionals also teach juniors one on one, booked online through CoachNow.</p>", f)
    if f == "events.html":
        # weddings are no longer offered (Laura, 2026-10-16, E1)
        s = sub(s, "Weddings, corporate functions and celebrations at Spring Lakes", "Corporate functions, golf days and celebrations at Spring Lakes", f)
        s = s.replace(">Weddings and Functions<", ">Events and Functions<")
        s = sub(s, "Spring Lakes hosts weddings, corporate days and celebrations", "Spring Lakes hosts corporate days, golf tournaments and celebrations", f)
        s, n = re.subn(r'<article class="course-card reveal"><div class="course-art"><img src="(?:\.\./)?assets/img/g05\.webp" alt=""></div>'
                       r'<div class="course-body"><h3 class="script"[^>]*>Weddings</h3>.*?</article>', "", s, count=1, flags=re.S)
        assert n == 1, (f, "weddings card")
        s = sub(s, '<div class="card-grid"><article class="course-card reveal d1">', '<div class="card-grid two"><article class="course-card reveal">', f)
        assert "edding" not in s, f
    if f == "golf-academy.html":
        s = s.replace(" Winter lesson programs available.", "")
        s, n = re.subn(r'<a class="link-arrow pro-extra" href="(?:\.\./)?assets/docs/Winter-[^"]*\.pdf".*?</a>', "", s, flags=re.S)
        assert n == 2, (f, "winter links", n)
        s = sub(s, "Yardage clinics, winter lesson programs and junior pathways", "Yardage clinics and junior pathways", f)
        assert "winter" not in s.lower(), f
    if f == "contact.html":
        s = sub(s, '<h3 style="font-size:1.5rem;margin:34px 0 6px">Staff Directory</h3>',
                '<div id="hours-wrap" class="hours-public" hidden><h3 style="font-size:1.5rem;margin:0 0 6px">Hours</h3>'
                '<div id="hours-box" class="hr-list" data-scope="public" aria-live="polite"></div></div>'
                '<h3 style="font-size:1.5rem;margin:34px 0 6px">Staff Directory</h3>', f)
        s = s.replace("</body>", '<script src="../assets/js/content.js" defer></script></body>', 1)
        s = re.sub(r' ·\s*<a href="mailto:[a-z]+@springlakesgolf\.com"[^>]*>[a-z]+@springlakesgolf\.com</a>', "", s)
        assert not re.search(r'(braeden|luke|cullen|rhys|laura|ashley|kelly|chris)@', s), f
        # review item 16 / E14: no separate dining topic; social membership goes through the membership inquiry
        s = sub(s, '<option>Golf lessons</option><option>Dining</option>', '<option>Golf lessons</option>', f)
    if f == "golf.html":
        s = re.sub(r'<a [^>]*href="assets/docs/[A-Za-z]+-Scorecard\.pdf"[^>]*>.*?</a>', "", s)
        s = re.sub(r'<a [^>]*href="\.\./assets/docs/[A-Za-z]+-Scorecard\.pdf"[^>]*>.*?</a>', "", s)
        assert "Scorecard.pdf" not in s, f
    if f == "members.html":
        s = re.sub(r'<script>\(function\(\)\{var fm=document\.getElementById\("memform"\).*?</script>', "", s, flags=re.S)
        s = cut(s, '<div id="memgate"', '<div id="memarea"', '<p class="preview-note">Preview: at launch this page sits behind the '
                'member password, checked on the server. Member documents (calendar, renewal forms) are added then.</p>', "members")
        s = sub(s, '<div id="memarea" hidden>', '<div id="memarea">' + TEE_BAND + this_week(MAILS, WEEK) + MEMBER_EVENTS, f)
        s, n = re.subn(r'<section id="book" class="bg-cream">.*?</section>', "", s, count=1, flags=re.S)
        assert n == 1, (f, "old tee time section")
        s = sub(s, '</section><section><div class="container split"><div class="figure-wrap reveal"><div class="figure-frame ratio-54"><img src="../assets/img/member-leagues.webp"',
                '</section>' + lost_found() + '<section id="leagues"><div class="container split"><div class="figure-wrap reveal"><div class="figure-frame ratio-54"><img src="../assets/img/member-leagues.webp"', f)
        s = s.replace("</body>", '<script src="../assets/js/weather.js" defer></script><script src="../assets/js/content.js" defer></script></body>', 1)
        k = s.find("Member Documents"); i = s.rfind("<section", 0, k); j = s.find("</section>", k) + len("</section>")
        assert k > 0 and i > 0, f
        s = s[:i] + s[j:]
        s = re.sub(r'<p class="note"[^>]*>Prefer a paper form\?.*?</p>', "", s, flags=re.S)
        s = re.sub(r'<select([^>]*id="[^"]*")[^>]*>(?:(?!</select>).)*?Junior Intermediate.*?</select>',
                   lambda m: '<input type="text"' + m.group(1) + ' name="rn-cat">', s, count=1, flags=re.S)
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
