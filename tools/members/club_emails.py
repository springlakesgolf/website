"""Latest club Mailchimp campaigns for the members page.

Reads the public archive feed and writes assets/data/club-emails.json, which
tools/members/weather.js renders. Run by tools/build.py and every hour by
.github/workflows/club-emails.yml, so new campaigns show up without a rebuild.
"""
import datetime, email.utils, json, re, sys, urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

FEED = "https://us13.campaign-archive.com/feed?u=40d74683558e83493d58aafed&id=1872afdeb6"
HOME = "https://us13.campaign-archive.com/home/?u=40d74683558e83493d58aafed&id=1872afdeb6"
OUT = Path(__file__).resolve().parents[2]/"assets/data/club-emails.json"
# Braeden's weekly "week at a glance" email is featured on its own while it is
# current (staff edit E9, 2026-10-16)
WEEK = re.compile(r"this week at spring lakes|week at a glance", re.I)
WEEK_DAYS = 8

def latest(n=5, now=None):
    """Returns (emails, week). Newest first. Mailchimp lists resends and test splits as separate items
    with the same title, so keep only the newest of each title."""
    with urllib.request.urlopen(FEED, timeout=20) as r:
        items = ET.fromstring(r.read()).findall(".//item")
    out, seen = [], set()
    for it in items:
        title = (it.findtext("title") or "").strip()
        if not title or title.lower() in seen: continue
        seen.add(title.lower())
        out.append((email.utils.parsedate_to_datetime(it.findtext("pubDate")), title, it.findtext("link")))
    out.sort(reverse=True)
    mails = [{"date": w.date().isoformat(), "label": f"{w.strftime('%b')} {w.day}", "title": t, "link": l} for w, t, l in out]
    today = (now or datetime.date.today())
    week = next((m for m in mails if WEEK.search(m["title"])
                 and (today - datetime.date.fromisoformat(m["date"])).days <= WEEK_DAYS), None)
    return [m for m in mails if m is not week][:n], week

def write():
    """Returns (emails, week); keeps the previous file if the feed is down."""
    try:
        mails, week = latest()
    except Exception as e:
        print("club emails: feed unavailable,", e)
        if not OUT.exists(): return [], None
        d = json.loads(OUT.read_text())
        return d["emails"], d.get("week")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    body = json.dumps({"emails": mails, "week": week, "all": HOME}, indent=1) + "\n"
    if not OUT.exists() or OUT.read_text() != body:
        OUT.write_text(body)
    return mails, week

if __name__ == "__main__":
    mails, week = write(); print(len(mails), "club emails,", "week at a glance" if week else "no current week at a glance"); sys.exit(0)
