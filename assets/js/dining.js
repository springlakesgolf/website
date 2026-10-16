// tools/dining/panel.js
// "Reserve a table" panel on the Dining page (design option A, picked by
// Cullen 2026-10-16): a day strip, guests, open times, then the details.
(function () {
  var root = document.getElementById('reserve');
  if (!root || !window.DiningAPI || !window.DiningRules) return;
  var R = window.DiningRules, API = window.DiningAPI;
  var STRIP = 14;
  var state = {date: '', guests: 2, time: '', maxParty: 8, phone: '905-640-3633', rid: '', closed: ''};
  var WD = ['SUN', 'MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT'];
  var MONTHS = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];

  function el(tag, cls, text) { var n = document.createElement(tag); if (cls) n.className = cls; if (text != null) n.textContent = text; return n; }
  function today() { return new Date().toLocaleDateString('en-CA', {timeZone: 'America/Toronto'}); }
  function longDate(d) {
    var dt = new Date(d + 'T12:00:00Z');
    return ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'][dt.getUTCDay()] + ', ' + MONTHS[dt.getUTCMonth()] + ' ' + dt.getUTCDate();
  }

  var open = el('button', 'btn btn-gold rv-open', 'Reserve a table');
  open.type = 'button'; open.setAttribute('aria-expanded', 'false'); open.setAttribute('aria-controls', 'rv-panel');
  var panel = el('div', 'rv-panel'); panel.id = 'rv-panel'; panel.hidden = true;
  root.innerHTML = '';
  root.appendChild(open); root.appendChild(panel);

  var head = el('div', 'rv-head');
  head.appendChild(el('h3', null, 'Reserve a table'));
  head.appendChild(el('p', 'rv-sub', 'For members and their guests.'));
  var step1 = el('div', 'rv-step'), step2 = el('div', 'rv-step'), done = el('div', 'rv-step');
  step2.hidden = true; done.hidden = true; done.tabIndex = -1; done.setAttribute('role', 'status');
  var msg = el('p', 'rv-msg'); msg.setAttribute('role', 'status');
  panel.appendChild(head); panel.appendChild(step1); panel.appendChild(step2); panel.appendChild(done); panel.appendChild(msg);

  step1.appendChild(el('span', 'rv-lbl', 'Day'));
  var strip = el('div', 'rv-days'); strip.setAttribute('role', 'group'); strip.setAttribute('aria-label', 'Day');
  step1.appendChild(strip);
  step1.appendChild(el('span', 'rv-lbl', 'Guests'));
  var party = el('div', 'rv-party');
  var minus = el('button', null, '−'), plus = el('button', null, '+'), count = el('span');
  count.setAttribute('aria-live', 'polite');
  minus.type = plus.type = 'button'; minus.setAttribute('aria-label', 'Fewer guests'); plus.setAttribute('aria-label', 'More guests');
  party.appendChild(minus); party.appendChild(count); party.appendChild(plus); step1.appendChild(party);
  var big = el('p', 'rv-note'); big.hidden = true; step1.appendChild(big);
  step1.appendChild(el('span', 'rv-lbl', 'Time'));
  var timesBox = el('div', 'rv-times'); timesBox.setAttribute('role', 'group'); timesBox.setAttribute('aria-label', 'Time'); timesBox.tabIndex = -1; step1.appendChild(timesBox);
  var cont = el('button', 'btn btn-gold rv-next', 'Continue'); cont.type = 'button'; cont.disabled = true; step1.appendChild(cont);

  var form = el('form', 'rv-form'); step2.appendChild(form);
  var pick = el('p', 'rv-pick'); form.appendChild(pick);
  function field(name, label, type, auto) {
    var w = el('label', 'rv-field'); w.appendChild(el('span', 'rv-lbl', label));
    var i = el('input'); i.name = name; i.type = type || 'text'; if (auto) i.autocomplete = auto; if (name !== 'notes') i.required = true;
    w.appendChild(i); form.appendChild(w); return i;
  }
  var fName = field('name', 'Full name', 'text', 'name'), fMember = field('member', 'Member number', 'text', 'off'),
      fEmail = field('email', 'Email', 'email', 'email'), fPhone = field('phone', 'Phone', 'tel', 'tel'),
      fNotes = field('notes', 'Notes (optional)', 'text', 'off');
  fNotes.placeholder = 'Allergies, a birthday, the patio';
  var row = el('div', 'rv-row');
  var back = el('button', 'btn btn-ghost-navy', 'Back'); back.type = 'button';
  var confirm = el('button', 'btn btn-gold', 'Confirm reservation'); confirm.type = 'submit';
  row.appendChild(back); row.appendChild(confirm); form.appendChild(row);

  function say(text, bad) { msg.textContent = text || ''; msg.className = 'rv-msg' + (bad ? ' bad' : ''); }
  function setGuests(n) {
    state.guests = Math.max(1, n); count.textContent = state.guests + (state.guests === 1 ? ' guest' : ' guests');
    if (checkBig()) { timesBox.innerHTML = ''; cont.disabled = true; } else if (state.closed) showClosed(); else if (state.date) loadTimes();
  }
  // Closed days stay tappable so the reason is on screen; no times are loaded for them.
  function closedMessage(d) {
    if (d.reason === 'Not open for booking yet') return longDate(d.date) + ' is not open for booking yet.';
    return 'The dining room is closed on ' + longDate(d.date) + (d.reason && d.reason !== 'Closed' ? ' for ' + d.reason : '') + '.';
  }
  function showClosed() { timesBox.innerHTML = ''; timesBox.appendChild(el('span', 'rv-note', state.closed)); cont.disabled = true; }
  function checkBig() {
    var tooBig = state.guests > state.maxParty;
    big.hidden = !tooBig;
    big.textContent = 'For parties larger than ' + state.maxParty + ', please call the clubhouse at ' + state.phone + '.';
    return tooBig;
  }
  function loadDays() {
    say('');
    strip.innerHTML = ''; strip.appendChild(el('span', 'rv-loading', 'Loading days'));
    return API.get({action: 'days', from: today(), count: STRIP}).then(function (r) {
      if (!r.ok) throw new Error('days');
      strip.innerHTML = '';
      r.days.forEach(function (d) {
        var dt = new Date(d.date + 'T12:00:00Z'), b = el('button', 'rv-day' + (d.open ? '' : ' closed'));
        b.type = 'button'; b.setAttribute('aria-pressed', 'false');
        b.setAttribute('aria-label', longDate(d.date) + (d.open ? '' : (d.reason && d.reason !== 'Closed' ? ', closed for ' + d.reason : ', closed')));
        b.title = d.open ? longDate(d.date) : (d.reason === 'Closed' ? 'Dining room closed' : d.reason);
        b.appendChild(el('small', null, WD[dt.getUTCDay()])); b.appendChild(el('b', null, String(dt.getUTCDate())));
        b.addEventListener('click', function () {
          state.date = d.date; state.time = ''; state.closed = d.open ? '' : closedMessage(d);
          Array.prototype.forEach.call(strip.children, function (c) { c.classList.remove('on'); c.setAttribute('aria-pressed', 'false'); });
          b.classList.add('on'); b.setAttribute('aria-pressed', 'true');
          say('');
          if (state.closed) { checkBig(); showClosed(); } else loadTimes();
        });
        strip.appendChild(b);
      });
      var first = strip.querySelector('.rv-day:not(.closed)');
      if (first) first.click(); else timesBox.textContent = 'No days are open for booking right now.';
    }).catch(function () { strip.innerHTML = ''; say('Reservations are not loading right now. Please call the clubhouse at ' + state.phone + '.', true); });
  }
  function loadTimes() {
    if (state.guests > state.maxParty) return;
    var want = state.date + '|' + state.guests;
    say(''); state.time = '';
    timesBox.innerHTML = ''; timesBox.appendChild(el('span', 'rv-loading', 'Checking times')); cont.disabled = true;
    API.get({action: 'times', date: state.date, guests: state.guests}).then(function (r) {
      if (want !== state.date + '|' + state.guests) return;
      if (!r.ok) throw new Error('times');
      state.maxParty = r.maxParty || state.maxParty; state.phone = r.phone || state.phone;
      timesBox.innerHTML = '';
      if (checkBig()) { cont.disabled = true; return; }
      if (r.status !== 'open') { timesBox.appendChild(el('span', 'rv-note', 'The dining room is closed this day' + (r.reason && r.reason !== 'Closed' ? ' for ' + r.reason : '') + '.')); return; }
      if (!r.times.some(function (t) { return t.open; })) { timesBox.appendChild(el('span', 'rv-note', 'This day is fully booked for ' + state.guests + '. Try another day or call the clubhouse.')); return; }
      r.times.forEach(function (t) {
        var b = el('button', 'rv-time' + (t.open ? '' : ' off'), R.label(t.time));
        b.type = 'button'; b.disabled = !t.open; b.setAttribute('aria-pressed', 'false');
        if (!t.open) b.setAttribute('aria-label', R.label(t.time) + ', full');
        b.addEventListener('click', function () {
          state.time = t.time;
          Array.prototype.forEach.call(timesBox.children, function (c) { c.classList.remove('on'); c.setAttribute('aria-pressed', 'false'); });
          b.classList.add('on'); b.setAttribute('aria-pressed', 'true'); cont.disabled = false;
        });
        timesBox.appendChild(b);
      });
    }).catch(function () {
      if (want !== state.date + '|' + state.guests) return;
      timesBox.innerHTML = ''; say('Times are not loading right now. Please try again or call the clubhouse.', true); });
  }
  function summary() { return longDate(state.date) + ', ' + R.label(state.time) + ', party of ' + state.guests; }

  open.addEventListener('click', function () {
    var show = panel.hidden; panel.hidden = !show; open.setAttribute('aria-expanded', String(show));
    if (show && !strip.children.length) { setGuests(2); loadDays(); }
  });
  minus.addEventListener('click', function () { setGuests(state.guests - 1); });
  plus.addEventListener('click', function () { setGuests(state.guests + 1); });
  cont.addEventListener('click', function () {
    pick.textContent = summary(); step1.hidden = true; step2.hidden = false; say(''); state.rid = API.rid(); fName.focus();
  });
  function backToStep1() {
    step2.hidden = true; step1.hidden = false; say('');
    var sel = timesBox.querySelector('.rv-time.on');
    (sel || timesBox).focus();
  }
  back.addEventListener('click', backToStep1);
  form.addEventListener('submit', function (e) {
    e.preventDefault(); confirm.disabled = true; back.disabled = true; confirm.textContent = 'Booking'; say('');
    API.post({action: 'book', rid: state.rid, date: state.date, time: state.time, guests: state.guests,
              name: fName.value, member: fMember.value, email: fEmail.value, phone: fPhone.value, notes: fNotes.value})
    .then(function (r) {
      confirm.disabled = false; back.disabled = false; confirm.textContent = 'Confirm reservation';
      if (r.ok) {
        step1.hidden = true; step2.hidden = true; done.hidden = false; done.innerHTML = '';
        done.appendChild(el('p', 'rv-done', "You're booked: " + summary() + '.'));
        done.appendChild(el('p', 'rv-sub', 'A confirmation is on its way to ' + fEmail.value + '.'));
        done.focus();
        return;
      }
      // The server caches every reply, errors included, by action and request
      // id, so a corrected resubmit needs a new id or it replays this error.
      state.rid = API.rid();
      var m = {member: "We couldn't match that member number and name. Reservations are for members and their guests.",
               full: 'That time just filled up. Please pick another time.', closed: 'That day just closed for booking. Please pick another day.',
               time: 'Please pick one of the listed times.',
               email: 'Please check the email address.', phone: 'Please check the phone number.', name: 'Please enter your full name.',
               big: 'For larger parties, please call the clubhouse at ' + state.phone + '.'}[r.error] || 'Something went wrong. Please try again.';
      say(m, true);
      if (r.error === 'member') {
        var a = el('a', 'rv-link', 'Ask about a social membership'); a.href = '#inquire'; msg.appendChild(document.createTextNode(' ')); msg.appendChild(a);
      }
      if (r.error === 'full' || r.error === 'closed') { backToStep1(); loadTimes(); say(m, true); }
    }).catch(function () {
      confirm.disabled = false; back.disabled = false; confirm.textContent = 'Confirm reservation';
      say("That didn't go through. Check your connection and press Confirm again.", true);
    });
  });
})();
