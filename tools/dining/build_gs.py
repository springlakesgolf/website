"""Write dist/Dining.gs: rules.js followed by Code.gs, ready to paste into the
Apps Script editor. The module.exports line is dropped; Apps Script has no module.
The spreadsheet ID lives in tools/dining/config.local.json ({"sheet_id": "..."}), which is
gitignored so the sheet address never reaches the public repo. If it has a "sheet_id" (config.json
is read as a fallback), a SHEET_ID line is written first so a standalone script opens that
sheet by ID (see ss_() in Code.gs). Without one, the script uses its bound sheet."""
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXPORT = "if (typeof module !== 'undefined') module.exports = DiningRules;"
rules = (HERE / "rules.js").read_text()
if EXPORT not in rules:
    raise SystemExit("rules.js no longer ends with the module.exports line; update build_gs.py")
rules = rules.replace(EXPORT, "").rstrip() + "\n"
out = HERE / "dist" / "Dining.gs"
out.parent.mkdir(exist_ok=True)
prefix = ""
sheet_id = None
for name in ("config.local.json", "config.json"):
    path = HERE / name
    if path.exists():
        sheet_id = json.loads(path.read_text()).get("sheet_id")
        if sheet_id:
            if not re.fullmatch(r"[A-Za-z0-9_-]+", str(sheet_id)):
                raise SystemExit(f"{name} sheet_id must be letters, digits, dash or underscore")
            prefix = f"var SHEET_ID = '{sheet_id}';\n"
            break
out.write_text(prefix + rules + "\n" + (HERE / "Code.gs").read_text())
print("wrote", out, len(out.read_text()), "chars")
