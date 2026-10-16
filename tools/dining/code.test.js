// Offline test for the Apps Script backend. Builds its own source from rules.js
// (without the module.exports line) plus Code.gs, so it never reads dist/Dining.gs
// or config: no SHEET_ID line can leak in and a stale build cannot be tested by mistake.
// It loads that into a vm context with small in-memory fakes for the Google services,
// then drives doGet and doPost the way the web app would.
// Run: python3 tools/dining/build_gs.py && node --test tools/dining/*.test.js
const test = require('node:test');
const assert = require('node:assert');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const crypto = require('node:crypto');

const EXPORT_LINE = "if (typeof module !== 'undefined') module.exports = DiningRules;";
const RULES = fs.readFileSync(path.join(__dirname, 'rules.js'), 'utf8');
const CODE = fs.readFileSync(path.join(__dirname, 'Code.gs'), 'utf8');
assert.ok(RULES.includes(EXPORT_LINE), 'rules.js ends with the module.exports line');
const SOURCE = RULES.replace(EXPORT_LINE, '') + '\n' + CODE;

// ---- fakes ----------------------------------------------------------------
function fakeFormat(date, tz, pattern) {
  const parts = {};
  new Intl.DateTimeFormat('en-CA', {timeZone: tz, hourCycle: 'h23', year: 'numeric', month: '2-digit', day: '2-digit',
    hour: '2-digit', minute: '2-digit'}).formatToParts(date).forEach(p => { parts[p.type] = p.value; });
  const monthName = new Intl.DateTimeFormat('en-US', {timeZone: tz, month: 'long'}).format(date);
  const map = {yyyy: parts.year, MMMM: monthName, MM: parts.month, dd: parts.day, HH: parts.hour, mm: parts.minute, d: String(Number(parts.day))};
  return pattern.replace(/yyyy|MMMM|MM|dd|HH|mm|d/g, t => map[t]);
}

function fakeRange(sheet, r, c, nr, nc) {
  const self = {
    setValues(v) { v.forEach((row, i) => row.forEach((x, j) => sheet.put(r + i, c + j, x))); return self; },
    setValue(x) { sheet.log('setValue'); sheet.put(r, c, x); return self; },
    setFontWeight() { return self; }, setBackground() { return self; }, setFontColor() { return self; },
    setNumberFormat() { return self; }, setDataValidation() { return self; }
  };
  return self;
}
function noopRange() {
  const self = {};
  ['setValues', 'setValue', 'setFontWeight', 'setBackground', 'setFontColor', 'setNumberFormat', 'setDataValidation']
    .forEach(n => { self[n] = () => self; });
  return self;
}
function fakeSheet(name, log) {
  const sh = {
    name, data: [], log: log || (() => {}),
    put(r, c, x) {
      while (sh.data.length < r) sh.data.push([]);
      const row = sh.data[r - 1];
      while (row.length < c) row.push('');
      row[c - 1] = x;
    },
    getName() { return sh.name; },
    setName(n) { sh.name = n; return sh; },
    getLastRow() { return sh.data.length; },
    appendRow(row) { sh.log('appendRow'); sh.data.push(row.slice()); },
    deleteRow(n) { sh.log('deleteRow'); sh.data.splice(n - 1, 1); },
    getDataRange() {
      const width = Math.max(1, ...sh.data.map(r => r.length));
      const grid = (sh.data.length ? sh.data : [[]]).map(r => { const o = r.slice(); while (o.length < width) o.push(''); return o; });
      return {getValues: () => grid.map(r => r.slice()), getDisplayValues: () => grid.map(r => r.map(x => (x == null ? '' : String(x))))};
    },
    getRange(a, b, c, d) { return typeof a === 'number' ? fakeRange(sh, a, b, c || 1, d || 1) : noopRange(); },
    setFrozenRows() {}, hideColumns() {}
  };
  return sh;
}

function makeEnv(opts) {
  const events = [];
  const log = e => { events.push(e); };
  const sheets = [fakeSheet('Sheet1', log)];
  const ss = {
    getSheetByName: n => sheets.filter(s => s.name === n)[0] || null,
    insertSheet: n => { const s = fakeSheet(n, log); sheets.push(s); return s; },
    getSheets: () => sheets.slice(),
    setSpreadsheetTimeZone() {}
  };
  const env = {sheets, ss, opened: [], mail: [], mailFails: false, failSpreadsheet: false, cache: new Map(), props: new Map(),
    events, warns: [], lockFails: false, lockWaits: [], cachePutFails: false, cacheGets: 0, cacheTtl: new Map()};
  const ctx = {
    console: {log() {}, error() {}, warn(...a) { env.warns.push(a.join(' ')); }},
    SpreadsheetApp: {
      getActiveSpreadsheet() { if (env.failSpreadsheet) throw new Error('spreadsheet down'); return ss; },
      openById(id) { env.opened.push(id); return ss; },
      newDataValidation: () => { const b = {requireValueInList: () => b, build: () => ({})}; return b; },
      flush() { log('flush'); }
    },
    CacheService: {getScriptCache: () => ({
      get: k => { env.cacheGets++; log('cacheGet:' + k); return env.cache.has(k) ? env.cache.get(k) : null; },
      put: (k, v, ttl) => { log('cachePut:' + k); if (env.cachePutFails) throw new Error('cache down'); env.cache.set(k, v); env.cacheTtl.set(k, ttl); },
      remove: k => { log('cacheRemove:' + k); env.cache.delete(k); }
    })},
    LockService: {getScriptLock: () => ({
      waitLock(ms) { log('waitLock'); env.lockWaits.push(ms); if (env.lockFails) throw new Error('lock timeout'); },
      releaseLock() { log('releaseLock'); }
    })},
    PropertiesService: {getScriptProperties: () => ({
      getProperty: k => (env.props.has(k) ? env.props.get(k) : null),
      setProperty: (k, v) => { env.props.set(k, v); }
    })},
    Utilities: {formatDate: fakeFormat, getUuid: () => crypto.randomUUID()},
    MailApp: {sendEmail(m) { log('sendMail'); if (env.mailFails) throw new Error('mail quota'); env.mail.push(m); }},
    ContentService: {
      MimeType: {JSON: 'json'},
      createTextOutput: s => { const o = {setMimeType: () => o, getContent: () => s}; return o; }
    }
  };
  if (opts && opts.sheetId) ctx.SHEET_ID = opts.sheetId;
  vm.createContext(ctx);
  vm.runInContext(SOURCE, ctx);
  env.ctx = ctx;
  ctx.setup();
  setSetting(env, 'Staff PIN', '432198');
  ss.getSheetByName('Members').appendRow(['9001', 'Test']);
  events.length = 0;
  return env;
}

