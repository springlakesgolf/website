// tools/dining/mock_server.js
// Local stand-in for the Dining Apps Script, for building the panel and the
// iPad page without touching the live sheet. Data lives in memory only.
// Run: node tools/dining/mock_server.js 8745   (staff PIN: 111111, member 1234 / Test)
// Staff PINs follow the real script: at least 6 characters, and 10 wrong PINs within
// 10 minutes lock every staff call ({ok:false, error:'locked'}) for 15 minutes. The
// failure count and lock live in memory, so restarting the mock clears them.
const http = require('node:http');
const crypto = require('node:crypto');
const R = require('./rules.js');

const settings = {guestsPerSlot: 20, daysAhead: 30, cutoffMinutes: 120, maxParty: 8, pin: '111111', phone: '905-640-3633',
  hours: {0: {first: '17:00', last: '20:30'}, 1: null, 2: {first: '17:00', last: '20:30'}, 3: {first: '17:00', last: '20:30'},
          4: {first: '17:00', last: '20:30'}, 5: {first: '17:00', last: '20:30'}, 6: {first: '17:00', last: '20:30'}}};
const members = [{number: '1234', last: 'Test'}];
const bookings = [], blocks = [], events = [];
const seen = new Map();
const PIN_MIN_LENGTH = 6, PIN_MAX_FAILS = 10, PIN_FAIL_MS = 10 * 60 * 1000, PIN_LOCK_MS = 15 * 60 * 1000;
let pinFails = 0, pinFailUntil = 0, pinLockUntil = 0;

// '' when the PIN is fine, else the error code. Mirrors checkPin in Code.gs.
function checkPin(b) {
  const now = Date.now();
  if (now < pinLockUntil) return 'locked';
  if (settings.pin.length >= PIN_MIN_LENGTH && String(b.pin) === settings.pin) { pinFails = 0; return ''; }
  if (now >= pinFailUntil) pinFails = 0;
  pinFails++;
  pinFailUntil = now + PIN_FAIL_MS;
  if (pinFails >= PIN_MAX_FAILS) pinLockUntil = now + PIN_LOCK_MS;
  return 'pin';
}
let nextId = 1;

function today() { return new Date().toLocaleDateString('en-CA', {timeZone: 'America/Toronto'}); }
function nowMinutes() {
  const p = new Date().toLocaleTimeString('en-GB', {timeZone: 'America/Toronto', hour12: false}).split(':');
  return Number(p[0]) * 60 + Number(p[1]);
}
function times(date, guests) {
  return R.openTimes({date, guests, settings, bookings, blocks, events, today: today(), nowMinutes: nowMinutes()});
}
const STAFF = ['day', 'add', 'block', 'unblock', 'status', 'staffCancel'];
const STATUSES = ['Booked', 'Seated', 'No-show'];
const MAX_BODY = 20 * 1024;

function isDate(d) {
  if (typeof d !== 'string' || !/^\d{4}-\d{2}-\d{2}$/.test(d)) return false;
  const t = new Date(d + 'T12:00:00Z');
  return !isNaN(t) && t.toISOString().slice(0, 10) === d;
}
function isTime(t) { return typeof t === 'string' && /^([01]\d|2[0-3]):[0-5]\d$/.test(t); }

