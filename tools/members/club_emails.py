"""Latest club Mailchimp campaigns for the members page.

Reads the public archive feed and writes assets/data/club-emails.json, which
tools/members/weather.js renders. Run by tools/build.py and every hour by
.github/workflows/club-emails.yml, so new campaigns show up without a rebuild.
"""
import email.utils, json, sys, urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

FEED = "https://us13.campaign-archive.com/feed?u=40d74683558e83493d58aafed&id=1872afdeb6"
HOME = "https://us13.campaign-archive.com/home/?u=40d74683558e83493d58aafed&id=1872afdeb6"
OUT = Path(__file__).resolve().parents[2]/"assets/data/club-emails.json"

def latest(n=5):
    """Newest first. Mailchimp lists resends and test splits as separate items
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
    return [{"date": w.date().isoformat(), "label": f"{w.strftime('%b')} {w.day}", "title": t, "link": l} for w, t, l in out[:n]]

def write():
    """Returns the list; keeps the previous file if the feed is down."""
    try:
        mails = latest()
    except Exception as e:
        print("club emails: feed unavailable,", e)
        return json.loads(OUT.read_text())["emails"] if OUT.exists() else []
    OUT.parent.mkdir(parents=True, exist_ok=True)
    body = json.dumps({"emails": mails, "all": HOME}, indent=1) + "\n"
    if not OUT.exists() or OUT.read_text() != body:
        OUT.write_text(body)
    return mails

if __name__ == "__main__":
    print(len(write()), "club emails"); sys.exit(0)
