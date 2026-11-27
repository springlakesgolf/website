// Club Events rows as content.js draws them from the content feed.
// Run: node --test tools/members/content.test.js
const test = require('node:test');
const assert = require('node:assert');
const { eventsHTML } = require('./content.js');

const row = o => Object.assign({ name: 'Night Golf', date: 'Sat, July 10', course: 'East Course', status: 'Details to come', link: '', photo: '' }, o);

test('each status gets its own pill', () => {
  assert.match(eventsHTML([row({ status: 'Sign-up open' })]), /evh-pill evh-open">Sign-up open</);
  assert.match(eventsHTML([row({ status: 'Opens soon' })]), /evh-pill evh-soon">Opens soon</);
  assert.match(eventsHTML([row()]), /evh-pill evh-later">Details to come</);
  assert.match(eventsHTML([row({ status: 'Confirmed' })]), /evh-later">Details to come</);
});

test('Sign up shows only when sign-up is open and the link is https', () => {
  const link = 'https://www.golfgenius.com/pages/123';
  assert.match(eventsHTML([row({ status: 'Sign-up open', link })]), /<a class="btn btn-navy evh-btn" href="https:\/\/www\.golfgenius\.com\/pages\/123" target="_blank" rel="noopener">Sign up<\/a>/);
  assert.doesNotMatch(eventsHTML([row({ status: 'Opens soon', link })]), /Sign up</);
  assert.doesNotMatch(eventsHTML([row({ status: 'Sign-up open' })]), /Sign up</);
  assert.doesNotMatch(eventsHTML([row({ status: 'Sign-up open', link: 'javascript:alert(1)' })]), /<a /);
  assert.doesNotMatch(eventsHTML([row({ status: 'Sign-up open', link: 'http://plain.example' })]), /<a /);
});

test('blank course and date read "to come"; photo only from https', () => {
  const h = eventsHTML([row({ course: '', date: '' })]);
  assert.match(h, /evh-course">Course to come</);
  assert.match(h, /evh-when">Date to come</);
  assert.doesNotMatch(h, /<img/);
  assert.match(eventsHTML([row({ photo: 'https://example.com/a.jpg' })]), /evh-item has-photo"><img class="evh-photo" src="https:\/\/example\.com\/a\.jpg" width="96" height="64" alt="" loading="lazy">/);
  assert.doesNotMatch(eventsHTML([row({ photo: 'data:image/png;base64,xx' })]), /<img/);
});

test('sheet text is escaped', () => {
  const h = eventsHTML([row({ name: '<script>alert(1)</script>', course: 'Tip & "Tuck"' })]);
  assert.ok(!h.includes('<script>'));
  assert.match(h, /&lt;script&gt;/);
  assert.match(h, /Tip &amp; &quot;Tuck&quot;/);
});

test('an empty list says the calendar is coming', () => {
  assert.equal(eventsHTML([]), '<li class="evh-empty">The 2027 calendar is on its way.</li>');
  assert.equal(eventsHTML(null), '<li class="evh-empty">The 2027 calendar is on its way.</li>');
});
