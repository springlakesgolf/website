// Restaurant reservations for Spring Lakes. DiningRules (rules.js) is pasted
// above this file by build_gs.py. setup() is first so Run defaults to it.
// Behaves like tools/dining/mock_server.js on every endpoint; code.test.js checks it offline.

function setup() {
  ssCache_ = null;
  var ss = ss_();
  ss.setSpreadsheetTimeZone('America/Toronto');
  Object.keys(TABS).forEach(function (name, i) {
    var sh = ss.getSheetByName(name) || (i === 0 && ss.getSheets()[0].getLastRow() === 0 ? ss.getSheets()[0].setName(name) : ss.insertSheet(name));
    sh.getRange(1, 1, 1, TABS[name].length).setValues([TABS[name]]).setFontWeight('bold').setBackground('#323C60').setFontColor('#ffffff');
    sh.setFrozenRows(1);
    sh.getRange('A:Z').setNumberFormat('@');
  });
  var st = ss.getSheetByName('Settings');
  if (st.getLastRow() < 2) {
    st.getRange(2, 1, DEFAULTS.length, 2).setValues(DEFAULTS);
    // The Staff PIN value stays empty (staff calls are refused until it is set). Column C is a hint only.
    DEFAULTS.forEach(function (d, i) { if (d[0] === 'Staff PIN') st.getRange(i + 2, 3).setValue('Use 6 or more digits'); });
  }
  var status = SpreadsheetApp.newDataValidation().requireValueInList(['Booked', 'Seated', 'No-show', 'Cancelled'], true).build();
  ss.getSheetByName('Bookings').getRange('J2:J').setDataValidation(status);
  var dining = SpreadsheetApp.newDataValidation().requireValueInList(['Open', 'Closed', 'Limited'], true).build();
  ss.getSheetByName('Events').getRange('C2:C').setDataValidation(dining);
  ss.getSheetByName('Bookings').hideColumns(13, 2);
}

// Opens the sheet by ID when build_gs.py sets SHEET_ID (standalone script); otherwise the bound sheet.
// Opened once per execution: doGet, doPost, setup and clearTestRows reset ssCache_ before they start.
var ssCache_ = null;
function ss_() {
  if (!ssCache_) ssCache_ = typeof SHEET_ID !== 'undefined' && SHEET_ID ? SpreadsheetApp.openById(SHEET_ID) : SpreadsheetApp.getActiveSpreadsheet();
  return ssCache_;
}

function clearTestRows() {
  ssCache_ = null;
  var lock = LockService.getScriptLock();
  lock.waitLock(20000);
  try {
    var sh = ss_().getSheetByName('Bookings');
    var v = sh.getDataRange().getValues();
    for (var r = v.length - 1; r >= 1; r--) if (/^TEST/i.test(String(v[r][4]))) sh.deleteRow(r + 1);
    SpreadsheetApp.flush();
  } finally {
    lock.releaseLock();
  }
}

function sendTestEmail() {
  ssCache_ = null;
  var s = settings();
  confirmEmail({id: 'R0', date: today(), time: '19:00', guests: 2, name: 'TEST Member', email: s.testEmail, token: 'test'}, s);
}

// ---- constants ------------------------------------------------------------
var TABS = {
  Bookings: ['ID', 'Date', 'Time', 'Guests', 'Name', 'Member #', 'Email', 'Phone', 'Notes', 'Status', 'Source', 'Created', 'Token', 'Request id'],
  Settings: ['Setting', 'Value'],
  Blocked: ['ID', 'Date', 'From', 'To', 'Reason'],
  Events: ['Date', 'Event', 'Dining room', 'Guest limit'],
  Members: ['Member #', 'Last name']
};
var DEFAULTS = [['Guests per half hour', 20], ['Days ahead', 30], ['Same-day cutoff (minutes)', 120], ['Largest online party', 8],
  ['Staff PIN', ''], ['Clubhouse phone', '905-640-3633'], ['Cancel page', 'https://springlakesgolf.github.io/website/food-beverage/cancel/'],
  ['Email mode', 'Test'], ['Test email', 'cullen@springlakesgolf.com'], ['Reply-to', 'laurap@springlakesgolf.com'],
  ['Sunday', '17:00-20:30'], ['Monday', 'Closed'], ['Tuesday', '17:00-20:30'], ['Wednesday', '17:00-20:30'],
  ['Thursday', '17:00-20:30'], ['Friday', '17:00-20:30'], ['Saturday', '17:00-20:30']];