function setSetting(env, name, value) {
  const sh = env.ss.getSheetByName('Settings');
  const i = sh.data.findIndex(r => r[0] === name);
  assert.ok(i > 0, 'setting exists: ' + name);
  sh.put(i + 1, 2, value);
}
const get = (env, q) => JSON.parse(env.ctx.doGet({parameter: q}).getContent());
const post = (env, b) => JSON.parse(env.ctx.doPost({postData: {contents: JSON.stringify(b)}}).getContent());
const rowsOf = (env, tab) => env.ss.getSheetByName(tab).data.slice(1);

function torontoToday() { return new Date().toLocaleDateString('en-CA', {timeZone: 'America/Toronto'}); }
function addDays(d, n) { const t = new Date(d + 'T12:00:00Z'); t.setUTCDate(t.getUTCDate() + n); return t.toISOString().slice(0, 10); }
function weekday(d) { return new Date(d + 'T12:00:00Z').getUTCDay(); }
// First open (non-Monday) date at least `from` days out.
function openDate(from) { let n = from; while (weekday(addDays(torontoToday(), n)) === 1) n++; return addDays(torontoToday(), n); }
function mondayDate() { let n = 3; while (weekday(addDays(torontoToday(), n)) !== 1) n++; return addDays(torontoToday(), n); }

const member = (date, extra) => Object.assign({action: 'book', rid: 'r' + Math.random().toString(36).slice(2), date, time: '19:00', guests: 2,
  name: 'TEST Jo Test', member: '9001', email: 'jo@example.com', phone: '905 555 0101'}, extra || {});

// ---- tests ----------------------------------------------------------------
test('setup is the first function in Code.gs and builds the five tabs', () => {
  assert.strictEqual(/^function (\w+)/m.exec(CODE)[1], 'setup');
  const env = makeEnv();
  assert.deepStrictEqual(env.sheets.map(s => s.name), ['Bookings', 'Settings', 'Blocked', 'Events', 'Members']);
  assert.strictEqual(env.ss.getSheetByName('Bookings').data[0].length, 14);
  assert.strictEqual(env.ss.getSheetByName('Bookings').data[0][13], 'Request id');
  assert.strictEqual(env.ss.getSheetByName('Settings').data.length, 18);
  const pinRow = env.ss.getSheetByName('Settings').data.find(r => r[0] === 'Staff PIN');
  assert.strictEqual(pinRow[2], 'Use 6 or more digits');
  env.ctx.setup(); // running it again must not duplicate anything
  assert.strictEqual(env.sheets.length, 5);
  assert.strictEqual(env.ss.getSheetByName('Settings').data.length, 18);
});

test('days: shape, default start, clamp, bad from', () => {
  const env = makeEnv();
  const r = get(env, {action: 'days', count: '7'});
  assert.strictEqual(r.ok, true);
  assert.strictEqual(r.days.length, 7);
  assert.deepStrictEqual(Object.keys(r.days[0]), ['date', 'open', 'reason']);
  assert.strictEqual(r.days[0].date, torontoToday());
  assert.strictEqual(get(env, {action: 'days'}).days.length, 14);
  assert.strictEqual(get(env, {action: 'days', count: '99'}).days.length, 31);
  assert.strictEqual(get(env, {action: 'days', count: '-5'}).days.length, 1);
  assert.strictEqual(get(env, {action: 'days', from: 'soon'}).error, 'date');
  assert.strictEqual(get(env, {action: 'days', from: '2027-02-31'}).error, 'date');
  assert.strictEqual(get(env, {action: 'days', from: '2027-03-01', count: '2'}).days[0].date, '2027-03-01');
});

test('times: shape, closed Monday, bad date', () => {
  const env = makeEnv();
  const d = openDate(3);
  const r = get(env, {action: 'times', date: d, guests: '2'});
  assert.strictEqual(r.ok, true);
  assert.strictEqual(r.status, 'open');
  assert.strictEqual(r.maxParty, 8);
  assert.strictEqual(r.phone, '905-640-3633');
  assert.deepStrictEqual(r.times.map(t => t.time), ['17:00', '17:30', '18:00', '18:30', '19:00', '19:30', '20:00', '20:30']);
  assert.ok(r.times.every(t => t.open === true));
  const m = get(env, {action: 'times', date: mondayDate()});
  assert.strictEqual(m.status, 'closed');
  assert.strictEqual(m.reason, 'Closed');
  assert.deepStrictEqual(m.times, []);
  assert.strictEqual(get(env, {action: 'times', date: 'tomorrow'}).error, 'date');
  assert.strictEqual(get(env, {action: 'times'}).error, 'date');
  assert.strictEqual(get(env, {}).error, 'action');
});

