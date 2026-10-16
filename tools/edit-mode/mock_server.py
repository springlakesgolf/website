"""Local test server: serves the site and fakes the Apps Script at /exec.

Build against it with SLG_EDIT_EXEC=http://127.0.0.1:8744/exec python3 tools/build.py,
open http://127.0.0.1:8744/?edit=testkey, and requests print here and go to mock_rows.json.
"""
import json, sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ROWS = Path(__file__).with_name("mock_rows.json")
seen = {}

class H(SimpleHTTPRequestHandler):
    def __init__(self, *a, **k): super().__init__(*a, directory=str(ROOT), **k)
    def do_POST(self):
        b = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        if b.get("key") != "testkey": out = {"ok": False, "error": "key"}
        elif b["rid"] in seen: out = seen[b["rid"]]
        else:
            rows = json.loads(ROWS.read_text()) if ROWS.exists() else []
            if b.get("photo"): b["photo"] = {"name": b["photo"]["name"], "bytes": len(b["photo"]["data"]) * 3 // 4}
            rows.append(b); ROWS.write_text(json.dumps(rows, indent=1))
            out = seen[b["rid"]] = {"ok": True, "rid": b["rid"], "id": f"E{len(rows)}"}
            print("ROW", json.dumps({k: b[k] for k in ("name", "page", "section", "current", "change")})[:400], flush=True)
        data = json.dumps(out).encode()
        self.send_response(200); self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data))); self.end_headers(); self.wfile.write(data)

ThreadingHTTPServer(("127.0.0.1", int(sys.argv[1]) if len(sys.argv) > 1 else 8744), H).serve_forever()
