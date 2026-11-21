// Offline test for the staff-edits bot route in Code.gs (W2). Loads Code.gs into a vm context with
// a small in-memory sheet, then posts the way staff_edits.py does.
// Run: node --test tools/edit-mode/code.test.js
const test = require('node:test');
const assert = require('node:assert');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const CODE = fs.readFileSync(path.join(__dirname, 'Code.gs'), 'utf8');
const SECRET = 'botsecret123';

function load(rows, props) {
  const grid = rows.map(r => r.slice());
  const sheet = {
    getLastRow: () => grid.length,
    getRange(r, c, nr, nc) {
      nr = nr || 1; nc = nc || 1;
      return {
        getValues: () => grid.slice(r - 1, r - 1 + nr).map(row => { const out = []; for (let j = 0; j < nc; j++) out.push(row[c - 1 + j] ?? ''); return out; }),
        getValue: () => grid[r - 1][c - 1],
        setValue(v) { grid[r - 1][c - 1] = v; return this; },
        setValues(v) { v.forEach((row, i) => row.forEach((x, j) => { grid[r - 1 + i][c - 1 + j] = x; })); return this; }
      };
    }
  };
  const ctx = {
    SpreadsheetApp: { openById: () => ({ getSheetByName: () => sheet }) },
    PropertiesService: { getScriptProperties: () => ({ getProperty: k => props[k] || null }) },
    LockService: { getScriptLock: () => ({ waitLock() {}, releaseLock() {} }) },
    CacheService: { getScriptCache: () => ({ get: () => null, put() {} }) },
    ContentService: { MimeType: { JSON: 'json' }, createTextOutput: s => ({ body: s, setMimeType() { return this; } }) },
    Utilities: {}, DriveApp: {}, Logger: { log() {} }
  };
  vm.createContext(ctx);
  vm.runInContext(CODE, ctx);
  const post = b => JSON.parse(ctx.doPost({ postData: { contents: JSON.stringify(b) } }).body);
  return { post, grid };
}

function row(id, status, pr) {
  const r = new Array(17).fill('');
  Object.assign(r, { 0: id, 2: 'Staff Name', 3: '/golf/', 4: 'North', 5: 'old text', 6: 'new text', 8: status, 11: 'https://x/golf/', 15: pr || '' });
  return r;
}

const HEAD = new Array(17).fill('head');

test('pending lists New rows with no PR, without the submitter name', () => {
  const { post } = load([HEAD, row('E1', 'New'), row('E2', 'Done'), row('E3', 'New', 'https://github.com/x'), row('E4', 'New')], { BOT_SECRET: SECRET });
  const out = post({ bot: SECRET, action: 'pending' });
  assert.equal(out.ok, true);
  assert.deepEqual(out.rows.map(r => r.id), ['E1', 'E4']);
  assert.equal(out.rows[0].change, 'new text');
  assert.equal(out.rows[0].name, undefined);
});

test('pending stops at five rows', () => {
  const rows = [HEAD]; for (let i = 1; i <= 8; i++) rows.push(row('E' + i, 'New'));
  assert.equal(load(rows, { BOT_SECRET: SECRET }).post({ bot: SECRET, action: 'pending' }).rows.length, 5);
});

test('wrong, missing or unset secret is refused', () => {
  const { post } = load([HEAD, row('E1', 'New')], { BOT_SECRET: SECRET });
  assert.equal(post({ bot: 'nope', action: 'pending' }).error, 'key');
  assert.equal(post({ bot: SECRET + 'x', action: 'pending' }).error, 'key');
  assert.equal(load([HEAD], {}).post({ bot: '', action: 'pending' }).ok, false);
  // the staff edit key is not the bot secret
  assert.equal(load([HEAD], { BOT_SECRET: SECRET, EDIT_KEY: 'k' }).post({ bot: 'k', action: 'pending' }).error, 'key');
});

test('result writes status, PR link and note to that row only', () => {
  const { post, grid } = load([HEAD, row('E1', 'New'), row('E2', 'New')], { BOT_SECRET: SECRET });
  const pr = 'https://github.com/springlakesgolf/website/pull/12';
  assert.equal(post({ bot: SECRET, action: 'result', id: 'E2', status: 'PR open', pr, note: 'Tidied the wording.' }).ok, true);
  assert.deepEqual([grid[2][8], grid[2][15], grid[2][16]], ['PR open', pr, 'Tidied the wording.']);
  assert.equal(grid[1][8], 'New');
});

test('result refuses other statuses, other PR hosts, and rows a person already changed', () => {
  const { post, grid } = load([HEAD, row('E1', 'New'), row('E2', 'Done')], { BOT_SECRET: SECRET });
  assert.equal(post({ bot: SECRET, action: 'result', id: 'E1', status: 'Done' }).error, 'status');
  assert.equal(post({ bot: SECRET, action: 'result', id: 'E1', status: 'PR open', pr: 'https://evil.example/pull/1' }).error, 'pr');
  assert.equal(post({ bot: SECRET, action: 'result', id: 'E2', status: 'Needs Cullen', note: 'x' }).error, 'not new');
  assert.equal(grid[2][8], 'Done');
  assert.equal(post({ bot: SECRET, action: 'result', id: 'E9', status: 'Needs Cullen' }).error, 'no row');
});