test('book: succeeds, one row, one confirmation email to the Test address', () => {
  const env = makeEnv();
  const d = openDate(3);
  const body = member(d, {rid: 'a1'});
  const r = post(env, body);
  assert.deepStrictEqual(r, {ok: true, rid: 'a1', booking: {date: d, time: '19:00', guests: 2, name: 'TEST Jo Test'}});
  const rows = rowsOf(env, 'Bookings');
  assert.strictEqual(rows.length, 1);
  assert.strictEqual(rows[0][0], 'R1');
  assert.strictEqual(rows[0][9], 'Booked');
  assert.strictEqual(rows[0][10], 'Website');
  assert.match(rows[0][12], /^[0-9a-f]{32}$/);
  assert.strictEqual(rows[0][13], 'a1');
  assert.strictEqual(env.mail.length, 1);
  assert.strictEqual(env.mail[0].to, 'cullen@springlakesgolf.com');
  assert.strictEqual(env.mail[0].replyTo, 'laurap@springlakesgolf.com');
  assert.ok(env.mail[0].htmlBody.includes('?t=' + rows[0][12]));
  assert.ok(env.mail[0].htmlBody.includes('7:00 pm'));
  assert.ok(!/[–—]/.test(env.mail[0].htmlBody + env.mail[0].subject), 'no em or en dashes in the email');
  const t = get(env, {action: 'times', date: d, guests: '2'});
  assert.strictEqual(t.times.find(x => x.time === '19:00').open, true); // 2 of 20 used
});

test('book: Live mode emails the member; a mail failure does not fail the booking', () => {
  const env = makeEnv();
  setSetting(env, 'Email mode', 'Live');
  const d = openDate(3);
  assert.strictEqual(post(env, member(d, {rid: 'l1'})).ok, true);
  assert.strictEqual(env.mail[0].to, 'jo@example.com');
  env.mailFails = true;
  const r = post(env, member(d, {rid: 'l2', time: '18:00'}));
  assert.strictEqual(r.ok, true);
  assert.strictEqual(rowsOf(env, 'Bookings').length, 2);
});

test('book: HTML in a name is escaped in the email', () => {
  const env = makeEnv();
  assert.strictEqual(post(env, member(openDate(3), {name: '<b>Jo</b> Test'})).ok, true);
  assert.ok(!env.mail[0].htmlBody.includes('<b>Jo'));
});

test('replay with the same rid adds no second row and no second email', () => {
  const env = makeEnv();
  const body = member(openDate(3), {rid: 'same'});
  const a = post(env, body), b = post(env, body);
  assert.deepStrictEqual(b, a);
  assert.strictEqual(rowsOf(env, 'Bookings').length, 1);
  assert.strictEqual(env.mail.length, 1);
  // the cache is per action: the same rid on a cancel is a fresh request
  assert.strictEqual(post(env, {action: 'cancel', rid: 'same', token: 'nope'}).error, 'token');
});

test('book: wrong member number gives member, nothing written', () => {
  const env = makeEnv();
  assert.strictEqual(post(env, member(openDate(3), {member: '1111'})).error, 'member');
  assert.strictEqual(post(env, member(openDate(3), {name: 'TEST Jo Smith'})).error, 'member');
  assert.strictEqual(rowsOf(env, 'Bookings').length, 0);
  assert.strictEqual(env.mail.length, 0);
});

test('book: validation codes, closed day, non-slot time', () => {
  const env = makeEnv();
  const d = openDate(3);
  assert.strictEqual(post(env, member(d, {guests: 0})).error, 'guests');
  assert.strictEqual(post(env, member(d, {guests: 9})).error, 'big');
  assert.strictEqual(post(env, member(d, {email: 'nope'})).error, 'email');
  assert.strictEqual(post(env, member(d, {date: 20270301})).error, 'date');
  assert.strictEqual(post(env, member(mondayDate())).error, 'closed');
  assert.strictEqual(post(env, member(d, {time: '19:15'})).error, 'time');
  assert.strictEqual(post(env, member(d, {time: '16:00'})).error, 'time');
  assert.strictEqual(rowsOf(env, 'Bookings').length, 0);
});

test('book: a full slot gives full', () => {
  const env = makeEnv();
  const d = openDate(3);
  const a = post(env, {action: 'add', pin: '432198', date: d, time: '18:00', guests: 19, name: 'Big Group'});
  assert.strictEqual(a.ok, true);
  assert.strictEqual(post(env, member(d, {time: '18:00'})).error, 'full');
  assert.strictEqual(post(env, member(d, {time: '18:30'})).ok, true);
  const t = get(env, {action: 'times', date: d, guests: '2'});
  assert.strictEqual(t.times.find(x => x.time === '18:00').open, false);
});

