const test = require('node:test');
const assert = require('node:assert');
const R = require('./rules.js');

const S = {
  guestsPerSlot: 20, daysAhead: 30, cutoffMinutes: 120, maxParty: 8,
  hours: {0: {first: '17:00', last: '20:30'}, 1: null, 2: {first: '17:00', last: '20:30'},
          3: {first: '17:00', last: '20:30'}, 4: {first: '17:00', last: '20:30'},
          5: {first: '17:00', last: '20:30'}, 6: {first: '17:00', last: '20:30'}}
};
const base = {settings: S, bookings: [], blocks: [], events: [], today: '2027-05-10', nowMinutes: 9 * 60};

test('half hour slots inclusive, closed day empty', () => {
  assert.deepStrictEqual(R.slotTimes(S, 5), ['17:00', '17:30', '18:00', '18:30', '19:00', '19:30', '20:00', '20:30']);
  assert.deepStrictEqual(R.slotTimes(S, 1), []);
});

test('weekday and label', () => {
  assert.strictEqual(R.weekdayOf('2027-05-14'), 5);
  assert.strictEqual(R.label('19:00'), '7:00 pm');
  assert.strictEqual(R.label('12:30'), '12:30 pm');
});

test('capacity fills a time, cancelled and no-show do not count', () => {
  const bookings = [
    {date: '2027-05-14', time: '19:00', guests: 16, status: 'Booked'},
    {date: '2027-05-14', time: '19:00', guests: 6, status: 'Cancelled'},
    {date: '2027-05-14', time: '19:00', guests: 6, status: 'No-show'}];
  const r = R.openTimes({...base, date: '2027-05-14', guests: 4, bookings});
  assert.strictEqual(r.status, 'open');
  assert.deepStrictEqual(r.times.find(t => t.time === '19:00'), {time: '19:00', open: true});
  const r2 = R.openTimes({...base, date: '2027-05-14', guests: 5, bookings});
  assert.strictEqual(r2.times.find(t => t.time === '19:00').open, false);
});

test('blocks close times from <= t < to', () => {
  const blocks = [{date: '2027-05-14', from: '18:00', to: '19:00', reason: 'Ladies League'}];
  const r = R.openTimes({...base, date: '2027-05-14', guests: 2, blocks});
  const open = r.times.filter(t => t.open).map(t => t.time);
  assert.ok(!open.includes('18:00') && !open.includes('18:30'));
  assert.ok(open.includes('17:30') && open.includes('19:00'));
});

test('events close or limit the day', () => {
  const closed = [{date: '2027-05-16', name: 'Member Guest', dining: 'Closed', limit: 0}];
  assert.deepStrictEqual(R.dayStatus('2027-05-16', S, closed, '2027-05-10'), {open: false, reason: 'Member Guest', limit: 0});
  const r = R.openTimes({...base, date: '2027-05-16', guests: 2, events: closed});
  assert.strictEqual(r.status, 'closed');
  assert.strictEqual(r.times.length, 0);
  const limited = [{date: '2027-05-14', name: 'Wedding', dining: 'Limited', limit: 6}];
  const r2 = R.openTimes({...base, date: '2027-05-14', guests: 8, events: limited});
  assert.ok(r2.times.every(t => !t.open));
});

test('several events on one date: closed wins, else smallest limit wins', () => {
  const closedWins = [
    {date: '2027-05-14', name: 'League', dining: 'Limited', limit: 6},
    {date: '2027-05-14', name: 'Wedding', dining: 'Closed', limit: 0}];
  assert.deepStrictEqual(R.dayStatus('2027-05-14', S, closedWins, '2027-05-10'), {open: false, reason: 'Wedding', limit: 0});
  const smallestLimit = [
    {date: '2027-05-14', name: 'A', dining: 'Limited', limit: 10},
    {date: '2027-05-14', name: 'B', dining: 'Limited', limit: 6}];
  assert.deepStrictEqual(R.dayStatus('2027-05-14', S, smallestLimit, '2027-05-10'), {open: true, reason: 'B', limit: 6});
  const openIgnored = [
    {date: '2027-05-14', name: 'Open day', dining: 'Open', limit: 0},
    {date: '2027-05-14', name: 'C', dining: 'Limited', limit: 4}];
  assert.deepStrictEqual(R.dayStatus('2027-05-14', S, openIgnored, '2027-05-10'), {open: true, reason: 'C', limit: 4});
});

