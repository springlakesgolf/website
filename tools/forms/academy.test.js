// Offline test for the Junior Academy application script (academy.gs). Loads it into a vm context
// with an in-memory spreadsheet and a fake MailApp, then posts the way academy.js does.
// Run: node --test tools/forms/academy.test.js
const test = require('node:test');
const assert = require('node:assert');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const CODE = fs.readFileSync(path.join(__dirname, 'academy.gs'), 'utf8');

// A small fake of the Sheets objects academy.gs uses. tabs: {name: [[row], ...]} including the header row.
function fakeBook(tabs) {
  const sheet = name => {
    const grid = tabs[name];
    return {
      getLastRow: () => grid.length,
      getDataRange: () => ({ getDisplayValues: () => grid.map(r => r.map(String)), getValues: () => grid.map(r => r.slice()) }),
      getRange(r, c, nr, nc) {
        nr = nr || 1; nc = nc || 1;
        return { getValues: () => grid.slice(r - 1, r - 1 + nr).map(row => { const o = []; for (let j = 0; j < nc; j++) o.push(row[c - 1 + j] ?? ''); return o; }) };
      },
      appendRow(row) { grid.push(row.slice()); }
    };
  };
  return { getSheetByName: name => (tabs[name] ? sheet(name) : null) };
}

function load({ accepting = 'Yes', mode = 'Test', sheetId = 'SHEET1', mailFails = false } = {}) {
  const HEAD = ['Received', 'Request id', 'Player name'];
  const tabs = {
    Applications: [HEAD], Test: [HEAD],
    Settings: [['Setting', 'Value'], ['Accepting applications', accepting], ['Mode', mode],
               ['Alert email', 'alerts@example.com'], ['Test alert email', 'tester@example.com']]
  };
  const mail = [];
  let locked = 0;
  const ctx = {
    SpreadsheetApp: { openById: id => { assert.equal(id, 'SHEET1'); return fakeBook(tabs); } },
    PropertiesService: { getScriptProperties: () => ({ getProperty: k => (k === 'SHEET_ID' ? sheetId : null) }) },
    LockService: { getScriptLock: () => ({ waitLock() { locked++; }, releaseLock() { locked--; } }) },
    ContentService: { MimeType: { JSON: 'json' }, createTextOutput: s => ({ body: s, setMimeType() { return this; } }) },
    MailApp: { sendEmail(m) { if (mailFails) throw new Error('quota'); mail.push(m); } },
    Utilities: { formatDate: () => '2027-02-01 09:00' },
    Logger: { log() {} }, console: { error() {}, log() {} }
  };
  vm.createContext(ctx);
  vm.runInContext(CODE, ctx);
  const post = b => JSON.parse(ctx.doPost({ postData: { contents: typeof b === 'string' ? b : JSON.stringify(b) } }).body);
  const get = () => JSON.parse(ctx.doGet().body);
  return { post, get, tabs, mail, locks: () => locked };
}

const APP = { rid: 'r1', player: 'Sam Player', age: '12', years: '3', handicap: '18.4', tournaments: 'Club junior day 2026',
              parent: 'Pat Parent', email: 'pat@example.com', phone: '905-555-0100', website: '' };

test('doGet says whether applications are open', () => {
  assert.deepEqual(load({ accepting: 'No' }).get(), { ok: true, open: false });
  assert.deepEqual(load({ accepting: 'Yes' }).get(), { ok: true, open: true });
});

test('closed by default: a post is refused and nothing is written', () => {
  const t = load({ accepting: 'No' });
  const out = t.post(APP);
  assert.equal(out.ok, false);
  assert.equal(out.closed, true);
  assert.equal(t.tabs.Test.length, 1);
  assert.equal(t.tabs.Applications.length, 1);
  assert.equal(t.mail.length, 0);
  assert.equal(t.locks(), 0, 'lock released');
});

