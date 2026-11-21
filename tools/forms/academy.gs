// Junior Academy applications for the Spring Lakes website (/junior-golf/academy/).
// Standalone Apps Script web app: Deploy, New deployment, Web app, Execute as Me, Who has access Anyone.
// setup() is first so Run defaults to it. It makes its own Google Sheet, "Junior Academy Applications",
// kept apart from the Spring Lakes Website sheet because the rows are about minors.
// tools/forms/academy.test.js checks this file offline; tools/forms/academy_mock.js runs it locally.

function setup() {
  var props = PropertiesService.getScriptProperties();
  var ss = props.getProperty('SHEET_ID') ? SpreadsheetApp.openById(props.getProperty('SHEET_ID')) : null;
  if (!ss) {
    ss = SpreadsheetApp.create(SHEET_NAME);
    props.setProperty('SHEET_ID', ss.getId());
  }
  ss.setSpreadsheetTimeZone('America/Toronto');
  Object.keys(TABS).forEach(function (name, i) {
    var sh = ss.getSheetByName(name) || (i === 0 && ss.getSheets()[0].getLastRow() === 0 ? ss.getSheets()[0].setName(name) : ss.insertSheet(name));
    sh.getRange(1, 1, 1, TABS[name].length).setValues([TABS[name]]).setFontWeight('bold').setBackground('#323C60').setFontColor('#ffffff');
    sh.setFrozenRows(1);
    sh.getRange('A:Z').setNumberFormat('@');
  });
  var st = ss.getSheetByName('Settings');
  if (st.getLastRow() < 2) st.getRange(2, 1, DEFAULTS.length, 2).setValues(DEFAULTS);
  var yesNo = SpreadsheetApp.newDataValidation().requireValueInList(['Yes', 'No'], true).build();
  var mode = SpreadsheetApp.newDataValidation().requireValueInList(['Test', 'Live'], true).build();
  st.getRange(2, 2).setDataValidation(yesNo);
  st.getRange(3, 2).setDataValidation(mode);
  Logger.log('Sheet: ' + ss.getUrl());
}

// ---- constants ------------------------------------------------------------
var SHEET_NAME = 'Junior Academy Applications';
var HEAD = ['Received', 'Request id', 'Player name', 'Age', 'Years playing', 'Handicap', 'Tournaments played',
            'Parent or guardian', 'Parent email', 'Parent phone', 'Status', 'Notes'];
var TABS = {Applications: HEAD, Test: HEAD, Settings: ['Setting', 'Value']};
// Accepting applications stays No until February 2027. Mode Test writes to the Test tab and sends the
// alert, marked [TEST], to the test address only.
var DEFAULTS = [['Accepting applications', 'No'], ['Mode', 'Test'],
                ['Alert email', 'braeden@springlakesgolf.com'], ['Test alert email', 'cullen@springlakesgolf.com']];
var MAX_BODY = 10 * 1024;
var CLOSED = 'Applications open in February. Please check back then, or call the pro shop at 905-640-3633.';

// ---- helpers --------------------------------------------------------------
function book_() {
  var id = PropertiesService.getScriptProperties().getProperty('SHEET_ID');
  if (!id) throw new Error('Run setup() first');
  return SpreadsheetApp.openById(id);
}
function settings_(ss) {
  var m = {}, v = ss.getSheetByName('Settings').getDataRange().getDisplayValues();
  v.slice(1).forEach(function (r) { m[String(r[0]).trim()] = String(r[1]).trim(); });
  return {open: /^yes$/i.test(m['Accepting applications'] || ''), live: /^live$/i.test(m['Mode'] || ''),
          alert: m['Alert email'] || '', testAlert: m['Test alert email'] || ''};
}
function json_(o) { return ContentService.createTextOutput(JSON.stringify(o)).setMimeType(ContentService.MimeType.JSON); }
// a cell that starts with = + - or @ would run as a formula in Sheets
function safe_(v) { v = String(v == null ? '' : v).replace(/[\u0000-\u0008\u000b\u000c\u000e-\u001f]/g, '').trim(); return /^[=+\-@]/.test(v) ? "'" + v : v; }
function stamp_() { return Utilities.formatDate(new Date(), 'America/Toronto', 'yyyy-MM-dd HH:mm'); }
function str_(b, k, max) { return String(b[k] == null ? '' : b[k]).trim().slice(0, max); }

