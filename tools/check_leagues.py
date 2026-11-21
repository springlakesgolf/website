"""Check the League hub codes against the live app: each code in LEAGUES (tools/build.py) must open that league's page.
Run after updating the codes each spring: python3 tools/check_leagues.py
"""
import re, sys, urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build import APP_URL, LEAGUES

bad = 0
for name, code in LEAGUES:
    if not code:
        print(f"-- {name}: no code yet, opens {APP_URL}/e")
        continue
    url = f"{APP_URL}/e/{code}"
    try:
        page = urllib.request.urlopen(url, timeout=20).read().decode("utf-8", "replace")
    except Exception as e:
        print(f"!! {name}: {url} did not open ({e})"); bad += 1; continue
    title = re.search(r"<title>(.*?)</title>", page, re.S)
    title = title.group(1) if title else ""
    if name.split()[0].lower() not in title.lower():
        print(f"!! {name}: {url} opens '{title}', not this league"); bad += 1
    else:
        print(f"ok {name}: {url} ({title})")
sys.exit(1 if bad else 0)
