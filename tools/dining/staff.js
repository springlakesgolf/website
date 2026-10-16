// Staff reservation book for the restaurant iPad (layout 2, picked 2026-10-16).
// Refreshes every 60 seconds and after every action; keeps the last good copy
// on screen when the connection drops.
(function () {
  var R = window.DiningRules, API = window.DiningAPI, app = document.getElementById('app'), msgBar = document.getElementById('msg');
  var KEY = 'slg-dining-pin', pin = null, mode = 'pin', busy = false, msgTimer = null;
  try { pin = localStorage.getItem(KEY); } catch (e) {}
  function todayStr() { return new Date().toLocaleDateString('en-CA', {timeZone: 'America/Toronto'}); }
  var date = todayStr(), seenToday = date, data = null, lastOk = null, timer = null;
  // dayState describes the day on screen: 'loading', 'ok' or 'failed'. loadFailed is for first open with no data.
  var dayState = 'loading', loadFailed = false;
  var DAYS = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
  var MONTHS = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];
  var MSG = {
    invalid: 'Please check the details and try again.',
    id: 'That booking or block has already changed. The list is refreshed.',
    status: 'That status is not allowed.',
    server: 'The reservation system had a problem. Try again in a moment.'
  };
  var BUSY = 'Still saving the last change. Try again in a moment.';
  var MAXG = 40;
  var LOCKED = 'Too many wrong PINs. Try again in 15 minutes.';
  function esc(s) { return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) { return {'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'}[c]; }); }
  function nice(d) { var x = new Date(d + 'T12:00:00Z'); return DAYS[x.getUTCDay()] + ', ' + MONTHS[x.getUTCMonth()] + ' ' + x.getUTCDate(); }
  function slots() { var out = []; for (var m = 11 * 60; m <= 22 * 60; m += 30) out.push(('0' + Math.floor(m / 60)).slice(-2) + ':' + (m % 60 ? '30' : '00')); return out; }
  function pick(sel, v) { if (sel.querySelector('option[value="' + v + '"]')) sel.value = v; }
  function short(t) { return R.label(t).replace(/ (am|pm)$/, ''); }

  // In-page message bar. iPad web apps saved to the home screen handle alert() poorly.
  function say(text) {
    clearTimeout(msgTimer); msgBar.textContent = text; msgBar.hidden = false;
    msgTimer = setTimeout(function () { msgBar.hidden = true; }, 7000);
  }
  msgBar.addEventListener('click', function () { msgBar.hidden = true; });

  function pinScreen(err) {
    mode = 'pin'; clearInterval(timer); msgBar.hidden = true;
    var old = document.querySelector('.sheet'); if (old) old.remove();
    app.innerHTML = '<form class="pin"><h1>Reservations</h1><input type="password" inputmode="numeric" pattern="[0-9]*" autocomplete="off" aria-label="Staff PIN" placeholder="PIN"><p role="alert">' + esc(err || '') + '</p><button class="sbtn gold" type="submit">Open</button></form>';
    var f = app.querySelector('form'), i = f.querySelector('input'), note = f.querySelector('p'); i.focus();
    f.addEventListener('submit', function (e) {
      e.preventDefault();
      var typed = i.value.trim();
      // Check the shape here so a typo never counts toward the wrong-PIN lockout.
      if (!/^\d{6,}$/.test(typed)) { note.textContent = 'Enter your PIN (6 digits or more).'; return; }
      note.textContent = '';
      API.post({action: 'day', pin: typed, date: date}).then(function (r) {
        if (!r.ok) return pinScreen(r.error === 'locked' ? LOCKED : r.error === 'pin' ? 'That PIN did not work.' : 'Something went wrong. Try again.');
        pin = typed;
        try { localStorage.setItem(KEY, pin); } catch (x) {}
        data = r; lastOk = new Date(); dayState = 'ok'; loadFailed = false; mode = 'book'; render(); start();
      }).catch(function () { pinScreen('Could not connect. Check the Wi-Fi and try again.'); });
    });
  }
  // true when the reply was a PIN problem and the PIN screen is now showing.
  function authFail(r) {
    if (r && !r.ok && r.error === 'locked') { pinScreen(LOCKED); return true; }  // keep any stored PIN
    if (r && !r.ok && r.error === 'pin') {
      pin = null; try { localStorage.removeItem(KEY); } catch (x) {}
      pinScreen('The PIN has changed. Please enter the new one.'); return true;
    }
    return false;
  }
  function loadFailedFor(asked) {
    if (asked !== date) return;  // the date moved on while this was in flight
    dayState = data && dayState === 'ok' ? 'ok' : 'failed';
    loadFailed = !data; render(true);
  }
  function load() {
    var asked = date;
    return API.post({action: 'day', pin: pin, date: asked}).then(function (r) {
      if (authFail(r)) return;
      if (asked !== date) return;  // the date moved on while this was in flight
      if (r.ok) { data = r; lastOk = new Date(); dayState = 'ok'; loadFailed = false; render(); }
      else { say(MSG[r.error] || MSG.server); loadFailedFor(asked); }
    }).catch(function () { loadFailedFor(asked); });
  }
  // The book may have sat open overnight: move "today" forward if it was showing the old today.
  function rollDay() {
    var t = todayStr(); if (t === seenToday) return;
    if (date === seenToday) { date = t; resetDay(); }
    seenToday = t;
  }
  function resetDay() {
    if (data) { data.bookings = []; data.blocks = []; data.totalGuests = 0; data.status = 'open'; data.reason = ''; }
    dayState = 'loading';
  }
  function start() { clearInterval(timer); timer = setInterval(function () { if (mode === 'book') { rollDay(); load(); } }, 60000); }
  // Resolves {ok, message}. quiet: the caller shows the message itself (a sheet keeps it beside what was typed).
  function act(body, quiet) {
    if (busy) { if (!quiet) say(BUSY); return Promise.resolve({ok: false, message: BUSY}); }
    busy = true; body.pin = pin;
    return API.post(body).then(function (r) {
      busy = false;
      if (authFail(r)) return {ok: false, auth: true};
      var res = r.ok ? {ok: true} : {ok: false, message: MSG[r.error] || MSG.server};
      if (!r.ok && !quiet) say(res.message);
      return load().then(function () { return res; });
    }, function () {
      busy = false;
      var res = {ok: false, message: "That didn't save. Check the Wi-Fi and try again."};
      if (!quiet) say(res.message);
      return load().then(function () { return res; });
    });
  }

  function render(stale) {
    if (mode !== 'book') return;
    if (!data) {
      app.innerHTML = loadFailed
        ? '<div class="empty"><p>Could not connect. Check the Wi-Fi.</p><button class="sbtn gold" data-retry>Retry</button></div>'
        : '<p class="empty">Loading</p>';
      return;
    }
    var ok = dayState === 'ok';
    var rows = [];
    data.blocks.forEach(function (b) { rows.push({t: b.from, html: '<tr class="blk"><td class="t">' + esc(short(b.from)) + '</td><td colspan="4" class="r">Blocked ' + esc(R.label(b.from)) + ' to ' + esc(R.label(b.to)) + (b.reason ? ': ' + esc(b.reason) : '') + '</td><td><div class="acts"><button data-unblock="' + esc(b.id) + '">Remove</button></div></td></tr>'}); });
    data.bookings.forEach(function (b) {
      rows.push({t: b.time, html: '<tr class="' + esc(b.status) + '"><td class="t">' + esc(short(b.time)) + '</td><td class="g">' + esc(b.guests) + '</td><td>' + esc(b.name) + '<span class="src">' + esc(b.source) + '</span></td><td class="ph">' + esc(b.phone) + '</td><td class="note">' + esc(b.notes) + '</td>'
        + '<td><div class="acts"><button data-id="' + esc(b.id) + '" data-s="Seated" class="' + (b.status === 'Seated' ? 'on' : '') + '">Seated</button><button data-id="' + esc(b.id) + '" data-s="No-show" class="ns ' + (b.status === 'No-show' ? 'on' : '') + '">No-show</button><button data-cancel="' + esc(b.id) + '" aria-label="Cancel booking">Cancel</button></div></td></tr>'});
    });
    rows.sort(function (a, b) { return a.t < b.t ? -1 : a.t > b.t ? 1 : 0; });
    app.innerHTML = '<div class="top"><button data-nav="-1" aria-label="Previous day">&lsaquo;</button><span class="d">' + esc(nice(date)) + '</span><button data-nav="1" aria-label="Next day">&rsaquo;</button><button data-today>Today</button>'
      + (ok ? '<span class="count"><b>' + esc(data.totalGuests) + '</b> ' + (Number(data.totalGuests) === 1 ? 'guest' : 'guests') + '</span>' : '<span class="count"></span>') + '<button data-block>Block time</button><button class="gold" data-add>Add booking</button></div>'
      + (stale && lastOk ? '<div class="stale">Not updated since ' + esc(lastOk.toLocaleTimeString('en-CA', {hour: 'numeric', minute: '2-digit'}).replace(/\./g, '')) + '. Checking the connection.</div>' : '')
      + (!ok ? '' : data.status === 'closed' ? '<div class="event">Dining room closed' + (data.reason && data.reason !== 'Closed' ? ': ' + esc(data.reason) : '') + '</div>' : data.reason ? '<div class="event">' + esc(data.reason) + '</div>' : '')
      + '<div class="book">' + (!ok ? '<p class="empty">' + (dayState === 'failed' ? 'Could not load this day. Checking the connection.' : 'Loading') + '</p>' : rows.length ? '<table><thead><tr><th>Time</th><th>Guests</th><th>Name</th><th>Phone</th><th>Notes</th><th></th></tr></thead><tbody>' + rows.map(function (r) { return r.html; }).join('') + '</tbody></table>' : '<p class="empty">No bookings yet for this day.</p>') + '</div>';
  }

  // fields is constant markup written in this file (never member text).
  function sheet(title, fields, submit, saveLabel, setup) {
    var wrap = document.createElement('div'); wrap.className = 'sheet';
    var opts = slots().map(function (t) { return '<option value="' + t + '">' + esc(R.label(t)) + '</option>'; }).join('');
    wrap.innerHTML = '<form><h2>' + title + '</h2>' + fields.replace(/__TIMES__/g, opts) + '<p class="err" role="alert" hidden></p><div class="btns"><button type="button" class="sbtn" data-close>Close</button><button class="sbtn gold" type="submit">' + saveLabel + '</button></div></form>';
    document.body.appendChild(wrap);
    var f = wrap.querySelector('form'), err = wrap.querySelector('.err'), save = wrap.querySelector('button[type=submit]');
    function fail(text) { err.textContent = text || ''; err.hidden = !text; }
    wrap.querySelector('[data-close]').addEventListener('click', function () { wrap.remove(); });
    // submit(values, fail) returns false when the values are wrong (it has called fail), or a promise
    // of act()'s result. The sheet stays open, with what was typed, until the save succeeds.
    f.addEventListener('submit', function (e) {
      e.preventDefault();
      if (busy) { fail(BUSY); return; }
      fail('');
      var v = {}; new FormData(f).forEach(function (x, k) { v[k] = x; });
      var res = submit(v, fail);
      if (res === false) return;
      save.disabled = true;
      Promise.resolve(res).then(function (r) {
        if (!r || r.ok || r.auth) { wrap.remove(); return; }
        save.disabled = false; fail(r.message || MSG.server);
      }).catch(function () { save.disabled = false; fail(MSG.server); });
    });
    if (setup) setup(f);
    var first = f.querySelector('input,select'); if (first) first.focus();
  }

  app.addEventListener('click', function (e) {
    var b = e.target.closest('button'); if (!b) return;
    if (b.hasAttribute('data-retry')) { loadFailed = false; render(); load(); }
    else if (b.dataset.nav) { date = R.addDays(date, Number(b.dataset.nav)); resetDay(); render(); load(); }
    else if (b.hasAttribute('data-today')) { date = todayStr(); seenToday = date; resetDay(); render(); load(); }
    else if (b.dataset.id) act({action: 'status', id: b.dataset.id, status: b.classList.contains('on') ? 'Booked' : b.dataset.s});
    else if (b.dataset.cancel) {
      var cid = b.dataset.cancel;
      var bk = (data && data.bookings || []).filter(function (x) { return x.id === cid; })[0];
      var who = bk ? 'Cancel the booking for ' + esc(bk.name) + ', ' + esc(bk.guests) + ' at ' + esc(R.label(bk.time)) + '?' : 'Cancel this booking?';
      sheet('Cancel this booking?', '<p>' + who + '</p><p>The table is released and the booking comes off the list.</p>', function () { return act({action: 'staffCancel', id: cid}, true); }, 'Cancel booking');
      var cb = document.querySelector('.sheet [data-close]'); if (cb) cb.textContent = 'Keep it';
    }
    else if (b.dataset.unblock) act({action: 'unblock', id: b.dataset.unblock});
    else if (b.hasAttribute('data-add')) sheet('Add a booking',
      '<div class="row"><label>Time<select name="time">__TIMES__</select></label><label>Guests<input name="guests" type="number" inputmode="numeric" min="1" max="40" step="1" value="2" required></label></div>'
      + '<label>Name<input name="name" maxlength="80" required></label><label>Phone<input name="phone" type="tel" maxlength="30"></label><label>Notes<input name="notes" maxlength="300"></label>',
      function (v, fail) {
        var g = Number(v.guests);
        if (!(g >= 1) || Math.floor(g) !== g || !String(v.name).trim()) { fail('Enter a name and a whole number of guests.'); return false; }
        if (g > MAXG) { fail('Guests must be ' + MAXG + ' or fewer. For a larger party, call the club.'); return false; }
        return act({action: 'add', date: date, time: v.time, guests: g, name: v.name.trim(), phone: v.phone, notes: v.notes}, true);
      }, 'Save', function (f) { pick(f.elements.time, '17:00'); });
    else if (b.hasAttribute('data-block')) sheet('Block off time',
      '<div class="row"><label>From<select name="from">__TIMES__</select></label><label>To<select name="to">__TIMES__</select></label></div><label>Reason<input name="reason" maxlength="120" placeholder="Event or note for staff"></label>',
      function (v, fail) {
        if (!(v.from < v.to)) { fail('Pick a "To" time later than the "From" time.'); return false; }
        return act({action: 'block', date: date, from: v.from, to: v.to, reason: v.reason}, true);
      }, 'Save', function (f) {
        pick(f.elements.from, '17:00'); pick(f.elements.to, '18:00');
        f.elements.from.addEventListener('change', function () {
          var all = slots(), i = all.indexOf(f.elements.from.value) + 2;  // one hour later, else the last slot
          pick(f.elements.to, all[i < all.length ? i : all.length - 1]);
        });
      });
  });
  document.addEventListener('visibilitychange', function () { if (!document.hidden && pin && mode === 'book') { rollDay(); if (data) render(); load(); } });

  if (pin) { mode = 'book'; load().then(function () { if (mode === 'book') start(); }); } else pinScreen();
})();