test('a note that looks like a formula is stored as text', () => {
  const { post, grid } = load([HEAD, row('E1', 'New')], { BOT_SECRET: SECRET });
  post({ bot: SECRET, action: 'result', id: 'E1', status: 'Needs Cullen', note: '=IMPORTDATA("x")' });
  assert.equal(grid[1][16], '\'=IMPORTDATA("x")');
});

test('staff submissions still need the edit key', () => {
  const { post } = load([HEAD], { BOT_SECRET: SECRET, EDIT_KEY: 'k' });
  assert.equal(post({ key: SECRET, rid: 'r1', change: 'x' }).error, 'key');
});

// Content feed (?feed=content): Club Events from the Events tab, next to Hours and Lost & Found.
function loadContent(tabs) {
  const sheets = {};
  for (const [name, grid] of Object.entries(tabs)) {
    sheets[name] = { getDataRange: () => ({ getDisplayValues: () => grid.map(r => r.map(String)), getValues: () => grid }) };
  }
  const ctx = {
    SpreadsheetApp: { openById: () => ({ getSheetByName: n => sheets[n] || null, getSpreadsheetTimeZone: () => 'America/Toronto' }) },
    CacheService: { getScriptCache: () => ({ get: () => null, put() {} }) },
    ContentService: { MimeType: { JSON: 'json' }, createTextOutput: s => ({ body: s, setMimeType() { return this; } }) },
    PropertiesService: {}, LockService: {}, Utilities: { formatDate: () => 'Nov 1' }, DriveApp: {}, Logger: { log() {} }
  };
  vm.createContext(ctx);
  vm.runInContext(CODE, ctx);
  return JSON.parse(ctx.doGet({ parameter: { feed: 'content' } }).body);
}

const HOURS = [['Who', 'What', 'Hours', 'Note'], ['Everyone', 'Pro Shop', '8 to 5', '']];
const LOST = [['Found', 'Item', 'Where', 'Photo', 'Status']];
const EV_HEAD = ['Event', 'Date', 'Course', 'Status', 'Sign-up link', 'Photo (last year)', 'Show', 'Staff notes'];

test('content feed sends Club Events in sheet order, without staff notes', () => {
  const out = loadContent({ Hours: HOURS, 'Lost & Found': LOST, Events: [EV_HEAD,
    ['Night Golf', 'Sat, July 10', 'East Course', 'Sign-up open', 'https://example.com/night', 'https://example.com/n.jpg', 'Yes', 'Call the band'],
    ['Ryder Cup', 'Sat, August 14', '', 'Opens soon', '', '', '', 'Draft'],
    ['Tip & Tuck', 'Sat, September 18', 'East Course', 'Details to come', '', '', 'Yes', '']] });
  assert.equal(out.ok, true);
  assert.equal(out.hours.length, 1);
  assert.deepEqual(out.events.map(e => e.name), ['Night Golf', 'Ryder Cup', 'Tip & Tuck']);
  assert.deepEqual(out.events[0], { name: 'Night Golf', date: 'Sat, July 10', course: 'East Course', status: 'Sign-up open',
    link: 'https://example.com/night', photo: 'https://example.com/n.jpg' });
  assert.equal(out.events[1].status, 'Opens soon');
  assert.ok(!JSON.stringify(out).includes('Call the band'));
  assert.ok(!JSON.stringify(out).includes('Draft'));
});

test('Club Events: hidden, blank and odd rows are cleaned up', () => {
  const out = loadContent({ Hours: HOURS, 'Lost & Found': LOST, Events: [EV_HEAD,
    ['Hidden', 'x', '', 'Sign-up open', '', '', 'No', ''],
    ['Hidden too', 'x', '', 'Sign-up open', '', '', ' no ', ''],
    ['', 'Sat, May 1', 'East Course', 'Opens soon', '', '', 'Yes', ''],
    ['Ladies Club Championship', 'Sat, July 17 – Sun, July 18', 'South Course — North Course', 'Confirmed', 'http://plain.example', 'javascript:alert(1)', 'Yes', ''],
    ['Quotes', 'x', '', 'Sign-up open', 'https://a.example/"><script>', '', 'Yes', '']] });
  assert.deepEqual(out.events.map(e => e.name), ['Ladies Club Championship', 'Quotes']);
  const e = out.events[0];
  assert.equal(e.date, 'Sat, July 17 to Sun, July 18');
  assert.equal(e.course, 'South Course to North Course');
  assert.equal(e.status, 'Details to come');
  assert.equal(e.link, '');
  assert.equal(e.photo, '');
  assert.equal(out.events[1].link, '');
});

test('Club Events: capped at 60 rows; no Events tab sends an empty list', () => {
  const grid = [EV_HEAD]; for (let i = 1; i <= 70; i++) grid.push(['Event ' + i, 'Date', '', 'Opens soon', '', '', 'Yes', '']);
  const out = loadContent({ Hours: HOURS, 'Lost & Found': LOST, Events: grid });
  assert.equal(out.events.length, 60);
  assert.equal(out.events[59].name, 'Event 60');
  assert.deepEqual(loadContent({ Hours: HOURS, 'Lost & Found': LOST }).events, []);
});
