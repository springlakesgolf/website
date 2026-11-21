/* Junior Academy application form on /junior-golf/academy/. Posts to the Apps Script in
   tools/forms/academy.gs, which writes the "Junior Academy Applications" sheet. The build marks
   the form data-open="1" only when tools/forms/academy.json has an exec address and open: true;
   the sheet's "Accepting applications" setting can still close it (checked on load and on send).
   The hidden "website" field is a honeypot. */
(function(){
  var f = document.getElementById('academy-form');
  if (!f || f.getAttribute('data-open') !== '1') return;
  var exec = f.getAttribute('data-exec');
  var note = f.querySelector('.form-note'), btn = f.querySelector('button[type=submit]');
  var label = btn.textContent, rid = null;
  var PHONE = 'That did not go through. Please call the pro shop at 905-640-3633.';
  function val(n){ var el = f.elements[n]; return el ? el.value.trim() : ''; }
  function say(msg, bad){ note.style.display = 'block'; note.textContent = msg; note.style.color = bad ? '#a3261d' : ''; }
  function fail(msg, el){ say(msg, true); btn.disabled = false; btn.textContent = label; if (el) el.focus(); }
  function close(msg){
    Array.prototype.forEach.call(f.querySelectorAll('fieldset'), function(set){ set.disabled = true; });
    btn.textContent = 'Applications open in February'; say(msg || 'Applications open in February. Please check back then.');
  }
  function whole(v, lo, hi){ return /^\d{1,2}$/.test(v) && Number(v) >= lo && Number(v) <= hi; }
  // the sheet may have been closed since the page was built
  fetch(exec).then(function(r){ return r.json(); }).then(function(res){ if (res && res.ok && res.open === false) close(); }).catch(function(){});
  f.addEventListener('submit', function(e){
    e.preventDefault();
    var p = {player: val('player'), age: val('age'), years: val('years'), handicap: val('handicap'), tournaments: val('tournaments'),
             parent: val('parent'), email: val('email'), phone: val('phone'), website: val('website')};
    if (!p.player) return fail('Please add the player\'s name.', f.elements.player);
    if (!whole(p.age, 5, 18)) return fail('Please add the player\'s age (5 to 18).', f.elements.age);
    if (!whole(p.years, 0, 17)) return fail('Please add how many years the player has played (0 if new).', f.elements.years);
    if (!p.parent) return fail('Please add a parent or guardian name.', f.elements.parent);
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(p.email)) return fail('Please add a valid parent email address.', f.elements.email);
    if (p.phone.replace(/\D/g, '').length < 10) return fail('Please add a parent phone number with area code.', f.elements.phone);
    // one id per application, so a retry after a dropped reply does not add a second row
    rid = rid || Date.now().toString(36) + Math.random().toString(36).slice(2, 8);
    p.rid = rid;
    btn.disabled = true; btn.textContent = 'Sending';
    fetch(exec, {method: 'POST', body: JSON.stringify(p)})
      .then(function(r){ return r.json(); })
      .then(function(res){
        if (res && res.closed) return close(res.message);
        if (!res || !res.ok) return fail((res && res.message) || PHONE);
        f.reset(); rid = null; btn.disabled = false; btn.textContent = label;
        say('Thank you. The application for ' + p.player.split(' ')[0] + ' is in, and our team will be in touch.');
      })
      .catch(function(){ fail(PHONE); });
  });
})();