test('test mode writes to the Test tab and sends a [TEST] alert to the test address only', () => {
  const t = load();
  assert.deepEqual(t.post(APP), { ok: true });
  assert.equal(t.tabs.Test.length, 2);
  assert.equal(t.tabs.Applications.length, 1);
  const row = t.tabs.Test[1];
  assert.deepEqual(row.slice(1, 11), ['r1', 'Sam Player', '12', '3', '18.4', 'Club junior day 2026', 'Pat Parent', 'pat@example.com', '905-555-0100', 'New']);
  assert.equal(t.mail.length, 1);
  assert.equal(t.mail[0].to, 'tester@example.com');
  assert.match(t.mail[0].subject, /^\[TEST\] Junior Academy application: Sam Player$/);
  assert.equal(t.mail[0].replyTo, 'pat@example.com');
});

test('live mode writes to Applications and alerts the alert address', () => {
  const t = load({ mode: 'Live' });
  assert.equal(t.post(APP).ok, true);
  assert.equal(t.tabs.Applications.length, 2);
  assert.equal(t.tabs.Test.length, 1);
  assert.equal(t.mail[0].to, 'alerts@example.com');
  assert.doesNotMatch(t.mail[0].subject, /TEST/);
});

test('the same request id twice adds one row', () => {
  const t = load();
  t.post(APP);
  const again = t.post(APP);
  assert.equal(again.ok, true);
  assert.equal(again.duplicate, true);
  assert.equal(t.tabs.Test.length, 2);
  assert.equal(t.mail.length, 1);
});

test('honeypot: a filled website field is thanked and dropped', () => {
  const t = load();
  assert.deepEqual(t.post({ ...APP, website: 'http://spam.example' }), { ok: true });
  assert.equal(t.tabs.Test.length, 1);
  assert.equal(t.mail.length, 0);
});

test('validation: each required field is checked', () => {
  const t = load();
  const bad = [
    [{ player: '' }, /name/], [{ age: '4' }, /age/], [{ age: '19' }, /age/], [{ age: 'ten' }, /age/],
    [{ years: '' }, /years/], [{ years: '30' }, /years/], [{ parent: ' ' }, /parent or guardian/],
    [{ email: 'nope' }, /email/], [{ phone: '555-0100' }, /phone/]
  ];
  for (const [change, msg] of bad) {
    const out = t.post({ ...APP, rid: 'x' + Math.random(), ...change });
    assert.equal(out.ok, false, JSON.stringify(change));
    assert.match(out.message, msg, JSON.stringify(change));
  }
  assert.equal(t.tabs.Test.length, 1, 'nothing written');
});

test('handicap and tournaments are optional', () => {
  const t = load();
  assert.equal(t.post({ ...APP, handicap: '', tournaments: '' }).ok, true);
});

test('cells that start like a formula are written as text', () => {
  const t = load();
  t.post({ ...APP, player: '=HYPERLINK("http://x")', tournaments: '+1 event', handicap: '-2', phone: '+1 905 555 0100' });
  const row = t.tabs.Test[1];
  assert.equal(row[2], '\'=HYPERLINK("http://x")');
  assert.equal(row[5], "'-2");
  assert.equal(row[6], "'+1 event");
  assert.equal(row[9], "'+1 905 555 0100");
});

test('bad bodies are refused without a row', () => {
  const t = load();
  assert.equal(t.post('not json').ok, false);
  assert.equal(t.post('x'.repeat(20000)).ok, false);
  assert.equal(t.post('null').ok, false);
  assert.equal(t.tabs.Test.length, 1);
});

test('a failed alert email still keeps the application', () => {
  const t = load({ mailFails: true });
  assert.equal(t.post(APP).ok, true);
  assert.equal(t.tabs.Test.length, 2);
});

test('the script holds no prices and no dashes a family could see', () => {
  assert.doesNotMatch(CODE, /\$\d/);
  assert.doesNotMatch(CODE, /[–—]/);
});
