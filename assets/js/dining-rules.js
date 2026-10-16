// Booking rules for restaurant reservations. Pure functions only: the same file
// runs in Node tests, the mock server, the browser and Apps Script (pasted in
// by build_gs.py), so it must not touch sheets, the DOM or the clock.
var DiningRules = (function () {
  function pad(n) { return (n < 10 ? '0' : '') + n; }
  function toMin(t) { var p = String(t).split(':'); return Number(p[0]) * 60 + Number(p[1]); }
  function fromMin(m) { return pad(Math.floor(m / 60)) + ':' + pad(m % 60); }
  function addDays(date, n) {
    var d = new Date(date + 'T12:00:00Z'); d.setUTCDate(d.getUTCDate() + n);
    return d.toISOString().slice(0, 10);
  }
  function diffDays(a, b) { return Math.round((new Date(a + 'T12:00:00Z') - new Date(b + 'T12:00:00Z')) / 864e5); }
  function weekdayOf(date) { return new Date(date + 'T12:00:00Z').getUTCDay(); }
  function label(t) {
    var m = toMin(t), h = Math.floor(m / 60), h12 = h % 12 || 12;
    return h12 + ':' + pad(m % 60) + (h < 12 ? ' am' : ' pm');
  }
  function slotTimes(settings, weekday) {
    var h = settings.hours[weekday];
    if (!h) return [];
    var out = [];
    for (var m = toMin(h.first); m <= toMin(h.last); m += 30) out.push(fromMin(m));
    return out;
  }
  function eventsOn(events, date) {
    return events.filter(function (e) { return e.date === date && e.dining !== 'Open'; });
  }
  // Weekday hours and Events only, with no booking window. What staff see for any day.
  function hoursStatus(date, settings, events) {
    if (!slotTimes(settings, weekdayOf(date)).length) return {open: false, reason: 'Closed', limit: 0};
    var evs = eventsOn(events, date), closed = null, best = null, bestLimit = 0, i;
    for (i = 0; i < evs.length; i++) if (evs[i].dining === 'Closed') { closed = evs[i]; break; }
    if (closed) return {open: false, reason: closed.name, limit: 0};
    for (i = 0; i < evs.length; i++) {
      var lim = Number(evs[i].limit) || 0;
      if (best === null || lim < bestLimit) { best = evs[i]; bestLimit = lim; }
    }
    if (best) return {open: true, reason: best.name, limit: bestLimit};
    return {open: true, reason: '', limit: settings.guestsPerSlot};
  }
  // What members can book: hours and Events, inside the booking window.
  function dayStatus(date, settings, events, today) {
    var ahead = diffDays(date, today);
    if (ahead < 0) return {open: false, reason: 'Past', limit: 0};
    if (ahead > settings.daysAhead) return {open: false, reason: 'Not open for booking yet', limit: 0};
    return hoursStatus(date, settings, events);
  }
  // What the staff book shows: past days and days beyond the member window show normally.
  function staffStatus(date, settings, events) {
    var st = hoursStatus(date, settings, events);
    return {open: st.open, reason: st.reason};
  }
  function counted(b) { return b.status === 'Booked' || b.status === 'Seated'; }
  function openTimes(o) {
    var st = dayStatus(o.date, o.settings, o.events, o.today);
    if (!st.open) return {status: 'closed', reason: st.reason, times: []};
    var used = {};
    o.bookings.forEach(function (b) { if (b.date === o.date && counted(b)) used[b.time] = (used[b.time] || 0) + Number(b.guests); });
    var blocks = o.blocks.filter(function (b) { return b.date === o.date; });
    var sameDay = o.date === o.today;
    var times = slotTimes(o.settings, weekdayOf(o.date)).map(function (t) {
      var m = toMin(t), open = (used[t] || 0) + Number(o.guests) <= st.limit;
      if (sameDay && m - o.nowMinutes < o.settings.cutoffMinutes) open = false;
      blocks.forEach(function (b) { if (m >= toMin(b.from) && m < toMin(b.to)) open = false; });
      return {time: t, open: open};
    });
    return {status: 'open', reason: st.reason, times: times};
  }
  function days(o) {
    var out = [];
    for (var i = 0; i < o.count; i++) {
      var d = addDays(o.from, i), st = dayStatus(d, o.settings, o.events, o.today);
      out.push({date: d, open: st.open, reason: st.reason});
    }
    return out;
  }
  function fold(s) {
    return String(s == null ? '' : s).normalize('NFD').replace(/[\u0300-\u036f]/g, '').replace(/\s+/g, '').toLowerCase();
  }
  function isMember(members, number, fullName) {
    var n = fold(number), f = fold(fullName);
    if (!n || !f) return false;
    return members.some(function (m) {
      var l = fold(m.last);
      return !!l && fold(m.number) === n && f.length >= l.length && f.slice(f.length - l.length) === l;
    });
  }
  function clean(v, max) {
    var s = String(v == null ? '' : v).trim().slice(0, max);
    return /^[=+\-@]/.test(s) ? "'" + s : s;
  }
  function checkBooking(b, settings) {
    if (!/^\d{4}-\d{2}-\d{2}$/.test(b.date || '')) return 'date';
    if (!/^\d{2}:\d{2}$/.test(b.time || '')) return 'time';
    var g = Number(b.guests);
    if (!(g >= 1) || Math.floor(g) !== g) return 'guests';
    if (g > settings.maxParty) return 'big';
    if (!String(b.name || '').trim()) return 'name';
    if (!String(b.member || '').trim()) return 'member';
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(String(b.email || '').trim())) return 'email';
    if (String(b.phone || '').replace(/\D/g, '').length < 7) return 'phone';
    return '';
  }
  return {slotTimes: slotTimes, dayStatus: dayStatus, staffStatus: staffStatus, openTimes: openTimes, days: days, isMember: isMember,
          clean: clean, checkBooking: checkBooking, label: label, weekdayOf: weekdayOf, addDays: addDays};
})();
if (typeof module !== 'undefined') module.exports = DiningRules;