test('staff PIN: wrong PIN gives pin before the replay cache, empty sheet PIN always fails', () => {
  const env = makeEnv();
  const d = openDate(3);
  const ok = post(env, {action: 'day', pin: '432198', rid: 'cached', date: d});
  assert.strictEqual(ok.ok, true);
  assert.strictEqual(post(env, {action: 'day', pin: '0000', rid: 'cached', date: d}).error, 'pin');
  assert.strictEqual(post(env, {action: 'day', rid: 'cached', date: d}).error, 'pin');
  assert.strictEqual(post(env, {action: 'day', pin: 432198, date: d}).ok, true); // a number PIN still matches
  for (const action of ['add', 'block', 'unblock', 'status', 'staffCancel']) {
    assert.strictEqual(post(env, {action, pin: 'bad', id: 'R1'}).error, 'pin', action);
  }
  setSetting(env, 'Staff PIN', '');
  assert.strictEqual(post(env, {action: 'day', pin: '', date: d}).error, 'pin');
  assert.strictEqual(post(env, {action: 'day', date: d}).error, 'pin');
});

test('cancel: empty token gives token, real token frees the seats, second cancel fails', () => {
  const env = makeEnv();
  const d = openDate(3);
  assert.strictEqual(post(env, {action: 'add', pin: '432198', date: d, time: '19:00', guests: 3, name: 'Phone Call'}).ok, true); // empty token row
  assert.strictEqual(post(env, member(d, {rid: 'c1', time: '20:00', guests: 8})).ok, true);
  const token = rowsOf(env, 'Bookings')[1][12];
  assert.strictEqual(post(env, {action: 'cancel', token: ''}).error, 'token');
  assert.strictEqual(post(env, {action: 'cancel'}).error, 'token');
  assert.strictEqual(post(env, {action: 'cancel', token: '   '}).error, 'token');
  assert.strictEqual(rowsOf(env, 'Bookings').every(r => r[9] === 'Booked'), true);
  // 8 guests at 20:00, so a party of 13 no longer fits there
  assert.strictEqual(get(env, {action: 'times', date: d, guests: '13'}).times.find(x => x.time === '20:00').open, false);
  const r = post(env, {action: 'cancel', rid: 'cx', token});
  assert.deepStrictEqual(r, {ok: true, rid: 'cx', booking: {date: d, time: '20:00', guests: 8, name: 'TEST Jo Test'}});
  assert.strictEqual(rowsOf(env, 'Bookings')[1][9], 'Cancelled');
  assert.strictEqual(get(env, {action: 'times', date: d, guests: '13'}).times.find(x => x.time === '20:00').open, true);
  assert.strictEqual(post(env, {action: 'cancel', token}).error, 'token');
});

test('staff add: valid, source Phone, empty token; invalid cases', () => {
  const env = makeEnv();
  const d = openDate(3);
  const r = post(env, {action: 'add', pin: '432198', rid: 'sa', date: d, time: '17:30', guests: 4, name: 'Ann Lee', phone: '905 555 0000', notes: '=cmd'});
  assert.deepStrictEqual(r, {ok: true, rid: 'sa', id: 'R1'});
  const row = rowsOf(env, 'Bookings')[0];
  assert.strictEqual(row[10], 'Phone');
  assert.strictEqual(row[12], '');
  assert.strictEqual(row[8], "'=cmd");
  const bad = [{date: 'x'}, {date: '2027-02-31'}, {time: '5pm'}, {time: '25:00'}, {guests: 0}, {guests: 2.5}, {guests: 'many'}, {name: '  '}, {name: undefined}];
  bad.forEach(o => assert.strictEqual(post(env, Object.assign({action: 'add', pin: '432198', date: d, time: '17:30', guests: 2, name: 'Ann'}, o)).error, 'invalid', JSON.stringify(o)));
  assert.strictEqual(rowsOf(env, 'Bookings').length, 1);
});

test('day: shape for staff, cancelled rows hidden, no-show not counted', () => {
  const env = makeEnv();
  const d = openDate(3);
  post(env, {action: 'add', pin: '432198', date: d, time: '19:00', guests: 4, name: 'Ann Lee', phone: '1', notes: 'window'});
  post(env, {action: 'add', pin: '432198', date: d, time: '18:00', guests: 2, name: 'Bo Kim'});
  post(env, {action: 'add', pin: '432198', date: d, time: '18:30', guests: 6, name: 'Cy Roe'});
  post(env, {action: 'add', pin: '432198', date: d, time: '20:00', guests: 1, name: 'Di Fox'});
  assert.strictEqual(post(env, {action: 'status', pin: '432198', id: 'R3', status: 'No-show'}).ok, true);
  assert.strictEqual(post(env, {action: 'staffCancel', pin: '432198', id: 'R4'}).ok, true);
  const b = post(env, {action: 'block', pin: '432198', date: d, from: '20:00', to: '21:00', reason: 'Private'});
  const r = post(env, {action: 'day', pin: '432198', date: d});
  assert.strictEqual(r.ok, true);
  assert.strictEqual(r.date, d);
  assert.strictEqual(r.status, 'open');
  assert.strictEqual(r.totalGuests, 6); // 4 + 2; the no-show is not counted, the cancelled row is gone
  assert.deepStrictEqual(r.bookings.map(x => x.id), ['R2', 'R3', 'R1']);
  assert.deepStrictEqual(Object.keys(r.bookings[2]), ['id', 'time', 'guests', 'name', 'phone', 'notes', 'status', 'source']);
  assert.deepStrictEqual(r.blocks, [{id: b.id, from: '20:00', to: '21:00', reason: 'Private'}]);
  assert.ok(!JSON.stringify(r).includes('token'));
});

