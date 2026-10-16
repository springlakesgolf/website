/* Hours and Lost & Found from the "Website Content" Google Sheet, through the
   Website Edits Apps Script (?feed=content). Staff change a row in the sheet and
   the site shows it within a minute. The last good copy is kept in this browser
   so the page fills in at once; if nothing loads, the hours block is removed. */
(function(){
  var EXEC = '__EXEC_URL__';
  var hoursBox = document.getElementById('hours-box'), lostBox = document.getElementById('lost-box');
  if (!hoursBox && !lostBox) return;
  var members = hoursBox && hoursBox.getAttribute('data-scope') === 'members';
  var KEY = 'slg-content';

  function esc(s){ return String(s == null ? '' : s).replace(/[&<>"]/g, function(c){ return {'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;'}[c]; }); }
  function cached(){ try { return JSON.parse(localStorage.getItem(KEY)); } catch(e) { return null; } }
  function keep(d){ try { localStorage.setItem(KEY, JSON.stringify(d)); } catch(e) {} }

  function render(d){
    if (hoursBox) {
      var rows = (d.hours || []).filter(function(h){ return members || !h.members; });
      if (!rows.length) return dropHours();
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
  }
  function dropHours(){
    var wrap = document.getElementById('hours-wrap') || hoursBox;
    if (wrap && wrap.parentNode) wrap.parentNode.removeChild(wrap);
    hoursBox = null;
    if (window.slgWeekDrop) window.slgWeekDrop();
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
