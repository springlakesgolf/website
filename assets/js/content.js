/* Hours, Lost & Found and Club Events from the "Spring Lakes Website" Google Sheet, through the
   Website Edits Apps Script (?feed=content). Staff change a row in the sheet and
   the site shows it within a minute. The last good copy is kept in this browser
   so the page fills in at once; if nothing loads, the hours block is removed and the
   Club Events list keeps the copy baked in at build time (tools/members/events.json). */
(function(){
  function esc(s){ return String(s == null ? '' : s).replace(/[&<>"]/g, function(c){ return {'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;'}[c]; }); }

  // One row per event. build.py bakes the same markup (club_events), and test_events.py checks they match.
  var PILL = {'Sign-up open': 'evh-open', 'Opens soon': 'evh-soon', 'Details to come': 'evh-later'};
  function https(v){ v = String(v == null ? '' : v).trim(); return /^https:\/\/[^\s"'<>]+$/.test(v) ? v : ''; }
  function eventsHTML(list){
    if (!list || !list.length) return '<li class="evh-empty">The 2027 calendar is on its way.</li>';
    return list.map(function(x){
      var status = PILL[x.status] ? x.status : 'Details to come';
      var link = https(x.link), photo = https(x.photo);
      return '<li class="evh-item' + (photo ? ' has-photo' : '') + '">'
        + (photo ? '<img class="evh-photo" src="' + esc(photo) + '" alt="" loading="lazy">' : '')
        + '<div class="evh-when">' + esc(x.date || 'Date to come') + '</div>'
        + '<div class="evh-main"><h3 class="evh-name">' + esc(x.name) + '</h3>'
        + '<div class="evh-course">' + esc(x.course || 'Course to come') + '</div></div>'
        + '<div class="evh-act"><span class="evh-pill ' + PILL[status] + '">' + esc(status) + '</span>'
        + (status === 'Sign-up open' && link ? '<a class="btn btn-navy evh-btn" href="' + esc(link) + '" target="_blank" rel="noopener">Sign up</a>' : '')
        + '</div></li>';
    }).join('');
  }
  if (typeof document === 'undefined') { module.exports = {eventsHTML: eventsHTML}; return; }

  var EXEC = 'https://script.google.com/macros/s/AKfycbyTjwerucMteyTyt4WPRKKzXWuCIFcmiXeS5amN1iTK9phCn8MmBQYxaWwTmk8IS0dAtQ/exec';
  var hoursBox = document.getElementById('hours-box'), lostBox = document.getElementById('lost-box');
  var eventsBox = document.getElementById('events-box');
  if (!hoursBox && !lostBox && !eventsBox) return;
  var members = hoursBox && hoursBox.getAttribute('data-scope') === 'members';
  var KEY = 'slg-content';

  function cached(){ try { return JSON.parse(localStorage.getItem(KEY)); } catch(e) { return null; } }
  function keep(d){ try { localStorage.setItem(KEY, JSON.stringify(d)); } catch(e) {} }

  function render(d){
    if (hoursBox) {
      var rows = (d.hours || []).filter(function(h){ return members || !h.members; });
      if (!rows.length) return dropHours(d);
      hoursBox.innerHTML = rows.map(function(h){
        return '<div class="hr-row"><div><div class="hr-what">' + esc(h.what) + '</div>'
          + (h.note ? '<div class="hr-note">' + esc(h.note) + '</div>' : '') + '</div>'
          + '<div class="hr-time">' + esc(h.hours) + '</div></div>';
      }).join('');
      hoursBox.setAttribute('aria-busy', 'false');
      var wrap = document.getElementById('hours-wrap'); if (wrap) wrap.hidden = false;
    }
    if (lostBox) {
      var items = d.lost || [];
      lostBox.innerHTML = items.length ? items.map(function(x){
        return '<li class="lf-item"><span class="lf-date">' + esc(x.found) + '</span><span class="lf-what">' + esc(x.item)
          + (x.where ? '<span class="lf-where">Found ' + esc(x.where.charAt(0).toLowerCase() + x.where.slice(1)) + '</span>' : '') + '</span>'
          + (x.photo ? '<a class="lf-photo" href="' + esc(x.photo) + '" target="_blank" rel="noopener">Photo</a>' : '') + '</li>';
      }).join('') : '<li class="lf-empty">Nothing has been turned in right now.</li>';
    }
    // a script deployed before the Events tab sends no "events": keep the baked list
    if (eventsBox && Array.isArray(d.events)) eventsBox.innerHTML = eventsHTML(d.events);
  }
  function dropHours(d){
    var wrap = document.getElementById('hours-wrap') || hoursBox;
    if (wrap && wrap.parentNode) wrap.parentNode.removeChild(wrap);
    hoursBox = null;
    if (window.slgWeekDrop) window.slgWeekDrop();
    if (d) render(d);
  }

  var c = cached();
  if (c) render(c);

  // Google's /exec redirect drops a reply now and then, so try a few times
  function load(tries){
    var ctl = window.AbortController ? new AbortController() : null;
    var t = setTimeout(function(){ if (ctl) ctl.abort(); }, 15000);
    return fetch(EXEC + '?feed=content&t=' + Date.now(), {signal: ctl ? ctl.signal : undefined})
      .then(function(r){ return r.json(); })
      .then(function(d){ clearTimeout(t); if (!d || !d.ok) throw 0; return d; })
      .catch(function(e){ clearTimeout(t); if (tries > 1) return new Promise(function(res){ setTimeout(res, 1200); }).then(function(){ return load(tries - 1); }); throw e; });
  }
  load(3).then(function(d){ keep(d); render(d); }).catch(function(){
    if (!c) {
      if (hoursBox) dropHours();
      if (lostBox) lostBox.innerHTML = '<li class="lf-empty">The list is not loading right now. Call the pro shop at 905-640-3633.</li>';
    }
  });
})();
