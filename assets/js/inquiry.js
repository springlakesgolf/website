/* Membership inquiry form on /memberships/. Posts to the same Apps Script as
   springlakesgolf.github.io/membership, which writes the "Membership Inquiries"
   sheet (staff edit E7). The hidden "website" field is a honeypot. */
(function(){
  var f = document.getElementById('mem-inquiry');
  if (!f) return;
  var note = f.querySelector('.form-note'), btn = f.querySelector('button[type=submit]');
  var label = btn.textContent;
  function val(n){ var el = f.elements[n]; return el ? el.value.trim() : ''; }
  function say(msg, bad){ note.style.display = 'block'; note.textContent = msg; note.style.color = bad ? '#a3261d' : ''; }
  function fail(msg, el){ say(msg, true); btn.disabled = false; btn.textContent = label; if (el) el.focus(); }
  f.addEventListener('submit', function(e){
    e.preventDefault();
    var p = {name: val('name'), email: val('email'), membership: val('interest'), year: val('year'),
             referral: val('referral'), website: val('website')};
    if (!p.name) return fail('Please add your name.', f.elements.name);
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(p.email)) return fail('Please add a valid email address.', f.elements.email);
    if (!p.membership) return fail('Please choose what you are interested in.', f.elements.interest);
    if (!p.year) return fail('Please choose when you would like to join.', f.elements.year);
    btn.disabled = true; btn.textContent = 'Sending';
    fetch(f.getAttribute('data-exec'), {method: 'POST', body: JSON.stringify(p)})
      .then(function(r){ return r.json(); })
      .then(function(res){
        if (!res || !res.ok) return fail((res && res.message) || 'That did not go through. Please call us at 905-640-3633.');
        f.reset(); btn.disabled = false; btn.textContent = label;
        say('Thank you, ' + p.name.split(' ')[0] + '. Our team will be in touch soon.');
      })
      .catch(function(){ fail('That did not go through. Please call us at 905-640-3633.'); });
  });
})();
