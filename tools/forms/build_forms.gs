/**
 * Builds the three Google Forms the website links to (staff edits E6 and E8, 2026-10-16):
 *   1. 2027 Camp Waitlist      open now, each entry emails Braeden
 *   2. 2027 Camp Registration  built closed; open it in December
 *   3. Lost Item Report        open now, each report emails reception
 * Each form gets its own response Sheet in the same Drive.
 *
 * Run once: script.google.com > New project > paste this file > run buildAll.
 * Approve the permissions, then copy the three "live" links from the log into
 * tools/forms/config.json. Running it again makes a second set, so run it once.
 */

var ALERTS = {
  waitlist: 'braeden@springlakesgolf.com',
  registration: 'braeden@springlakesgolf.com',
  lost: 'reception@springlakesgolf.com'
};

var WEEKS = ['Week 1: July 5 to 9', 'Week 2: July 19 to 23', 'Week 3: August 2 to 6', 'Week 4: August 16 to 20'];
var AGES = ['6', '7', '8', '9', '10', '11', '12', '13', '14'];

function buildAll() {
  var out = {
    waitlist: buildWaitlist_(),
    registration: buildRegistration_(),
    lost: buildLost_()
  };
  var ids = {};
  Object.keys(out).forEach(function (k) { ids[out[k].form.getId()] = k; });
  PropertiesService.getScriptProperties().setProperty('forms', JSON.stringify(ids));
  Object.keys(out).forEach(function (k) {
    ScriptApp.newTrigger('notify').forForm(out[k].form).onFormSubmit().create();
    Logger.log('%s live: %s', k, out[k].form.getPublishedUrl());
    Logger.log('%s edit: %s', k, out[k].form.getEditUrl());
    Logger.log('%s responses: %s', k, out[k].sheet.getUrl());
  });
}

function newForm_(title, description, confirmation) {
  var form = FormApp.create(title);
  form.setDescription(description);
  form.setConfirmationMessage(confirmation);
  form.setCollectEmail(false);
  form.setShowLinkToRespondAgain(false);
  try { form.setRequireLogin(false); } catch (e) {}
  var sheet = SpreadsheetApp.create(title + ' (responses)');
  form.setDestination(FormApp.DestinationType.SPREADSHEET, sheet.getId());
  return {form: form, sheet: sheet};
}

function text_(form, title, required, help) {
  var it = form.addTextItem().setTitle(title).setRequired(!!required);
  if (help) it.setHelpText(help);
  return it;
}

function email_(form) {
  text_(form, 'Email', true).setValidation(FormApp.createTextValidation().requireTextIsEmail().build());
}

function contact_(form, who) {
  text_(form, who, true);
  email_(form);
  text_(form, 'Phone', true);
}

function camper_(form) {
  text_(form, 'Camper name', true);
  form.addListItem().setTitle('Camper age next summer').setChoiceValues(AGES).setRequired(true);
  form.addCheckboxItem().setTitle('Which weeks?').setChoiceValues(WEEKS).setRequired(true);
  form.addMultipleChoiceItem().setTitle('Are you a Spring Lakes member family?').setChoiceValues(['Yes', 'No']).setRequired(true);
}

function buildWaitlist_() {
  var f = newForm_('Spring Lakes Summer Camp 2027 Waitlist',
    'Join the list for Spring Lakes Summer Camp 2027, for golfers aged 6 to 14. We will contact you when registration opens in December. ' +
    'One form per camper, please.',
    'Thank you. You are on the 2027 camp list, and our team will be in touch when registration opens.');
  contact_(f.form, 'Parent or guardian name');
  camper_(f.form);
  f.form.addParagraphTextItem().setTitle('Anything we should know?');
  return f;
}

function buildRegistration_() {
  var f = newForm_('Spring Lakes Summer Camp 2027 Registration',
    'Register a camper for Spring Lakes Summer Camp 2027. Ages 6 to 14, 9 am to 4 pm, five days a week. ' +
    'Camp is $599 per camper and includes a golf polo, lunch and a freezie every day. ' +
    'Spots are first come, first served. One form per camper, please.',
    'Thank you. Our team will contact you to arrange payment, and your spot is confirmed once payment is received.');
  contact_(f.form, 'Parent or guardian name');
  camper_(f.form);
  f.form.addListItem().setTitle('Polo size').setChoiceValues(['Youth XS', 'Youth S', 'Youth M', 'Youth L', 'Youth XL', 'Adult S', 'Adult M']).setRequired(true);
  f.form.addMultipleChoiceItem().setTitle('Golf experience').setChoiceValues(['New to golf', 'Some experience', 'Plays regularly']).setRequired(true);
  f.form.addParagraphTextItem().setTitle('Allergies or medical notes').setHelpText('Write "None" if there are none.').setRequired(true);
  text_(f.form, 'Emergency contact name', true, 'Someone other than the parent above, if possible.');
  text_(f.form, 'Emergency contact phone', true);
  f.form.addMultipleChoiceItem().setTitle('May we include your camper in club photos?').setChoiceValues(['Yes', 'No']).setRequired(true);
  f.form.addCheckboxItem().setTitle('Camp fee')
    .setChoiceValues(['I understand camp is $599 per camper, and our team will contact me to arrange payment.']).setRequired(true);
  f.form.addParagraphTextItem().setTitle('Anything we should know?');
  f.form.setAcceptingResponses(false);
  f.form.setCustomClosedFormMessage('Registration for Spring Lakes Summer Camp 2027 opens in December. Join the waitlist to hear first.');
  return f;
}

function buildLost_() {
  var f = newForm_('Spring Lakes Lost Item Report',
    'Lost something at the club? Tell us what it is and where you last had it. Our team checks this list against items turned in to the pro shop and clubhouse, and will call you if it turns up.',
    'Thank you. Our team will contact you if your item is turned in.');
  contact_(f.form, 'Your name');
  text_(f.form, 'What did you lose?', true, 'For example: 7 iron, rangefinder, black jacket.');
  f.form.addParagraphTextItem().setTitle('Description').setHelpText('Brand, colour, any name or markings.').setRequired(true);
  f.form.addMultipleChoiceItem().setTitle('Where?')
    .setChoiceValues(['North Course', 'East Course', 'South Course', 'Practice range', 'Clubhouse or patio', 'Parking lot', 'Not sure']).setRequired(true);
  text_(f.form, 'Hole or area', false);
  f.form.addDateItem().setTitle('Date lost').setRequired(true);
  return f;
}

/** Runs on every submission: emails the answers to that form's alert address. */
function notify(e) {
  var ids = JSON.parse(PropertiesService.getScriptProperties().getProperty('forms') || '{}');
  var key = ids[e.source.getId()];
  if (!key || !ALERTS[key]) return;
  var lines = e.response.getItemResponses().map(function (r) {
    var a = r.getResponse();
    return r.getItem().getTitle() + ': ' + (Array.isArray(a) ? a.join(', ') : a);
  });
  MailApp.sendEmail(ALERTS[key], 'New ' + e.source.getTitle().replace('Spring Lakes ', ''), lines.join('\n') +
    '\n\nAll responses: ' + SpreadsheetApp.openById(e.source.getDestinationId()).getUrl());
}