function handle(q, b) {
  if (q.action === 'days') {
    const from = q.from === undefined || q.from === '' ? today() : q.from;
    if (!isDate(from)) return {ok: false, error: 'date'};
    const count = Math.min(31, Math.max(1, Math.floor(Number(q.count)) || 14));
    return {ok: true, days: R.days({from, count, settings, events, today: today()})};
  }
  if (q.action === 'times') {
    if (!isDate(q.date)) return {ok: false, error: 'date'};
    const r = times(q.date, Number(q.guests) || 2);
    return {ok: true, ...r, maxParty: settings.maxParty, phone: settings.phone};
  }
  if (!b || typeof b !== 'object') return {ok: false, error: 'action'};
  // Staff calls need the PIN before anything else, so a replayed rid can never
  // hand a cached staff answer to someone without it.
  if (STAFF.includes(b.action)) { const pinErr = checkPin(b); if (pinErr) return {ok: false, error: pinErr}; }
  const key = b.rid ? b.action + ':' + b.rid : '';
  if (key && seen.has(key)) return seen.get(key);
  let out;
  if (b.action === 'book') {
    let err = isDate(b.date) ? R.checkBooking(b, settings) : 'date';
    if (!err && typeof b.time !== 'string') err = 'time';
    if (err) out = {ok: false, rid: b.rid, error: err};
    else {
      // Same order as book() in Code.gs: closed, time, full, and the member check last.
      const t = times(b.date, Number(b.guests));
      const slot = t.times.find(x => x.time === b.time);
      if (t.status !== 'open') out = {ok: false, rid: b.rid, error: 'closed'};
      else if (!R.slotTimes(settings, R.weekdayOf(b.date)).includes(b.time)) out = {ok: false, rid: b.rid, error: 'time'};
      else if (!slot || !slot.open) out = {ok: false, rid: b.rid, error: 'full'};
      else if (!R.isMember(members, b.member, b.name)) out = {ok: false, rid: b.rid, error: 'member'};
      else {
        const row = {id: 'R' + nextId++, date: b.date, time: b.time, guests: Number(b.guests), name: R.clean(b.name, 80),
          phone: R.clean(b.phone, 30), notes: R.clean(b.notes, 300), status: 'Booked', source: 'Website', token: crypto.randomUUID()};
        bookings.push(row);
        console.log('BOOKED', row.id, row.date, row.time, row.guests, row.name, 'cancel token', row.token);
        out = {ok: true, rid: b.rid, booking: {date: row.date, time: row.time, guests: row.guests, name: row.name}};
      }
    }
  } else if (b.action === 'cancel') {
    const row = b.token ? bookings.find(x => x.token && x.token === b.token && x.status === 'Booked') : null;
    if (!row) out = {ok: false, rid: b.rid, error: 'token'};
    else { row.status = 'Cancelled'; out = {ok: true, rid: b.rid, booking: {date: row.date, time: row.time, guests: row.guests, name: row.name}}; }
  } else if (b.action === 'day') {
    const st = R.staffStatus(b.date, settings, events);  // hours and Events only, no booking window
    const list = bookings.filter(x => x.date === b.date && x.status !== 'Cancelled').sort((x, y) => x.time.localeCompare(y.time));
    out = {ok: true, date: b.date, status: st.open ? 'open' : 'closed', reason: st.reason,
      totalGuests: list.filter(x => x.status !== 'No-show').reduce((s, x) => s + x.guests, 0),
      bookings: list.map(({token, date, ...x}) => x),
      blocks: blocks.filter(x => x.date === b.date).map(x => ({id: x.id, from: x.from, to: x.to, reason: x.reason}))};
  } else if (b.action === 'add') {
    const g = Number(b.guests);
    if (!isDate(b.date) || !isTime(b.time) || !(g >= 1) || Math.floor(g) !== g || !String(b.name == null ? '' : b.name).trim())
      out = {ok: false, rid: b.rid, error: 'invalid'};
    else {
      const row = {id: 'R' + nextId++, date: b.date, time: b.time, guests: g, name: R.clean(b.name, 80),
        phone: R.clean(b.phone, 30), notes: R.clean(b.notes, 300), status: 'Booked', source: 'Phone', token: null};
      bookings.push(row); out = {ok: true, rid: b.rid, id: row.id};
    }
  } else if (b.action === 'block') {
    if (!isDate(b.date) || !isTime(b.from) || !isTime(b.to) || !(b.from < b.to)) out = {ok: false, rid: b.rid, error: 'invalid'};
    else {
      const row = {id: 'B' + nextId++, date: b.date, from: b.from, to: b.to, reason: R.clean(b.reason, 120)};
      blocks.push(row); out = {ok: true, rid: b.rid, id: row.id};
    }
  } else if (b.action === 'unblock') {
    const i = blocks.findIndex(x => x.id === b.id);
    if (i < 0) out = {ok: false, error: 'id'};
    else { blocks.splice(i, 1); out = {ok: true}; }
  } else if (b.action === 'status' || b.action === 'staffCancel') {
    if (b.action === 'status' && !STATUSES.includes(b.status)) out = {ok: false, error: 'status'};
    else {
      const row = bookings.find(x => x.id === b.id);
      if (!row) out = {ok: false, error: 'id'};
      else { row.status = b.action === 'staffCancel' ? 'Cancelled' : b.status; out = {ok: true}; }
    }
  } else out = {ok: false, error: 'action'};
  if (key) seen.set(key, out);
  return out;
}

http.createServer((req, res) => {
  const url = new URL(req.url, 'http://x');
  const send = o => { res.writeHead(200, {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'}); res.end(JSON.stringify(o)); };
  const run = (q, b) => {
    try { return handle(q, b); } catch (e) { console.error('handler error', e); return {ok: false, error: 'server'}; }
  };
  if (req.method === 'OPTIONS') { res.writeHead(204, {'Access-Control-Allow-Origin': '*', 'Access-Control-Allow-Headers': 'Content-Type'}); return res.end(); }
  if (req.method === 'GET') return send(run(Object.fromEntries(url.searchParams), null));
  let body = '', size = 0, tooBig = false;
  req.setEncoding('utf8');
  req.on('data', c => {
    if (tooBig) return;
    size += Buffer.byteLength(c);
    if (size > MAX_BODY) { tooBig = true; body = ''; return; }
    body += c;
  });
  req.on('end', () => {
    if (tooBig) return send({ok: false, error: 'size'});
    let b; try { b = JSON.parse(body); } catch (e) { return send({ok: false, error: 'json'}); }
    send(run({}, b));
  });
}).listen(Number(process.argv[2]) || 8745, () => console.log('dining mock on', Number(process.argv[2]) || 8745));