// Checks one application. Returns {app} or {message} for the family to fix.
function check_(b) {
  var a = {player: str_(b, 'player', 80), age: str_(b, 'age', 3), years: str_(b, 'years', 3), handicap: str_(b, 'handicap', 20),
           tournaments: str_(b, 'tournaments', 600), parent: str_(b, 'parent', 80), email: str_(b, 'email', 120), phone: str_(b, 'phone', 30)};
  if (!a.player) return {message: 'Please add the player\'s name.'};
  if (!/^\d{1,2}$/.test(a.age) || Number(a.age) < 5 || Number(a.age) > 18) return {message: 'Please add the player\'s age (5 to 18).'};
  if (!/^\d{1,2}$/.test(a.years) || Number(a.years) > 17) return {message: 'Please add how many years the player has played (0 if new).'};
  if (!a.parent) return {message: 'Please add a parent or guardian name.'};
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(a.email)) return {message: 'Please add a valid parent email address.'};
  if (a.phone.replace(/\D/g, '').length < 10) return {message: 'Please add a parent phone number with area code.'};
  return {app: a};
}

// ---- web app --------------------------------------------------------------
function doGet() {
  try { return json_({ok: true, open: settings_(book_()).open}); }
  catch (e) { console.error(e); return json_({ok: false, open: false}); }
}

function doPost(e) {
  var raw = e && e.postData && e.postData.contents || '';
  if (raw.length > MAX_BODY) return json_({ok: false, message: 'That application is too long. Please shorten it and try again.'});
  var b;
  try { b = JSON.parse(raw); } catch (err) { return json_({ok: false, message: 'That did not go through. Please try again.'}); }
  if (!b || typeof b !== 'object') return json_({ok: false, message: 'That did not go through. Please try again.'});
  if (b.website) return json_({ok: true});  // honeypot: a person never fills it
  var lock = LockService.getScriptLock();
  try { lock.waitLock(20000); } catch (err) { return json_({ok: false, message: 'We are busy right now. Please try again in a minute.'}); }
  try {
    var ss = book_(), s = settings_(ss);
    if (!s.open) return json_({ok: false, closed: true, message: CLOSED});
    var c = check_(b);
    if (c.message) return json_({ok: false, message: c.message});
    var a = c.app, rid = str_(b, 'rid', 40), sh = ss.getSheetByName(s.live ? 'Applications' : 'Test');
    if (rid) {
      var last = sh.getLastRow();
      var ids = last > 1 ? sh.getRange(2, 2, last - 1, 1).getValues() : [];
      for (var i = 0; i < ids.length; i++) if (String(ids[i][0]) === rid) return json_({ok: true, duplicate: true});
    }
    sh.appendRow([stamp_(), rid, a.player, a.age, a.years, a.handicap, a.tournaments, a.parent, a.email, a.phone, 'New', ''].map(safe_));
    alert_(a, s);
    return json_({ok: true});
  } catch (err) {
    console.error(err);
    return json_({ok: false, message: 'That did not go through. Please call the pro shop at 905-640-3633.'});
  } finally {
    lock.releaseLock();
  }
}

function alert_(a, s) {
  var to = s.live ? s.alert : s.testAlert;
  if (!to) return;
  var body = ['A new Junior Academy application came in on the website.', '',
    'Player: ' + a.player, 'Age: ' + a.age, 'Years playing: ' + a.years, 'Handicap: ' + (a.handicap || 'none given'),
    'Tournaments played: ' + (a.tournaments || 'none given'), '',
    'Parent or guardian: ' + a.parent, 'Email: ' + a.email, 'Phone: ' + a.phone, '',
    'It is in the ' + (s.live ? 'Applications' : 'Test') + ' tab of the Junior Academy Applications sheet.'].join('\n');
  try {
    MailApp.sendEmail({to: to, subject: (s.live ? '' : '[TEST] ') + 'Junior Academy application: ' + a.player, body: body, replyTo: a.email});
  } catch (err) { console.error('alert email failed', err); }
}