test('block and unblock: validation, effect on times, unknown id', () => {
  const env = makeEnv();
  const d = openDate(3);
  ['', 'x', '25:00'].forEach(f => assert.strictEqual(post(env, {action: 'block', pin: '432198', date: d, from: f, to: '20:00'}).error, 'invalid', f));
  assert.strictEqual(post(env, {action: 'block', pin: '432198', date: d, from: '20:00', to: '19:00'}).error, 'invalid');
  assert.strictEqual(post(env, {action: 'block', pin: '432198', date: d, from: '19:00', to: '19:00'}).error, 'invalid');
  assert.strictEqual(post(env, {action: 'block', pin: '432198', date: 'nope', from: '18:00', to: '19:00'}).error, 'invalid');
  assert.strictEqual(post(env, {action: 'block', pin: '432198', from: '18:00', to: '19:00'}).error, 'invalid');
  const b = post(env, {action: 'block', pin: '432198', date: d, from: '18:00', to: '19:00', reason: 'Wedding'});
  assert.strictEqual(b.ok, true);
  assert.match(b.id, /^B\d+$/);
  const open = () => get(env, {action: 'times', date: d, guests: '2'}).times.filter(x => x.open).map(x => x.time);
  assert.deepStrictEqual(open(), ['17:00', '17:30', '19:00', '19:30', '20:00', '20:30']);
  assert.deepStrictEqual(post(env, {action: 'unblock', pin: '432198', id: b.id}), {ok: true});
  assert.strictEqual(open().length, 8);
  assert.strictEqual(post(env, {action: 'unblock', pin: '432198', id: b.id}).error, 'id');
  assert.strictEqual(post(env, {action: 'unblock', pin: '432198'}).error, 'id');
});

test('status: only Booked, Seated, No-show; unknown id gives id', () => {
  const env = makeEnv();
  const d = openDate(3);
  post(env, {action: 'add', pin: '432198', date: d, time: '19:00', guests: 2, name: 'Ann Lee'});
  assert.strictEqual(post(env, {action: 'status', pin: '432198', id: 'R1', status: 'Seated'}).ok, true);
  assert.strictEqual(rowsOf(env, 'Bookings')[0][9], 'Seated');
  assert.strictEqual(post(env, {action: 'status', pin: '432198', id: 'R1', status: 'No-show'}).ok, true);
  assert.strictEqual(post(env, {action: 'status', pin: '432198', id: 'R1', status: 'Booked'}).ok, true);
  assert.strictEqual(post(env, {action: 'status', pin: '432198', id: 'R1', status: 'Cancelled'}).error, 'status');
  assert.strictEqual(post(env, {action: 'status', pin: '432198', id: 'R1', status: 'Gone'}).error, 'status');
  assert.strictEqual(post(env, {action: 'status', pin: '432198', id: 'R99', status: 'Seated'}).error, 'id');
  assert.strictEqual(post(env, {action: 'staffCancel', pin: '432198', id: 'R99'}).error, 'id');
  assert.strictEqual(post(env, {action: 'staffCancel', pin: '432198', id: 'R1'}).ok, true);
  assert.strictEqual(rowsOf(env, 'Bookings')[0][9], 'Cancelled');
});

test('bad input: json, unknown action, oversize body, server error', () => {
  const env = makeEnv();
  const raw = s => JSON.parse(env.ctx.doPost({postData: {contents: s}}).getContent());
  assert.strictEqual(raw('{nope').error, 'json');
  assert.strictEqual(raw('null').error, 'action');
  assert.strictEqual(post(env, {action: 'dance'}).error, 'action');
  assert.strictEqual(raw(JSON.stringify({action: 'book', pad: 'x'.repeat(21 * 1024)})).error, 'size');
  assert.strictEqual(JSON.parse(env.ctx.doPost({}).getContent()).ok, false);
  env.failSpreadsheet = true;
  assert.deepStrictEqual(post(env, member(openDate(3))), {ok: false, error: 'server'});
  assert.deepStrictEqual(get(env, {action: 'days'}), {ok: false, error: 'server'});
});

test('clearTestRows removes only TEST rows; sendTestEmail goes to the Test email', () => {
  const env = makeEnv();
  const d = openDate(3);
  post(env, member(d, {name: 'TEST Jo Test'}));
  post(env, {action: 'add', pin: '432198', date: d, time: '18:00', guests: 2, name: 'Real Person'});
  env.mail.length = 0;
  env.ctx.clearTestRows();
  assert.deepStrictEqual(rowsOf(env, 'Bookings').map(r => r[4]), ['Real Person']);
  env.ctx.sendTestEmail();
  assert.strictEqual(env.mail.length, 1);
  assert.strictEqual(env.mail[0].to, 'cullen@springlakesgolf.com');
});

// ---- review fixes ---------------------------------------------------------
const lockOrder = env => env.events.filter(e => e !== 'setValue' && !/^cache/.test(e));
const bookingOrder = env => env.events.filter(e => ['waitLock', 'appendRow', 'flush', 'releaseLock', 'sendMail'].includes(e));

test('book: flush happens after the write and before the lock is released; the email goes after the unlock', () => {
  const env = makeEnv();
  assert.strictEqual(post(env, member(openDate(3))).ok, true);
  assert.deepStrictEqual(bookingOrder(env), ['waitLock', 'appendRow', 'flush', 'releaseLock', 'sendMail']);
});

