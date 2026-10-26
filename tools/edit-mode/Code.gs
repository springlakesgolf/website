// Website Edits: takes "Suggest an edit" requests from the preview site.
// setup() is first so the editor's Run button defaults to it.

var SHEET_ID = '1Ax7KBAsa37WQ6NEEcjxCgDEn8TI2Aqsf7jOKzSykwLc';

var HEAD = ['ID', 'Submitted', 'Name', 'Page', 'Section', 'Current text', 'Requested change',
            'Photo', 'Status', 'Done on', 'Cullen notes', 'Page link', 'Where (for Cullen)', 'Screen', 'Request id',
            'PR', 'Claude note'];
// PR open and Needs Cullen are set by the staff-edits GitHub Action (W2)
var STATUS = ['New', 'In progress', 'PR open', 'Needs Cullen', 'Done', 'Question', 'Not doing'];

function setup() {
  var ss = SpreadsheetApp.openById(SHEET_ID);
  ss.setSpreadsheetTimeZone('America/Toronto');
  var sh = ss.getSheetByName('Edits') || ss.getSheets()[0].setName('Edits');
  sh.getRange(1, 1, 1, HEAD.length).setValues([HEAD]).setFontWeight('bold')
    .setBackground('#323C60').setFontColor('#ffffff');
  sh.setFrozenRows(1);
  var widths = [60, 130, 80, 150, 180, 300, 340, 90, 100, 90, 240, 200, 200, 80, 110, 220, 260];
  widths.forEach(function (w, i) { sh.setColumnWidth(i + 1, w); });
  sh.getRange('F:G').setWrap(true);
  sh.getRange('K:K').setWrap(true);
  sh.getRange('Q:Q').setWrap(true);
  sh.getRange('A:Q').setVerticalAlignment('top');
  sh.getRange('B:B').setNumberFormat('mmm d, h:mm am/pm');
  sh.getRange('J:J').setNumberFormat('mmm d');
  sh.getRange(2, 9, sh.getMaxRows() - 1, 1).setDataValidation(
    SpreadsheetApp.newDataValidation().requireValueInList(STATUS, true).build());
  sh.hideColumns(13, 3);
  var props = PropertiesService.getScriptProperties();
  if (!props.getProperty('EDIT_KEY')) props.setProperty('EDIT_KEY', Utilities.getUuid().replace(/-/g, '').slice(0, 12));
  if (!props.getProperty('PHOTO_FOLDER')) props.setProperty('PHOTO_FOLDER', DriveApp.createFolder('Website Edit Photos').getId());
  if (!props.getProperty('BOT_SECRET')) props.setProperty('BOT_SECRET', Utilities.getUuid().replace(/-/g, '') + Utilities.getUuid().replace(/-/g, ''));
  Logger.log('EDIT_KEY=' + props.getProperty('EDIT_KEY'));
  Logger.log('BOT_SECRET (GitHub secret EDITS_BOT_SECRET)=' + props.getProperty('BOT_SECRET'));
}

// Hours and Lost & Found for the site, from the "Website Content" sheet that
// staff edit. Cached a minute so a busy page does not hit the sheet each time.
var CONTENT_ID = '1TecRaoIITgztIyDoQaPuJm9LuXd8E4DYtNxYQyjGWyI';

function doGet(e) {
  if (e && e.parameter && e.parameter.feed === 'content') return json(content());
  return json({ ok: true, service: 'website-edits' });
}

