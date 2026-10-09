/**
 * Family Menu – "add a dish" backend (Google Sheet + Apps Script web app).
 * Paste into the Sheet via Extensions > Apps Script, then Deploy > New deployment > Web app
 * (Execute as: Me, Who has access: Anyone).
 *
 * GET  <web app URL>            -> {"ok":true,"rows":[{...}, ...]}   (rows with "hide" filled in are skipped)
 * POST <web app URL> (text/plain JSON body, see FIELDS) -> {"ok":true,"row":{...}}
 * Photos arrive as base64 JPEG (already resized in the browser), are saved to the Drive folder
 * "Family Menu photos" (created on first use), shared "anyone with the link can view", and stored as
 * https://lh3.googleusercontent.com/d/<fileId>=w1200 (the site falls back to drive.google.com/thumbnail if needed).
 */
var SHEET_NAME = 'Dishes';
var FOLDER_NAME = 'Family Menu photos';
var HEADER = ['timestamp', 'id', 'name', 'where', 'section', 'protein', 'recent', 'soup',
              'link', 'ingredients', 'photo', 'photo_id', 'hide'];
var SECTIONS = ['beef', 'pork', 'poultry', 'sea', 'cold', 'soup', 'staple', 'lunch', 'other', 'sweet'];
var PROTEINS = ['', '牛', '猪', '羊', '鸡', '鸭', '鱼', '龙虾/虾', '蟹', '蛤蜊/贝', '豆腐/蛋', '素'];
var MAX_PHOTO_BYTES = 4 * 1024 * 1024;

function sheet_() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sh = ss.getSheetByName(SHEET_NAME) || ss.insertSheet(SHEET_NAME);
  if (sh.getLastRow() === 0) { sh.appendRow(HEADER); sh.setFrozenRows(1); }
  return sh;
}

function json_(obj) {
  return ContentService.createTextOutput(JSON.stringify(obj)).setMimeType(ContentService.MimeType.JSON);
}

function rows_() {
  var sh = sheet_();
  var values = sh.getDataRange().getValues();
  var head = values.shift().map(String);
  return values.map(function (r) {
    var o = {};
    head.forEach(function (h, i) { o[h] = r[i] instanceof Date ? r[i].toISOString() : r[i]; });
    return o;
  }).filter(function (o) { return o.name && !String(o.hide || '').trim(); });
}

function doGet() {
  try { return json_({ ok: true, rows: rows_() }); }
  catch (err) { return json_({ ok: false, error: String(err) }); }
}

function clean_(v, max) { return String(v == null ? '' : v).replace(/[\u0000-\u001f]/g, ' ').trim().slice(0, max); }

function doPost(e) {
  var lock = LockService.getScriptLock();
  try {
    var d = JSON.parse((e && e.postData && e.postData.contents) || '{}');
    if (d.website) return json_({ ok: true, skipped: true });          // honeypot: bots fill hidden fields
    var name = clean_(d.name, 60);
    if (!name) return json_({ ok: false, error: 'name required' });
    var where = d.where === 'todo' ? 'todo' : 'menu';
    var section = SECTIONS.indexOf(d.section) >= 0 ? d.section : (where === 'menu' ? 'other' : '');
    var protein = PROTEINS.indexOf(d.protein) >= 0 ? d.protein : '';
    var link = clean_(d.link, 500);
    if (link && !/^https?:\/\//i.test(link)) link = '';
    var ingredients = clean_(d.ingredients, 500);

    var photo = '', photoId = '';
    if (d.photo) {
      var m = String(d.photo).match(/^data:image\/(jpeg|png|webp);base64,(.+)$/);
      if (!m) return json_({ ok: false, error: 'bad photo' });
      var bytes = Utilities.base64Decode(m[2]);
      if (bytes.length > MAX_PHOTO_BYTES) return json_({ ok: false, error: 'photo too large' });
      var it = DriveApp.getFoldersByName(FOLDER_NAME);
      var folder = it.hasNext() ? it.next() : DriveApp.createFolder(FOLDER_NAME);
      var ext = m[1] === 'jpeg' ? 'jpg' : m[1];
      var file = folder.createFile(Utilities.newBlob(bytes, 'image/' + m[1], name + '-' + Date.now() + '.' + ext));
      file.setSharing(DriveApp.Access.ANYONE_WITH_LINK, DriveApp.Permission.VIEW);
      photoId = file.getId();
      photo = 'https://lh3.googleusercontent.com/d/' + photoId + '=w1200';
    }

    lock.waitLock(20000);
    var row = {
      timestamp: new Date().toISOString(), id: 'g' + Date.now(), name: name, where: where, section: section,
      protein: protein, recent: d.recent ? 'yes' : '', soup: d.soup ? 'yes' : '',
      link: link, ingredients: ingredients, photo: photo, photo_id: photoId, hide: ''
    };
    sheet_().appendRow(HEADER.map(function (h) { return row[h]; }));
    return json_({ ok: true, row: row });
  } catch (err) {
    return json_({ ok: false, error: String(err) });
  } finally {
    try { lock.releaseLock(); } catch (e2) {}
  }
}

/** Optional: run once from the editor (▶ Run) to create the sheet header and approve Drive access up front. */
function setup() {
  sheet_();
  var it = DriveApp.getFoldersByName(FOLDER_NAME);
  if (!it.hasNext()) DriveApp.createFolder(FOLDER_NAME);
}
