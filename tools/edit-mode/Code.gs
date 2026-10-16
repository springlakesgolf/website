// Website Edits: takes "Suggest an edit" requests from the preview site.
// setup() is first so the editor's Run button defaults to it.

var SHEET_ID = '1Ax7KBAsa37WQ6NEEcjxCgDEn8TI2Aqsf7jOKzSykwLc';

var HEAD = ['ID', 'Submitted', 'Name', 'Page', 'Section', 'Current text', 'Requested change',
            'Photo', 'Status', 'Done on', 'Cullen notes', 'Page link', 'Where (for Cullen)', 'Screen', 'Request id'];
var STATUS = ['New', 'In progress', 'Done', 'Question', 'Not doing'];

function setup() {
  var ss = SpreadsheetApp.openById(SHEET_ID);
  var sh = ss.getSheetByName('Edits') || ss.getSheets()[0].setName('Edits');
  sh.getRange(1, 1, 1, HEAD.length).setValues([HEAD]).setFontWeight('bold')
    .setBackground('#323C60').setFontColor('#ffffff');
  sh.setFrozenRows(1);
  var widths = [60, 130, 80, 150, 180, 300, 340, 90, 100, 90, 240, 200, 200, 80, 110];
  widths.forEach(function (w, i) { sh.setColumnWidth(i + 1, w); });
  sh.getRange('F:G').setWrap(true);
  sh.getRange('K:K').setWrap(true);
  sh.getRange('A:O').setVerticalAlignment('top');
  sh.getRange('B:B').setNumberFormat('mmm d, h:mm am/pm');
  sh.getRange('J:J').setNumberFormat('mmm d');
  sh.getRange(2, 9, sh.getMaxRows() - 1, 1).setDataValidation(
    SpreadsheetApp.newDataValidation().requireValueInList(STATUS, true).build());
  sh.hideColumns(13, 3);
  var props = PropertiesService.getScriptProperties();
  if (!props.getProperty('EDIT_KEY')) props.setProperty('EDIT_KEY', Utilities.getUuid().replace(/-/g, '').slice(0, 12));
  if (!props.getProperty('PHOTO_FOLDER')) props.setProperty('PHOTO_FOLDER', DriveApp.createFolder('Website Edit Photos').getId());
  Logger.log('EDIT_KEY=' + props.getProperty('EDIT_KEY'));
}

function doGet() {
  return json({ ok: true, service: 'website-edits' });
}

function doPost(e) {
  var b;
  try { b = JSON.parse(e.postData.contents); } catch (err) { return json({ ok: false, error: 'bad json' }); }
  var props = PropertiesService.getScriptProperties();
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

// Keeps a typed value from being read as a formula.
function clip(v, n) {
  var s = String(v == null ? '' : v).slice(0, n);
  return /^[=+\-@]/.test(s) ? "'" + s : s;
}

function json(o) {
  return ContentService.createTextOutput(JSON.stringify(o)).setMimeType(ContentService.MimeType.JSON);
}