test('book: the reply and the replay cache never contain the mail row or the cancel token', () => {
  const env = makeEnv();
  const r = post(env, member(openDate(3), {rid: 'nomail'}));
  assert.strictEqual(r.ok, true);
  assert.deepStrictEqual(Object.keys(r), ['ok', 'rid', 'booking']);
  const token = rowsOf(env, 'Bookings')[0][12];
  assert.ok(token);
  const cached = [...env.cache.entries()].filter(([k]) => k.startsWith('rid:'));
  assert.strictEqual(cached.length, 1);
  cached.forEach(([k, v]) => { assert.ok(!v.includes(token), 'token not cached'); assert.ok(!v.includes('_mail'), 'no mail field cached'); assert.ok(!v.includes('jo@example.com')); });
  assert.ok(!JSON.stringify(r).includes(token));
});

test('book: a mail failure after the unlock still returns ok and leaves the lock released', () => {
  const env = makeEnv();
  env.mailFails = true;
  assert.strictEqual(post(env, member(openDate(3))).ok, true);
  assert.deepStrictEqual(bookingOrder(env), ['waitLock', 'appendRow', 'flush', 'releaseLock', 'sendMail']);
});

test('book: an impossible calendar date gives date', () => {
  const env = makeEnv();
  assert.strictEqual(post(env, member('2026-02-31')).error, 'date');
  assert.strictEqual(post(env, member('2027-13-01')).error, 'date');
  assert.strictEqual(post(env, member('2027-04-31')).error, 'date');
  assert.strictEqual(rowsOf(env, 'Bookings').length, 0);
});

test('book: the member check comes last, so a wrong member number learns nothing about open days', () => {
  const env = makeEnv();
  const d = openDate(3);
  const wrong = {member: '1111'};
  assert.strictEqual(post(env, member(mondayDate(), wrong)).error, 'closed');
  assert.strictEqual(post(env, member(d, Object.assign({time: '19:15'}, wrong))).error, 'time');
  assert.strictEqual(post(env, {action: 'add', pin: '432198', date: d, time: '18:00', guests: 19, name: 'Big Group'}).ok, true);
  assert.strictEqual(post(env, member(d, Object.assign({time: '18:00'}, wrong))).error, 'full');
  assert.strictEqual(post(env, member(d, Object.assign({time: '18:30'}, wrong))).error, 'member');
  assert.strictEqual(rowsOf(env, 'Bookings').length, 1); // only the staff booking
});

test('staff call and a rejected call also flush before releasing the lock', () => {
  const env = makeEnv();
  post(env, {action: 'day', pin: '432198', date: openDate(3)});
  assert.deepStrictEqual(lockOrder(env), ['waitLock', 'flush', 'releaseLock']);
  env.events.length = 0;
  post(env, member(openDate(3), {member: '1111'}));
  assert.deepStrictEqual(lockOrder(env), ['waitLock', 'flush', 'releaseLock']);
});

test('waitLock failure gives server, no rows, no mail, no release', () => {
  const env = makeEnv();
  env.lockFails = true;
  assert.deepStrictEqual(post(env, member(openDate(3))), {ok: false, error: 'server'});
  assert.strictEqual(rowsOf(env, 'Bookings').length, 0);
  assert.strictEqual(env.mail.length, 0);
  assert.ok(!env.events.includes('releaseLock'));
});

test('book: a cache.put failure does not turn a written booking into server', () => {
  const env = makeEnv();
  env.cachePutFails = true;
  const r = post(env, member(openDate(3), {rid: 'cp1'}));
  assert.strictEqual(r.ok, true);
  assert.strictEqual(rowsOf(env, 'Bookings').length, 1);
  assert.strictEqual(env.mail.length, 1);
});

test('book: same rid after the cache forgot it adds no second row and no second email', () => {
  const env = makeEnv();
  const body = member(openDate(3), {rid: 'evict'});
  const a = post(env, body);
  assert.strictEqual(a.ok, true);
  env.cache.clear(); // simulate eviction
  const b = post(env, body);
  assert.deepStrictEqual(b, a);
  assert.strictEqual(rowsOf(env, 'Bookings').length, 1);
  assert.strictEqual(env.mail.length, 1);
});

test('staff PIN lockout: 10 wrong PINs lock even the right PIN; clearing the cache unlocks', () => {
  const env = makeEnv();
  const d = openDate(3);
  for (let i = 0; i < 10; i++) assert.strictEqual(post(env, {action: 'day', pin: 'bad' + i, date: d}).error, 'pin');
  assert.strictEqual(env.cacheTtl.get('pinfail'), 600);
  assert.strictEqual(env.cacheTtl.get('pinlock'), 900);
  assert.deepStrictEqual(post(env, {action: 'day', pin: '432198', date: d}), {ok: false, error: 'locked'});
  assert.deepStrictEqual(post(env, {action: 'add', pin: 'bad', date: d}), {ok: false, error: 'locked'});
  assert.ok(env.warns.length >= 1);
  assert.ok(env.cache.has('pinlock'), 'a correct PIN does not clear an active lock');
  env.cache.clear();
  assert.strictEqual(post(env, {action: 'day', pin: '432198', date: d}).ok, true);
  assert.strictEqual(post(env, member(d)).ok, true); // public calls are never locked out
});

test('staff PIN lockout: a correct PIN resets the failure count when no lock is active', () => {
  const env = makeEnv();
  const d = openDate(3);
  for (let i = 0; i < 9; i++) post(env, {action: 'day', pin: 'bad', date: d});
  assert.strictEqual(post(env, {action: 'day', pin: '432198', date: d}).ok, true);
  for (let i = 0; i < 9; i++) assert.strictEqual(post(env, {action: 'day', pin: 'bad', date: d}).error, 'pin');
  assert.strictEqual(post(env, {action: 'day', pin: '432198', date: d}).ok, true);
});

