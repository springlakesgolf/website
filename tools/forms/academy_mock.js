// Local stand-in for the Junior Academy Apps Script, for a browser check of the form.
// Serves a built site folder and runs academy.gs (in a vm, with a fake sheet) for /exec.
// Accepting applications = Yes and Mode = Test, so a post lands in the Test tab with a [TEST] alert.
// Rows and alerts are written to the JSON file given (nothing leaves this computer).
//
//   SLG_ACADEMY_EXEC=http://127.0.0.1:8756/exec SLG_ACADEMY_OPEN=1 python3 <copy>/tools/build.py
//   node tools/forms/academy_mock.js <built site folder> 8756 <rows.json>
//   open http://127.0.0.1:8756/junior-golf/academy/
const http = require('node:http');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const ROOT = path.resolve(process.argv[2] || path.join(__dirname, '..', '..'));
const PORT = Number(process.argv[3] || 8756);
const OUT = path.resolve(process.argv[4] || path.join(__dirname, 'academy_mock_rows.json'));
const HEAD = ['Received', 'Request id', 'Player name', 'Age', 'Years playing', 'Handicap', 'Tournaments played',
              'Parent or guardian', 'Parent email', 'Parent phone', 'Status', 'Notes'];
const state = fs.existsSync(OUT) ? JSON.parse(fs.readFileSync(OUT, 'utf8')) : {
  tabs: { Applications: [HEAD], Test: [HEAD],
          Settings: [['Setting', 'Value'], ['Accepting applications', 'Yes'], ['Mode', 'Test'],
                     ['Alert email', 'alerts@example.com'], ['Test alert email', 'tester@example.com']] },
  mail: []
};
const save = () => fs.writeFileSync(OUT, JSON.stringify(state, null, 1));
const sheet = name => {
  const grid = state.tabs[name];
  return {
    getLastRow: () => grid.length,
    getDataRange: () => ({ getDisplayValues: () => grid.map(r => r.map(String)) }),
    getRange: (r, c, nr) => ({ getValues: () => grid.slice(r - 1, r - 1 + (nr || 1)).map(row => [row[c - 1]]) }),
    appendRow(row) { grid.push(row); save(); }
  };
};
const ctx = {
  SpreadsheetApp: { openById: () => ({ getSheetByName: n => (state.tabs[n] ? sheet(n) : null) }) },
  PropertiesService: { getScriptProperties: () => ({ getProperty: k => (k === 'SHEET_ID' ? 'MOCK' : null) }) },
  LockService: { getScriptLock: () => ({ waitLock() {}, releaseLock() {} }) },
  ContentService: { MimeType: { JSON: 'json' }, createTextOutput: s => ({ body: s, setMimeType() { return this; } }) },
  MailApp: { sendEmail(m) { state.mail.push(m); save(); console.log('ALERT', m.to, m.subject); } },
  Utilities: { formatDate: () => new Date().toISOString().slice(0, 16).replace('T', ' ') },
  Logger: { log: console.log }, console
};
vm.createContext(ctx);
vm.runInContext(fs.readFileSync(path.join(__dirname, 'academy.gs'), 'utf8'), ctx);

const TYPES = { '.html': 'text/html', '.css': 'text/css', '.js': 'text/javascript', '.json': 'application/json', '.png': 'image/png',
                '.jpg': 'image/jpeg', '.webp': 'image/webp', '.svg': 'image/svg+xml', '.pdf': 'application/pdf', '.woff2': 'font/woff2' };
http.createServer((req, res) => {
  const url = new URL(req.url, 'http://x');
  if (url.pathname === '/exec') {
    let body = '';
    req.on('data', c => { body += c; });
    req.on('end', () => {
      const out = req.method === 'POST' ? ctx.doPost({ postData: { contents: body } }) : ctx.doGet();
      if (req.method === 'POST') console.log('POST', out.body);
      res.writeHead(200, { 'Content-Type': 'application/json' }); res.end(out.body);
    });
    return;
  }
  let file = path.join(ROOT, decodeURIComponent(url.pathname));
  if (!file.startsWith(ROOT)) { res.writeHead(403); return res.end(); }
  if (fs.existsSync(file) && fs.statSync(file).isDirectory()) file = path.join(file, 'index.html');
  if (!fs.existsSync(file)) { res.writeHead(404); return res.end('not found'); }
  res.writeHead(200, { 'Content-Type': TYPES[path.extname(file)] || 'application/octet-stream' });
  fs.createReadStream(file).pipe(res);
}).listen(PORT, '127.0.0.1', () => console.log(`academy mock on http://127.0.0.1:${PORT}/ serving ${ROOT}, rows in ${OUT}`));
