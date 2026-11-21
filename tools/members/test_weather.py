"""7-day forecast strip on the members page (Cullen, 2026-11-21).

Runs tools/members/weather.js under node with a stand-in page and a sample Environment
Canada reply, and checks it draws one cell per day for the strip along the bottom of Club news.
Run: python3 -m unittest tools/members/test_weather.py
"""
import json, re, shutil, subprocess, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
JS = ROOT/"tools/members/weather.js"

DAYS = ["Saturday", "Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]

def period(name, cls, temp, icon, text, pop=""):
    return {"period": {"value": {"en": name}},
            "abbreviatedForecast": {"icon": {"value": icon}, "textSummary": {"en": text}, "pop": {"value": {"en": pop}}},
            "temperatures": {"temperature": [{"class": {"en": cls}, "value": {"en": temp}}]}}

def sample():
    f = []
    for i, d in enumerate(DAYS):
        f.append(period(d, "high", 10 + i, 0 if i % 2 else 12, "Rain <b>" if i == 2 else "Sunny", "40" if i == 2 else ""))
        f.append(period(d + " night", "low", -i, 30, "Clear"))
    return {"properties": {"forecastGroup": {"forecasts": f}}}

RUN = r"""
const src = require('fs').readFileSync(process.argv[1], 'utf8');
const els = {};
function el(id){ return els[id] || (els[id] = {id, innerHTML: '', attrs: {}, parentNode: null,
  setAttribute(k, v){ this.attrs[k] = v; }, getAttribute(k){ return this.attrs[k]; }}); }
global.document = {currentScript: null,
  getElementById: id => ['mc-list', 'mc-frame', 'mc-open'].includes(id) ? null : el(id)};
global.window = {};
let s = ''; process.stdin.on('data', d => s += d).on('end', () => {
  const data = JSON.parse(s);
  global.fetch = () => Promise.resolve({ok: true, json: () => Promise.resolve(data)});
  new Function(src)();
  setTimeout(() => process.stdout.write(JSON.stringify({html: els['wx-days'].innerHTML, busy: els['wx-days'].attrs['aria-busy']})), 50);
});
"""

class Strip(unittest.TestCase):
    def test_one_cell_per_day_side_by_side(self):
        node = shutil.which("node")
        if not node: self.skipTest("node not installed")
        out = json.loads(subprocess.run([node, "-e", RUN, str(JS)], input=json.dumps(sample()),
                                        capture_output=True, text=True, check=True).stdout)
        cells = re.findall(r'<div class="wx-day">(.*?)</div>', out["html"])
        self.assertEqual(len(cells), 7)
        self.assertNotIn("wx-row", out["html"])
        self.assertEqual(out["busy"], "false")
        for c in cells:
            # day, icon, high and low, then the summary, in that order
            order = [c.index(k) for k in ('class="wx-name"', 'class="wx-ico"', 'class="wx-temp"', 'class="wx-text"')]
            self.assertEqual(order, sorted(order), c)
        self.assertIn('<span class="wx-name">Today</span>', cells[0])
        self.assertIn('<span class="wx-name">Sun</span>', cells[1])
        self.assertIn("<b>10&deg;</b>0&deg;", cells[0])
        self.assertIn("Rain &lt;b&gt; <em>40%</em>", cells[2])

if __name__ == "__main__":
    unittest.main()