test('staff PIN: the 10th wrong PIN sets pinlock, the 9th does not', () => {
  const env = makeEnv();
  const d = openDate(3);
  for (let i = 1; i <= 10; i++) {
    assert.strictEqual(post(env, {action: 'day', pin: 'bad' + i, date: d}).error, 'pin', 'attempt ' + i);
    assert.strictEqual(env.cache.has('pinlock'), i === 10, 'pinlock after attempt ' + i);
    assert.strictEqual(env.cache.get('pinfail'), String(i));
  }
  assert.strictEqual(post(env, {action: 'day', pin: '432198', date: d}).error, 'locked');
});

test('staff PIN: refused before the lock when locked, compared after waitLock and before any replay-cache read', () => {
  const env = makeEnv();
  const d = openDate(3);
  // Wrong PIN: pinlock fast check, then lock, then the failure count, and never the rid cache.
  post(env, {action: 'day', pin: 'nope99', rid: 'x1', date: d});
  assert.deepStrictEqual(env.events.filter(e => e !== 'setValue'),
    ['cacheGet:pinlock', 'waitLock', 'cacheGet:pinlock', 'cacheGet:pinfail', 'cachePut:pinfail', 'flush', 'releaseLock']);
  // Right PIN: the compare (failure reset) is after waitLock and before the rid cache get.
  env.events.length = 0;
  assert.strictEqual(post(env, {action: 'day', pin: '432198', rid: 'x2', date: d}).ok, true);
  const ev = env.events.filter(e => e !== 'setValue');
  const lockAt = ev.indexOf('waitLock'), pinAt = ev.indexOf('cacheRemove:pinfail'), ridAt = ev.findIndex(e => e.startsWith('cacheGet:rid:'));
  assert.ok(lockAt >= 0 && pinAt > lockAt, 'PIN compare after waitLock: ' + ev.join(','));
  assert.ok(ridAt > pinAt, 'replay cache read after the PIN compare: ' + ev.join(','));
  assert.ok(ev.slice(0, lockAt).every(e => e === 'cacheGet:pinlock'), 'only the pinlock read before the lock: ' + ev.join(','));
  // Locked: refused before waitLock.
  env.cache.set('pinlock', '1');
  env.events.length = 0;
  assert.deepStrictEqual(post(env, {action: 'day', pin: '432198', rid: 'x3', date: d}), {ok: false, error: 'locked'});
  assert.ok(!env.events.includes('waitLock'));
});

test('staff PIN: a lock set while a request waited for the script lock still refuses it', () => {
  const env = makeEnv();
  const d = openDate(3);
  const orig = env.ctx.LockService.getScriptLock;
  env.ctx.LockService.getScriptLock = () => { const l = orig(); const w = l.waitLock; l.waitLock = ms => { w(ms); env.cache.set('pinlock', '1'); }; return l; };
  assert.strictEqual(post(env, {action: 'day', pin: '432198', date: d}).error, 'locked');
});

test('staff PIN: a sheet PIN shorter than 6 characters counts as unset', () => {
  const env = makeEnv();
  const d = openDate(3);
  setSetting(env, 'Staff PIN', '4321');
  assert.strictEqual(post(env, {action: 'day', pin: '4321', date: d}).error, 'pin');
  setSetting(env, 'Staff PIN', ' 12345 ');
  assert.strictEqual(post(env, {action: 'day', pin: '12345', date: d}).error, 'pin');
  setSetting(env, 'Staff PIN', ' 123456 ');
  assert.strictEqual(post(env, {action: 'day', pin: '123456', date: d}).ok, true);
});

test('book: the confirmation greeting uses the raw name, the sheet keeps the cleaned copy', () => {
  const env = makeEnv();
  assert.strictEqual(post(env, member(openDate(3), {name: '  =Jo <b> Test '})).ok, true);
  assert.strictEqual(rowsOf(env, 'Bookings')[0][4], "'=Jo <b> Test");
  assert.ok(env.mail[0].htmlBody.includes('<p>Hi =Jo,</p>'), env.mail[0].htmlBody);
  const env2 = makeEnv();
  post(env2, member(openDate(3), {name: '<i>Jo Test'}));
  assert.ok(env2.mail[0].htmlBody.includes('<p>Hi &lt;i&gt;Jo,</p>'));
});

test('book: the confirmation goes to the validated email, the sheet keeps the cleaned copy', () => {
  const env = makeEnv();
  setSetting(env, 'Email mode', 'Live');
  assert.strictEqual(post(env, member(openDate(3), {email: '  +jo@example.com '})).ok, true);
  assert.strictEqual(env.mail[0].to, '+jo@example.com');
  assert.strictEqual(rowsOf(env, 'Bookings')[0][6], "'+jo@example.com");
});

test('book: a name and phone that start like formulas are stored with a leading quote, mail still goes', () => {
  const env = makeEnv();
  const r = post(env, member(openDate(3), {name: '=HYPERLINK("x") Test', phone: '+1 905 555 0101'}));
  assert.strictEqual(r.ok, true);
  const row = rowsOf(env, 'Bookings')[0];
  assert.strictEqual(row[4], "'=HYPERLINK(\"x\") Test");
  assert.strictEqual(row[7], "'+1 905 555 0101");
  assert.strictEqual(env.mail.length, 1);
});