test('past, too far ahead, closed weekday, and same day cutoff', () => {
  assert.strictEqual(R.dayStatus('2027-05-09', S, [], '2027-05-10').open, false);
  assert.strictEqual(R.dayStatus('2027-06-20', S, [], '2027-05-10').open, false);
  assert.strictEqual(R.dayStatus('2027-05-17', S, [], '2027-05-10').open, false);
  const today = R.openTimes({...base, date: '2027-05-11', guests: 2, today: '2027-05-12', nowMinutes: 17 * 60});
  assert.strictEqual(today.status, 'closed');
  const sameDay = R.openTimes({...base, date: '2027-05-11', guests: 2, today: '2027-05-11', nowMinutes: 16 * 60 + 30});
  const open = sameDay.times.filter(t => t.open).map(t => t.time);
  assert.deepStrictEqual(open, ['18:30', '19:00', '19:30', '20:00', '20:30']);
});

test('days strip', () => {
  const d = R.days({from: '2027-05-14', count: 4, settings: S, events: [{date: '2027-05-16', name: 'Member Guest', dining: 'Closed', limit: 0}], today: '2027-05-10'});
  assert.deepStrictEqual(d.map(x => [x.date, x.open]), [['2027-05-14', true], ['2027-05-15', true], ['2027-05-16', false], ['2027-05-17', false]]);
  assert.strictEqual(d[2].reason, 'Member Guest');
});

test('member check ignores case, spaces and accents, uses the full name', () => {
  const members = [{number: '1234', last: 'Côté'}];
  assert.strictEqual(R.isMember(members, ' 1234 ', 'Jean cote'), true);
  assert.strictEqual(R.isMember(members, '1234', 'Jean Smith'), false);
  assert.strictEqual(R.isMember(members, '', ''), false);
  assert.strictEqual(R.isMember(members, '1234', ''), false);
  assert.strictEqual(R.isMember(members, '', 'Jean Cote'), false);
  assert.strictEqual(R.isMember([{number: '1234', last: ''}], '1234', 'Jean Cote'), false);
});

test('member check matches a multi-word last name', () => {
  const members = [{number: '77', last: 'Van Der Berg'}];
  assert.strictEqual(R.isMember(members, '77', 'Anna van der Berg'), true);
  assert.strictEqual(R.isMember(members, '77', 'Anna Berg'), false);
});

test('clean blocks formulas and trims length', () => {
  assert.strictEqual(R.clean('=HYPERLINK("x")', 50), "'=HYPERLINK(\"x\")");
  assert.strictEqual(R.clean('  hi  ', 50), 'hi');
  assert.strictEqual(R.clean('abcdef', 3), 'abc');
  assert.strictEqual(R.clean(null, 5), '');
});

test('checkBooking codes', () => {
  const ok = {date: '2027-05-14', time: '19:00', guests: 4, name: 'Jane Doe', member: '1234', email: 'j@x.ca', phone: '905 555 0101'};
  assert.strictEqual(R.checkBooking(ok, S), '');
  assert.strictEqual(R.checkBooking({...ok, guests: 9}, S), 'big');
  assert.strictEqual(R.checkBooking({...ok, guests: 0}, S), 'guests');
  assert.strictEqual(R.checkBooking({...ok, email: 'nope'}, S), 'email');
  assert.strictEqual(R.checkBooking({...ok, time: '7pm'}, S), 'time');
  assert.strictEqual(R.checkBooking({...ok, name: ' '}, S), 'name');
  assert.strictEqual(R.checkBooking({...ok, phone: '12'}, S), 'phone');
});

test('staffStatus: hours and Events only, no booking window', () => {
  const evs = [{date: '2027-05-16', name: 'Member Guest', dining: 'Closed', limit: 0}, {date: '2027-05-14', name: 'Wedding', dining: 'Limited', limit: 6}];
  assert.deepStrictEqual(R.staffStatus('2027-05-01', S, evs), {open: true, reason: ''});    // past, for a "2027-05-10" today
  assert.deepStrictEqual(R.staffStatus('2027-09-01', S, evs), {open: true, reason: ''});    // far beyond daysAhead
  assert.deepStrictEqual(R.staffStatus('2027-05-17', S, evs), {open: false, reason: 'Closed'}); // Monday
  assert.deepStrictEqual(R.staffStatus('2027-05-16', S, evs), {open: false, reason: 'Member Guest'});
  assert.deepStrictEqual(R.staffStatus('2027-05-14', S, evs), {open: true, reason: 'Wedding'});
  // Members still see the window.
  assert.strictEqual(R.dayStatus('2027-05-01', S, evs, '2027-05-10').reason, 'Past');
  assert.strictEqual(R.dayStatus('2027-09-01', S, evs, '2027-05-10').reason, 'Not open for booking yet');
});