function content() {
  var cache = CacheService.getScriptCache(), hit = cache.get('content');
  if (hit) return JSON.parse(hit);
  var ss = SpreadsheetApp.openById(CONTENT_ID), tz = ss.getSpreadsheetTimeZone();
  var hours = ss.getSheetByName('Hours').getDataRange().getDisplayValues().slice(1)
    .filter(function (r) { return r[1] && r[2] && (r[0] === 'Everyone' || r[0] === 'Members only'); })
    .map(function (r) { return { members: r[0] === 'Members only', what: r[1], hours: r[2], note: r[3] }; });
  var cutoff = Date.now() - 90 * 864e5;
  var lost = ss.getSheetByName('Lost & Found').getDataRange().getValues().slice(1)
    .filter(function (r) { return r[1] && r[4] !== 'Claimed' && (!(r[0] instanceof Date) || r[0].getTime() >= cutoff); })
    .map(function (r) {
      return { found: r[0] instanceof Date ? Utilities.formatDate(r[0], tz, 'MMM d') : String(r[0] || ''),
               item: String(r[1]), where: String(r[2] || ''), photo: /^https:\/\//.test(r[3]) ? String(r[3]) : '' };
    }).reverse();
  var out = { ok: true, hours: hours, lost: lost };
  cache.put('content', JSON.stringify(out), 60);
  return out;
}

function doPost(e) {
  var b;
  try { b = JSON.parse(e.postData.contents); } catch (err) { return json({ ok: false, error: 'bad json' }); }
  var props = PropertiesService.getScriptProperties();
  if (b.bot) return json(bot(b, props.getProperty('BOT_SECRET')));
  if (!b.key || b.key !== props.getProperty('EDIT_KEY')) return json({ ok: false, error: 'key' });
  if (!b.rid || !b.change) return json({ ok: false, error: 'missing' });

  var cache = CacheService.getScriptCache();
  var seen = cache.get('rid:' + b.rid);
  if (seen) return json(JSON.parse(seen));

  var lock = LockService.getScriptLock();
  lock.waitLock(20000);
  try {
    seen = cache.get('rid:' + b.rid);
    if (seen) return json(JSON.parse(seen));
    var sh = SpreadsheetApp.openById(SHEET_ID).getSheetByName('Edits');
    var last = sh.getLastRow();
    if (last > 1) {
      var rids = sh.getRange(2, 15, last - 1, 1).getValues();
      for (var i = 0; i < rids.length; i++) if (rids[i][0] === b.rid) {
        var again = { ok: true, rid: b.rid, id: sh.getRange(i + 2, 1).getValue() };
        cache.put('rid:' + b.rid, JSON.stringify(again), 21600);
        return json(again);
      }
    }
    var id = 'E' + (last < 2 ? 1 : (Number(String(sh.getRange(last, 1).getValue()).replace(/\D/g, '')) || last - 1) + 1);
    var photo = '';
    if (b.photo && b.photo.data) {
      var blob = Utilities.newBlob(Utilities.base64Decode(b.photo.data), b.photo.type || 'image/jpeg', id + ' ' + (b.photo.name || 'photo.jpg'));
      var file = DriveApp.getFolderById(props.getProperty('PHOTO_FOLDER')).createFile(blob);
      photo = '=HYPERLINK("' + file.getUrl() + '","View photo")';
    }
    var row = [id, new Date(), clip(b.name, 40), clip(b.page, 80), clip(b.section, 200), clip(b.current, 1500),
               clip(b.change, 4000), photo, 'New', '', '', clip(b.url, 300), clip(b.where, 400), clip(b.screen, 20), b.rid];
    sh.getRange(last + 1, 1, 1, row.length).setValues([row]);
    var reply = { ok: true, rid: b.rid, id: id };
    cache.put('rid:' + b.rid, JSON.stringify(reply), 21600);
    return json(reply);
  } finally {
    lock.releaseLock();
  }
}

// The staff-edits GitHub Action (W2): "pending" lists New rows with no PR yet,
// "result" writes the PR link or a Needs Cullen note back to one row.
// Guarded by BOT_SECRET, which is also the repo secret EDITS_BOT_SECRET.
var BOT_LIMIT = 5;

function bot(b, secret) {
  if (!secret || !same(String(b.bot), secret)) return { ok: false, error: 'key' };
  var sh = SpreadsheetApp.openById(SHEET_ID).getSheetByName('Edits');
  var last = sh.getLastRow();
  var rows = last < 2 ? [] : sh.getRange(2, 1, last - 1, HEAD.length).getValues();
  if (b.action === 'pending') {
    var out = [];
    for (var i = 0; i < rows.length && out.length < BOT_LIMIT; i++) {
      var r = rows[i];
      if (r[8] !== 'New' || r[15] || !r[0]) continue;
      out.push({ id: String(r[0]), page: String(r[3]), section: String(r[4]), current: String(r[5]),
                 change: String(r[6]), photo: !!r[7], url: String(r[11]), where: String(r[12]) });
    }
    return { ok: true, rows: out };
  }
  if (b.action === 'result') {
    if (['PR open', 'Needs Cullen'].indexOf(b.status) < 0) return { ok: false, error: 'status' };
    if (last < 2) return { ok: false, error: 'no row' };
    if (b.pr && !/^https:\/\/github\.com\/springlakesgolf\/website\/pull\/\d+$/.test(b.pr)) return { ok: false, error: 'pr' };
    var lock = LockService.getScriptLock();
    lock.waitLock(20000);
    try {
      rows = sh.getRange(2, 1, last - 1, HEAD.length).getValues();
      for (var j = 0; j < rows.length; j++) if (String(rows[j][0]) === String(b.id)) {
        // a person changed the row since the Action read it: leave their status alone
        if (rows[j][8] !== 'New') return { ok: false, error: 'not new' };
        sh.getRange(j + 2, 9).setValue(b.status);
        sh.getRange(j + 2, 16, 1, 2).setValues([[b.pr || '', clip(b.note, 1000)]]);
        return { ok: true, id: b.id };
      }
      return { ok: false, error: 'no row' };
    } finally {
      lock.releaseLock();
    }
  }
  return { ok: false, error: 'action' };
}

// Compares every character so the time taken does not hint at the secret.
function same(a, b) {
  var diff = a.length ^ b.length;
  for (var i = 0; i < Math.max(a.length, b.length); i++) diff |= (a.charCodeAt(i) || 0) ^ (b.charCodeAt(i) || 0);
  return diff === 0;
}

// Keeps a typed value from being read as a formula.
function clip(v, n) {
  var s = String(v == null ? '' : v).slice(0, n);
  return /^[=+\-@]/.test(s) ? "'" + s : s;
}

function json(o) {
  return ContentService.createTextOutput(JSON.stringify(o)).setMimeType(ContentService.MimeType.JSON);
}