test('clearTestRows takes the lock, flushes, and releases even when it throws', () => {
  const env = makeEnv();
  post(env, member(openDate(3)));
  env.events.length = 0;
  env.lockWaits.length = 0;
  env.ctx.clearTestRows();
  assert.deepStrictEqual(env.events, ['waitLock', 'deleteRow', 'flush', 'releaseLock']);
  assert.deepStrictEqual(env.lockWaits, [20000]);
  env.events.length = 0;
  env.failSpreadsheet = true;
  assert.throws(() => env.ctx.clearTestRows());
  assert.deepStrictEqual(env.events, ['waitLock', 'releaseLock']);
});

test('unknown action gives action before any cache use', () => {
  const env = makeEnv();
  assert.deepStrictEqual(post(env, {action: 'dance', rid: 'x1'}), {ok: false, error: 'action'});
  assert.deepStrictEqual(post(env, {action: 'toString', rid: 'x2'}), {ok: false, error: 'action'});
  assert.deepStrictEqual(post(env, {rid: 'x3'}), {ok: false, error: 'action'});
  assert.strictEqual(env.cache.size, 0);
  assert.strictEqual(env.cacheGets, 0);
});

test('ID sequences seed from the highest existing row when the property is missing', () => {
  const env = makeEnv();
  env.ss.getSheetByName('Bookings').appendRow(['R7', '2027-01-01', '19:00', 2, 'Old', '', '', '', '', 'Booked', 'Phone', '', '', '']);
  env.ss.getSheetByName('Blocked').appendRow(['B3', '2027-01-01', '18:00', '19:00', 'Old']);
  const d = openDate(3);
  assert.strictEqual(post(env, {action: 'add', pin: '432198', date: d, time: '17:30', guests: 2, name: 'Ann Lee'}).id, 'R8');
  assert.strictEqual(post(env, {action: 'block', pin: '432198', date: d, from: '18:00', to: '19:00'}).id, 'B4');
  assert.strictEqual(post(env, {action: 'add', pin: '432198', date: d, time: '18:00', guests: 2, name: 'Bo Kim'}).id, 'R9');
});

test('SHEET_ID in the context: the sheet is opened by that ID and a days call works', () => {
  const env = makeEnv({sheetId: '1AbC_dEf-GhI'});
  env.opened.length = 0;
  const r = get(env, {action: 'days', count: '3'});
  assert.strictEqual(r.ok, true);
  assert.strictEqual(r.days.length, 3);
  assert.ok(env.opened.length > 0, 'openById was used');
  assert.ok(env.opened.every(id => id === '1AbC_dEf-GhI'), 'openById got the configured id');
});

test('day: staff see weekday hours and Events only, not the member booking window', () => {
  const env = makeEnv();
  const past = addDays(torontoToday(), -3), far = addDays(torontoToday(), 90);
  // Past and far-future open weekdays read "open" with no reason for staff.
  [past, far].forEach(d => {
    if (weekday(d) === 1) return;
    const r = post(env, {action: 'day', pin: '432198', date: d});
    assert.strictEqual(r.status, 'open', d);
    assert.strictEqual(r.reason, '', d);
  });
  // A Monday is closed by the weekday hours, in the past or not.
  let mon = addDays(torontoToday(), -1); while (weekday(mon) !== 1) mon = addDays(mon, -1);
  const m = post(env, {action: 'day', pin: '432198', date: mon});
  assert.strictEqual(m.status, 'closed');
  assert.strictEqual(m.reason, 'Closed');
  // Past bookings show on a past day.
  assert.strictEqual(post(env, {action: 'add', pin: '432198', date: past, time: '19:00', guests: 2, name: 'Old Booking'}).ok, true);
  const p = post(env, {action: 'day', pin: '432198', date: past});
  assert.strictEqual(p.bookings.length, 1);
  assert.strictEqual(p.totalGuests, 2);
  // Events still apply: Closed and Limited both name the event.
  const d = openDate(3), ev = env.ss.getSheetByName('Events');
  ev.appendRow([d, 'Member Guest', 'Closed', '']);
  const c = post(env, {action: 'day', pin: '432198', date: d});
  assert.strictEqual(c.status, 'closed');
  assert.strictEqual(c.reason, 'Member Guest');
  const d2 = addDays(d, 1); if (weekday(d2) !== 1) {
    ev.appendRow([d2, 'Wedding', 'Limited', 6]);
    const l = post(env, {action: 'day', pin: '432198', date: d2});
    assert.strictEqual(l.status, 'open');
    assert.strictEqual(l.reason, 'Wedding');
  }
});

test('book: the email greeting is capped at 40 characters', () => {
  const env = makeEnv();
  const long = 'A'.repeat(100);
  assert.strictEqual(post(env, member(openDate(3), {name: long + ' Test'})).ok, true);
  assert.ok(env.mail[0].htmlBody.includes('<p>Hi ' + 'A'.repeat(40) + ',</p>'), env.mail[0].htmlBody.slice(0, 200));
  assert.ok(!env.mail[0].htmlBody.includes('A'.repeat(41)));
});

test('the spreadsheet is opened once per execution', () => {
  const env = makeEnv({sheetId: '1AbC_dEf-GhI'});
  env.opened.length = 0;
  assert.strictEqual(post(env, member(openDate(3))).ok, true);
  assert.strictEqual(env.opened.length, 1, 'doPost book opened the sheet once');
  env.opened.length = 0;
  get(env, {action: 'times', date: openDate(3), guests: '2'});
  assert.strictEqual(env.opened.length, 1, 'doGet opened the sheet once');
  env.opened.length = 0;
  env.ctx.clearTestRows();
  assert.strictEqual(env.opened.length, 1, 'clearTestRows opened the sheet once');
});