var DAYS = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
var STAFF = ['day', 'add', 'block', 'unblock', 'status', 'staffCancel'];
var ACTIONS = ['book', 'cancel'].concat(STAFF);
var PIN_MIN_LENGTH = 6, PIN_MAX_FAILS = 10, PIN_FAIL_SECONDS = 600, PIN_LOCK_SECONDS = 900;
var STATUSES = ['Booked', 'Seated', 'No-show'];
var MAX_BODY = 20 * 1024;

// ---- readers --------------------------------------------------------------
function tab(name) { return ss_().getSheetByName(name); }
function rows(name) { var v = tab(name).getDataRange().getDisplayValues(); return v.slice(1); }
function settings() {
  var m = {};
  rows('Settings').forEach(function (r) { m[r[0]] = String(r[1]).trim(); });
  var hours = {};
  DAYS.forEach(function (d, i) {
    var v = m[d] || 'Closed', p = v.split('-');
    hours[i] = /^\d{2}:\d{2}-\d{2}:\d{2}$/.test(v) ? {first: p[0], last: p[1]} : null;
  });
  return {guestsPerSlot: Number(m['Guests per half hour']) || 0, daysAhead: Number(m['Days ahead']) || 0,
          cutoffMinutes: Number(m['Same-day cutoff (minutes)']) || 0, maxParty: Number(m['Largest online party']) || 1,
          pin: (m['Staff PIN'] || '').length >= PIN_MIN_LENGTH ? m['Staff PIN'] : '', phone: m['Clubhouse phone'] || '', cancelPage: m['Cancel page'] || '',
          emailMode: m['Email mode'] || 'Test', testEmail: m['Test email'] || '', replyTo: m['Reply-to'] || '', hours: hours};
}
function bookings() {
  return rows('Bookings').filter(function (r) { return r[0]; }).map(function (r) {
    return {id: r[0], date: r[1], time: r[2], guests: Number(r[3]), name: r[4], member: r[5], email: r[6], phone: r[7],
            notes: r[8], status: r[9], source: r[10], token: r[12], rid: r[13]};
  });
}
function blocks() { return rows('Blocked').filter(function (r) { return r[0]; }).map(function (r) { return {id: r[0], date: r[1], from: r[2], to: r[3], reason: r[4]}; }); }
function events() { return rows('Events').filter(function (r) { return r[0]; }).map(function (r) { return {date: r[0], name: r[1], dining: r[2] || 'Open', limit: Number(r[3]) || 0}; }); }
function members() { return rows('Members').filter(function (r) { return r[0]; }).map(function (r) { return {number: r[0], last: r[1]}; }); }
function today() { return Utilities.formatDate(new Date(), 'America/Toronto', 'yyyy-MM-dd'); }
function nowMinutes() { var t = Utilities.formatDate(new Date(), 'America/Toronto', 'HH:mm').split(':'); return Number(t[0]) * 60 + Number(t[1]); }
function stamp() { return Utilities.formatDate(new Date(), 'America/Toronto', 'yyyy-MM-dd HH:mm'); }
function times(date, guests) {
  return DiningRules.openTimes({date: date, guests: guests, settings: settings(), bookings: bookings(), blocks: blocks(), events: events(),
                                today: today(), nowMinutes: nowMinutes()});
}
function nextId(prefix) {
  var p = PropertiesService.getScriptProperties(), cur = p.getProperty('seq_' + prefix);
  if (cur === null || cur === undefined || cur === '') {
    // No counter yet (new script, or properties cleared): continue after the highest ID already in the sheet.
    var re = new RegExp('^' + prefix + '(\\d+)$'), max = 0;
    rows(prefix === 'B' ? 'Blocked' : 'Bookings').forEach(function (r) {
      var m = re.exec(String(r[0])); if (m && Number(m[1]) > max) max = Number(m[1]);
    });
    cur = max;
  }
  var n = Number(cur) + 1;
  p.setProperty('seq_' + prefix, String(n));
  return prefix + n;
}
// The cache only speeds up replays and counts PIN failures; a broken cache must never fail a request.
function cacheGet(cache, k) { try { return cache.get(k); } catch (e) { console.error('cache get failed', e); return null; } }
function cachePut(cache, k, v, secs) { try { cache.put(k, v, secs); } catch (e) { console.error('cache put failed', e); } }
function cacheRemove(cache, k) { try { cache.remove(k); } catch (e) { console.error('cache remove failed', e); } }
// Staff PIN check. Call it with the script lock held, so the failure count is read, bumped and
// reset by one request at a time. Returns '' when the PIN is fine, else the error code to send back.
function checkPin(cache, b, s) {
  if (cacheGet(cache, 'pinlock')) { console.warn('staff PIN locked out, call refused'); return 'locked'; }
  if (s.pin && String(b.pin) === s.pin) { cacheRemove(cache, 'pinfail'); return ''; }
  var n = Number(cacheGet(cache, 'pinfail') || 0) + 1;
  cachePut(cache, 'pinfail', String(n), PIN_FAIL_SECONDS);
  if (n >= PIN_MAX_FAILS) { cachePut(cache, 'pinlock', '1', PIN_LOCK_SECONDS); console.warn('staff PIN locked out after ' + n + ' failed attempts'); }
  return 'pin';
}
function json(o) { return ContentService.createTextOutput(JSON.stringify(o)).setMimeType(ContentService.MimeType.JSON); }
function isDate(d) {
  if (typeof d !== 'string' || !/^\d{4}-\d{2}-\d{2}$/.test(d)) return false;
  var t = new Date(d + 'T12:00:00Z');
  return !isNaN(t.getTime()) && t.toISOString().slice(0, 10) === d;
}
function isTime(t) { return typeof t === 'string' && /^([01]\d|2[0-3]):[0-5]\d$/.test(t); }
function esc(v) {
  return String(v).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

// ---- public GET -----------------------------------------------------------
function doGet(e) {
  ssCache_ = null;
  try {
    var q = (e && e.parameter) || {}, s = settings();
    if (q.action === 'days') {
      var from = q.from === undefined || q.from === '' ? today() : q.from;
      if (!isDate(from)) return json({ok: false, error: 'date'});
      var count = Math.min(31, Math.max(1, Math.floor(Number(q.count)) || 14));
      return json({ok: true, days: DiningRules.days({from: from, count: count, settings: s, events: events(), today: today()})});
    }
    if (q.action === 'times') {
      if (!isDate(q.date)) return json({ok: false, error: 'date'});
      var r = times(q.date, Number(q.guests) || 2);
      return json({ok: true, status: r.status, reason: r.reason, times: r.times, maxParty: s.maxParty, phone: s.phone});
    }
    return json({ok: false, error: 'action'});
  } catch (err) {
    console.error('doGet failed', err);
    return json({ok: false, error: 'server'});
  }
}

// ---- POST -----------------------------------------------------------------
function doPost(e) {
  ssCache_ = null;
  var lock = null, locked = false, mailRow = null, s = null;
  try {
    var raw = String(e.postData.contents);
    if (raw.length > MAX_BODY) return json({ok: false, error: 'size'});
    var b;
    try { b = JSON.parse(raw); } catch (parseErr) { return json({ok: false, error: 'json'}); }
    if (!b || typeof b !== 'object') return json({ok: false, error: 'action'});
    if (ACTIONS.indexOf(b.action) < 0) return json({ok: false, error: 'action'});
    s = settings();
    var cache = CacheService.getScriptCache();
    // Staff calls need the PIN before anything else, so a replayed rid can never hand a cached
    // staff answer to someone without it. A locked-out or unset PIN is refused before the lock;
    // the compare and the failure count run just after waitLock, before any replay-cache read.
    var staff = STAFF.indexOf(b.action) >= 0;
    if (staff) {
      if (!s.pin) return json({ok: false, error: 'pin'});
      if (cacheGet(cache, 'pinlock')) { console.warn('staff PIN locked out, call refused'); return json({ok: false, error: 'locked'}); }
    }
    var key = b.rid ? 'rid:' + b.action + ':' + String(b.rid).slice(0, 100) : '';
    if (key && !staff) { var seen = cacheGet(cache, key); if (seen) return json(JSON.parse(seen)); }
    lock = LockService.getScriptLock();
    lock.waitLock(20000);
    locked = true;
    if (staff) {
      var pinErr = checkPin(cache, b, s);
      if (pinErr) return json({ok: false, error: pinErr});
    }
    if (key) { var again = cacheGet(cache, key); if (again) return json(JSON.parse(again)); }
    var out;
    if (b.action === 'book') out = book(b, s);
    else if (b.action === 'cancel') out = cancel(b);
    else if (b.action === 'day') out = day(b, s);
    else if (b.action === 'add') out = staffAdd(b);
    else if (b.action === 'block') out = block(b);
    else if (b.action === 'unblock') out = unblock(b);
    else out = setStatus(b);
    // book() hands back the confirmation row in _mail. It is sent after the lock is released
    // and never goes into the reply or the replay cache.
    if (out && out._mail) { mailRow = out._mail; delete out._mail; }
    if (key) cachePut(cache, key, JSON.stringify(out), 21600);
    return json(out);
  } catch (err) {
    console.error('doPost failed', err);
    return json({ok: false, error: 'server'});
  } finally {
    if (locked) {
      // Push pending writes to the sheet before the next caller gets the lock.
      try { SpreadsheetApp.flush(); } catch (flushErr) { console.error('flush failed', flushErr); }
      try { lock.releaseLock(); } catch (relErr) { console.error('releaseLock failed', relErr); }
    }
    if (mailRow) {
      try { confirmEmail(mailRow, s); } catch (mailErr) { console.error('confirmation email failed', mailErr); }
    }
  }
}

function book(b, s) {
  var C = DiningRules.clean;
  var err = isDate(b.date) ? DiningRules.checkBooking(b, s) : 'date';
  if (!err && typeof b.time !== 'string') err = 'time';
  if (err) return {ok: false, rid: b.rid, error: err};
  // The replay cache can be evicted or fail to write. The sheet is the record: a rid already booked is answered from its row.
  var rid = C(b.rid, 40);
  if (rid) {
    var prior = rows('Bookings').filter(function (r) { return r[13] === rid && r[10] === 'Website'; })[0];
    if (prior) return {ok: true, rid: b.rid, booking: {date: prior[1], time: prior[2], guests: Number(prior[3]), name: prior[4]}};
  }
  var t = times(b.date, Number(b.guests));
  var slot = t.times.filter(function (x) { return x.time === b.time; })[0];
  if (t.status !== 'open') return {ok: false, rid: b.rid, error: 'closed'};
  if (DiningRules.slotTimes(s, DiningRules.weekdayOf(b.date)).indexOf(b.time) < 0) return {ok: false, rid: b.rid, error: 'time'};
  if (!slot || !slot.open) return {ok: false, rid: b.rid, error: 'full'};
  // The member check comes last, right before the write, so a wrong number cannot be used to
  // learn which days or times are open, and the answers above reveal nothing about members.
  if (!DiningRules.isMember(members(), b.member, b.name)) return {ok: false, rid: b.rid, error: 'member'};
  var id = nextId('R'), token = Utilities.getUuid().replace(/-/g, '');
  var row = {id: id, date: b.date, time: b.time, guests: Number(b.guests), name: C(b.name, 80), greet: String(b.name).trim(), email: String(b.email).trim(), token: token};
  tab('Bookings').appendRow([id, b.date, b.time, row.guests, row.name, C(b.member, 20), C(b.email, 120), C(b.phone, 30),
    C(b.notes, 300), 'Booked', 'Website', stamp(), token, rid]);
  // _mail is stripped by doPost, which sends the confirmation after the lock is released.
  return {ok: true, rid: b.rid, booking: {date: row.date, time: row.time, guests: row.guests, name: row.name}, _mail: row};
}

function findRow(col, value) {
  var v = tab('Bookings').getDataRange().getDisplayValues();
  for (var r = 1; r < v.length; r++) if (v[r][col] === value) return {row: r + 1, values: v[r]};
  return null;
}
function cancel(b) {
  var token = b.token == null ? '' : String(b.token).trim();
  var f = token ? findRow(12, token) : null;
  if (!f || f.values[9] !== 'Booked') return {ok: false, rid: b.rid, error: 'token'};
  tab('Bookings').getRange(f.row, 10).setValue('Cancelled');
  return {ok: true, rid: b.rid, booking: {date: f.values[1], time: f.values[2], guests: Number(f.values[3]), name: f.values[4]}};
}
function day(b, s) {
  // Staff see the weekday hours and the Events only: past days and days past the member window show normally.
  var st = DiningRules.staffStatus(b.date, s, events());
  var list = bookings().filter(function (x) { return x.date === b.date && x.status !== 'Cancelled'; })
    .sort(function (a, c) { return a.time < c.time ? -1 : a.time > c.time ? 1 : 0; });
  var total = list.filter(function (x) { return x.status !== 'No-show'; }).reduce(function (n, x) { return n + x.guests; }, 0);
  return {ok: true, date: b.date, status: st.open ? 'open' : 'closed', reason: st.reason, totalGuests: total,
    bookings: list.map(function (x) { return {id: x.id, time: x.time, guests: x.guests, name: x.name, phone: x.phone, notes: x.notes, status: x.status, source: x.source}; }),
    blocks: blocks().filter(function (x) { return x.date === b.date; }).map(function (x) { return {id: x.id, from: x.from, to: x.to, reason: x.reason}; })};
}
function staffAdd(b) {
  var g = Number(b.guests);
  if (!isDate(b.date) || !isTime(b.time) || !(g >= 1) || Math.floor(g) !== g || !String(b.name == null ? '' : b.name).trim()) return {ok: false, rid: b.rid, error: 'invalid'};
  var C = DiningRules.clean, id = nextId('R');
  tab('Bookings').appendRow([id, b.date, b.time, g, C(b.name, 80), '', '', C(b.phone, 30), C(b.notes, 300), 'Booked', 'Phone', stamp(), '', C(b.rid, 40)]);
  return {ok: true, rid: b.rid, id: id};
}
function block(b) {
  if (!isDate(b.date) || !isTime(b.from) || !isTime(b.to) || !(b.from < b.to)) return {ok: false, rid: b.rid, error: 'invalid'};
  var id = nextId('B');
  tab('Blocked').appendRow([id, b.date, b.from, b.to, DiningRules.clean(b.reason, 120)]);
  return {ok: true, rid: b.rid, id: id};
}
function unblock(b) {
  var sh = tab('Blocked'), v = sh.getDataRange().getDisplayValues(), id = String(b.id == null ? '' : b.id);
  if (id) for (var r = v.length - 1; r >= 1; r--) if (v[r][0] === id) { sh.deleteRow(r + 1); return {ok: true}; }
  return {ok: false, error: 'id'};
}
function setStatus(b) {
  if (b.action === 'status' && STATUSES.indexOf(b.status) < 0) return {ok: false, error: 'status'};
  var id = String(b.id == null ? '' : b.id);
  var f = id ? findRow(0, id) : null;
  if (!f) return {ok: false, error: 'id'};
  tab('Bookings').getRange(f.row, 10).setValue(b.action === 'staffCancel' ? 'Cancelled' : b.status);
  return {ok: true};
}

// ---- email ----------------------------------------------------------------
function confirmEmail(row, s) {
  var dt = new Date(row.date + 'T12:00:00Z');
  var when = DAYS[dt.getUTCDay()] + ', ' + Utilities.formatDate(dt, 'UTC', 'MMMM d') + ' at ' + DiningRules.label(row.time);
  var link = s.cancelPage + '?t=' + encodeURIComponent(row.token);
  var to = s.emailMode === 'Live' ? row.email : s.testEmail;
  var html = '<div style="font-family:Arial,sans-serif;color:#222639;font-size:15px;line-height:1.6">'
    + '<p>Hi ' + esc(String(row.greet !== undefined ? row.greet : row.name).split(/\s+/)[0].slice(0, 40)) + ',</p>'
    + '<p>Your table at Spring Lakes Golf Club is booked.</p>'
    + '<p style="font-size:17px;color:#323C60"><b>' + esc(when) + '</b><br>Party of ' + esc(row.guests) + '</p>'
    + '<p>If your plans change, you can <a href="' + esc(link) + '" style="color:#323C60">cancel your reservation</a>, or call the clubhouse at ' + esc(s.phone) + '.</p>'
    + '<p>We look forward to seeing you.</p>'
    + '<p style="color:#5b6178;font-size:13px">Spring Lakes Golf Club<br>4962 Stouffville Road, Stouffville ON L4A 3S8</p></div>';
  MailApp.sendEmail({to: to, subject: 'Your table at Spring Lakes, ' + when, htmlBody: html,
                     replyTo: s.replyTo, name: 'Spring Lakes Golf Club'});
}
