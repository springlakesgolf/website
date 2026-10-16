/* Staff "Suggest an edit" mode for the preview site.
   Off unless the page was opened with ?edit=<key>; the key is then remembered
   in this browser and sent with every request, and the Apps Script rejects
   anything without it. Requests land in the "Website Edits" sheet. */
(function(){
  var EXEC = 'https://script.google.com/macros/s/AKfycbyTjwerucMteyTyt4WPRKKzXWuCIFcmiXeS5amN1iTK9phCn8MmBQYxaWwTmk8IS0dAtQ/exec';
  var NAMES = ['Braeden', 'Laura', 'Cullen'];
  var PICKABLE = 'h1,h2,h3,h4,p,li,img,figure,blockquote,.btn,a.tee-link,label,td,th,.eyebrow,.lead-text,iframe,form';
  var store = {
    get: function(k){ try { return localStorage.getItem(k) } catch(e){ return null } },
    set: function(k, v){ try { v == null ? localStorage.removeItem(k) : localStorage.setItem(k, v) } catch(e){} }
  };
  var qs = new URLSearchParams(location.search);
  if (qs.has('edit')) {
    var k = qs.get('edit');
    store.set('slg-edit-key', k && k !== 'off' ? k : null);
    qs.delete('edit');
    history.replaceState(null, '', location.pathname + (qs.toString() ? '?' + qs : '') + location.hash);
  }
  var KEY = store.get('slg-edit-key');
  if (!KEY) return;

  var css = ''
    + '.sle-fab{position:fixed;right:16px;bottom:16px;z-index:10000;font:600 12px/1 Montserrat,sans-serif;letter-spacing:.12em;text-transform:uppercase;'
    + 'background:#323C60;color:#fff;border:0;border-radius:4px;padding:14px 18px;box-shadow:0 6px 22px rgba(38,46,76,.3);cursor:pointer}'
    + '.sle-fab:focus-visible,.sle-box button:focus-visible{outline:3px solid #cdb155;outline-offset:2px}'
    + '.sle-bar{position:fixed;left:0;right:0;top:0;z-index:10001;background:#B89A2D;color:#323C60;font:600 14px/1.4 Montserrat,sans-serif;'
    + 'padding:14px 16px;display:flex;gap:12px;align-items:center;justify-content:center;flex-wrap:wrap;text-align:center;box-shadow:0 4px 16px rgba(0,0,0,.2)}'
    + '.sle-bar button{font:600 12px/1 Montserrat,sans-serif;letter-spacing:.08em;text-transform:uppercase;border:1px solid #323C60;background:transparent;color:#323C60;padding:9px 12px;border-radius:4px;cursor:pointer}'
    + '.sle-picking,.sle-picking *{cursor:crosshair!important}'
    + '.sle-hover{outline:3px solid #B89A2D!important;outline-offset:3px;background-color:rgba(184,154,45,.10)!important}'
    + '.sle-chosen{outline:3px solid #323C60!important;outline-offset:3px}'
    + '.sle-veil{position:fixed;inset:0;z-index:10002;background:rgba(34,38,57,.55);display:flex;align-items:flex-end;justify-content:center;padding:16px}'
    + '@media(min-width:700px){.sle-veil{align-items:center}}'
    + '.sle-box{background:#fff;color:#222639;width:100%;max-width:520px;max-height:calc(100vh - 32px);overflow:auto;border-radius:6px;padding:22px;font:400 15px/1.5 Montserrat,sans-serif;box-shadow:0 18px 50px rgba(38,46,76,.35)}'
    + '.sle-box h3{font:600 26px/1.1 Cormorant,Georgia,serif;color:#323C60;margin:0 0 12px}'
    + '.sle-box label{display:block;font-weight:600;font-size:12px;letter-spacing:.08em;text-transform:uppercase;color:#323C60;margin:14px 0 6px}'
    + '.sle-box select,.sle-box textarea,.sle-box input[type=file]{width:100%;font:inherit;border:1px solid #e3ded1;border-radius:4px;padding:10px;background:#fff;color:#222639}'
    + '.sle-box textarea{min-height:120px;resize:vertical}'
    + '.sle-quote{background:#f7f5ef;border-left:3px solid #B89A2D;padding:10px 12px;font-size:13px;color:#5b6178;max-height:110px;overflow:auto;white-space:pre-wrap}'
    + '.sle-row{display:flex;gap:10px;justify-content:flex-end;margin-top:18px;flex-wrap:wrap}'
    + '.sle-row button{font:600 12px/1 Montserrat,sans-serif;letter-spacing:.1em;text-transform:uppercase;border-radius:4px;padding:13px 18px;cursor:pointer;border:1px solid #323C60}'
    + '.sle-send{background:#B89A2D;color:#323C60;border-color:#B89A2D!important}.sle-send[disabled]{opacity:.6;cursor:wait}'
    + '.sle-cancel{background:#fff;color:#323C60}'
    + '.sle-msg{margin-top:12px;font-size:14px}.sle-msg.err{color:#a3261d}.sle-msg.ok{color:#2c6b3f}'
    + '.sle-hint{font-size:13px;color:#5b6178;margin:4px 0 0}';
  var st = document.createElement('style'); st.textContent = css; document.head.appendChild(st);

  var fab = el('button', {className: 'sle-fab', type: 'button'}, 'Suggest an edit');
  document.body.appendChild(fab);
  var bar = null, hovered = null, chosen = null;

  fab.addEventListener('click', startPicking);

  function startPicking(){
    fab.style.display = 'none';
    document.documentElement.classList.add('sle-picking');
    bar = el('div', {className: 'sle-bar'});
    bar.appendChild(el('span', {}, 'Tap the part of the page you want changed.'));
    var general = el('button', {type: 'button'}, 'General note for this page');
    var cancel = el('button', {type: 'button'}, 'Cancel');
    general.addEventListener('click', function(e){ e.stopPropagation(); stopPicking(); openForm(null); });
    cancel.addEventListener('click', function(e){ e.stopPropagation(); stopPicking(); fab.style.display = ''; });
    bar.appendChild(general); bar.appendChild(cancel);
    document.body.appendChild(bar);
    // a hover highlight on a touch screen eats the first tap (iOS treats it as hover), so only mice get it
    if (window.matchMedia && matchMedia('(hover: hover)').matches) document.addEventListener('mouseover', onOver, true);
    document.addEventListener('click', onPick, true);
    document.addEventListener('keydown', onKey, true);
  }
  function stopPicking(){
    document.documentElement.classList.remove('sle-picking');
    if (hovered) hovered.classList.remove('sle-hover');
    hovered = null;
    if (bar) bar.remove();
    bar = null;
    document.removeEventListener('mouseover', onOver, true);
    document.removeEventListener('click', onPick, true);
    document.removeEventListener('keydown', onKey, true);
  }
  function target(node){
    if (!node || !node.closest || node.closest('.sle-bar,.sle-fab,.sle-veil')) return null;
    return node.closest(PICKABLE) || node.closest('section,header,footer') || null;
  }
  function onOver(e){
    var t = target(e.target);
    if (t === hovered) return;
    if (hovered) hovered.classList.remove('sle-hover');
    hovered = t;
    if (t) t.classList.add('sle-hover');
  }
  function onPick(e){
    if (e.target.closest && e.target.closest('.sle-bar')) return;
    var t = target(e.target);
    if (!t) return;
    e.preventDefault(); e.stopPropagation();
    stopPicking();
    openForm(t);
  }
  function onKey(e){ if (e.key === 'Escape'){ stopPicking(); fab.style.display = ''; } }

  function describe(t){
    if (!t) return {section: sectionName(document.querySelector('main') || document.body), current: '(General note for the whole page)', where: ''};
    var current;
    if (t.tagName === 'IMG') current = 'Photo: ' + (t.getAttribute('alt') || '(no description)') + ' [' + (t.getAttribute('src') || '').split('/').pop() + ']';
    else if (t.tagName === 'IFRAME') current = 'Embedded: ' + (t.getAttribute('title') || t.getAttribute('src') || 'frame');
    else {
      current = (t.innerText || '').replace(/\s+\n/g, '\n').replace(/[ \t]+/g, ' ').trim();
      var img = t.querySelector && t.querySelector('img');
      if (!current && img) current = 'Photo: ' + (img.getAttribute('alt') || '') + ' [' + (img.getAttribute('src') || '').split('/').pop() + ']';
    }
    return {section: sectionName(t), current: (current || '(no text)').slice(0, 1500), where: cssPath(t)};
  }
  function sectionName(t){
    var s = t.closest('section,header,footer') || t;
    var h = s.querySelector('h1,h2,h3');
    if (s.tagName === 'HEADER') return 'Top menu';
    if (s.tagName === 'FOOTER') return 'Footer';
    var label = h ? h.innerText.replace(/\s+/g, ' ').trim() : '';
    if (!label && s.previousElementSibling) { var ph = s.previousElementSibling.querySelector('h1,h2,h3'); if (ph) label = ph.innerText.trim(); }
    return label ? label.slice(0, 120) : 'Section ' + (Array.prototype.indexOf.call(document.querySelectorAll('section'), s) + 1);
  }
  function cssPath(t){
    var parts = [];
    while (t && t.nodeType === 1 && t !== document.body && parts.length < 8) {
      var p = t.tagName.toLowerCase();
      if (t.id) { parts.unshift(p + '#' + t.id); break; }
      var cls = (t.getAttribute('class') || '').split(/\s+/).filter(function(c){ return c && c.indexOf('sle-') && c !== 'reveal' && c !== 'in' && !/^d\d$/.test(c); });
      if (cls.length) p += '.' + cls.slice(0, 2).join('.');
      var sib = t, n = 1;
      while ((sib = sib.previousElementSibling)) if (sib.tagName === t.tagName) n++;
      if (n > 1) p += ':nth-of-type(' + n + ')';
      parts.unshift(p);
      t = t.parentElement;
    }
    return parts.join(' > ');
  }

  function openForm(t){
    chosen = t;
    if (t) t.classList.add('sle-chosen');
    var info = describe(t);
    var veil = el('div', {className: 'sle-veil'});
    var box = el('form', {className: 'sle-box'});
    box.setAttribute('role', 'dialog'); box.setAttribute('aria-modal', 'true'); box.setAttribute('aria-label', 'Suggest an edit');
    box.appendChild(el('h3', {}, t ? 'Suggest an edit' : 'General note'));
    box.appendChild(el('label', {}, t ? 'You picked' : 'Page'));
    box.appendChild(el('div', {className: 'sle-quote'}, t ? info.current : pageName()));
    box.appendChild(el('label', {htmlFor: 'sle-name'}, 'Your name'));
    var who = el('select', {id: 'sle-name', required: true});
    who.appendChild(el('option', {value: ''}, 'Choose one'));
    NAMES.forEach(function(n){ who.appendChild(el('option', {value: n}, n)); });
    who.value = store.get('slg-edit-name') || '';
    box.appendChild(who);
    box.appendChild(el('label', {htmlFor: 'sle-change'}, 'What should change?'));
    var change = el('textarea', {id: 'sle-change', required: true, placeholder: t ? 'Type the new wording, or describe the change.' : 'Describe what you would like changed on this page.'});
    box.appendChild(change);
    box.appendChild(el('label', {htmlFor: 'sle-photo'}, 'Photo (optional)'));
    var photo = el('input', {id: 'sle-photo', type: 'file', accept: 'image/*'});
    box.appendChild(photo);
    box.appendChild(el('p', {className: 'sle-hint'}, 'Add a photo if you want one swapped in or added.'));
    var msg = el('div', {className: 'sle-msg', role: 'status'});
    box.appendChild(msg);
    var row = el('div', {className: 'sle-row'});
    var cancel = el('button', {type: 'button', className: 'sle-cancel'}, 'Cancel');
    var send = el('button', {type: 'submit', className: 'sle-send'}, 'Send');
    row.appendChild(cancel); row.appendChild(send); box.appendChild(row);
    veil.appendChild(box); document.body.appendChild(veil);
    (who.value ? change : who).focus();

    function close(){ veil.remove(); if (chosen) chosen.classList.remove('sle-chosen'); chosen = null; fab.style.display = ''; document.removeEventListener('keydown', esc, true); }
    function esc(e){ if (e.key === 'Escape' && !send.disabled) close(); }
    document.addEventListener('keydown', esc, true);
    cancel.addEventListener('click', close);
    veil.addEventListener('click', function(e){ if (e.target === veil && !send.disabled) close(); });

    box.addEventListener('submit', function(e){
      e.preventDefault();
      if (!who.value || !change.value.trim()) { msg.className = 'sle-msg err'; msg.textContent = 'Please choose your name and say what should change.'; return; }
      store.set('slg-edit-name', who.value);
      send.disabled = true; cancel.disabled = true; send.textContent = 'Sending';
      msg.className = 'sle-msg'; msg.textContent = '';
      readPhoto(photo.files[0]).then(function(img){
        return post({
          key: KEY, rid: rid(), name: who.value, page: pageName(), url: location.origin + location.pathname,
          section: info.section, current: info.current, where: info.where, change: change.value.trim(),
          photo: img, screen: window.innerWidth + 'x' + window.innerHeight
        });
      }).then(function(r){
        box.innerHTML = '';
        box.appendChild(el('h3', {}, 'Sent, thank you'));
        box.appendChild(el('p', {}, 'Request ' + r.id + ' is in. Cullen will make the change and mark it done.'));
        var row2 = el('div', {className: 'sle-row'});
        var more = el('button', {type: 'button', className: 'sle-send'}, 'Suggest another');
        var done = el('button', {type: 'button', className: 'sle-cancel'}, 'Close');
        more.addEventListener('click', function(){ close(); startPicking(); });
        done.addEventListener('click', close);
        row2.appendChild(done); row2.appendChild(more); box.appendChild(row2);
        more.focus();
      }).catch(function(err){
        send.disabled = false; cancel.disabled = false; send.textContent = 'Send';
        msg.className = 'sle-msg err';
        msg.textContent = err && err.message === 'key'
          ? 'This edit link is not valid any more. Ask Cullen for a new one.'
          : 'That did not go through. Check your connection and press Send again.';
      });
    });
  }

  function pageName(){
    var p = location.pathname.replace(/\/index\.html$/, '/').split('/').filter(Boolean);
    var known = ['golf', 'golf-academy', 'golf-camps', 'memberships', 'members', 'events-spring-lakes', 'food-beverage', 'course-gallery', 'contact-us'];
    var last = p.length ? p[p.length - 1] : '';
    return known.indexOf(last) >= 0 ? '/' + last + '/' : '/';
  }
  function rid(){ return Date.now().toString(36) + Math.random().toString(36).slice(2, 8); }

  // Google's /exec redirect drops a reply now and then, so retry with the same
  // request id; the script answers a repeat id without adding a second row.
  function post(body){
    var data = JSON.stringify(body), tries = 0;
    function once(){
      tries++;
      var ctl = window.AbortController ? new AbortController() : null;
      var timer = setTimeout(function(){ if (ctl) ctl.abort(); }, 30000);
      return fetch(EXEC, {method: 'POST', headers: {'Content-Type': 'text/plain;charset=utf-8'}, body: data, signal: ctl ? ctl.signal : undefined})
        .then(function(r){ return r.json(); })
        .then(function(j){
          clearTimeout(timer);
          if (j && j.error === 'key') throw new Error('key');
          if (!j || !j.ok || j.rid !== body.rid) throw new Error('reply');
          return j;
        })
        .catch(function(err){
          clearTimeout(timer);
          if (err.message === 'key' || tries >= 4) throw err;
          return new Promise(function(res){ setTimeout(res, 1500 * tries); }).then(once);
        });
    }
    return once();
  }

  function readPhoto(file){
    if (!file) return Promise.resolve(null);
    return new Promise(function(resolve, reject){
      var fr = new FileReader();
      fr.onerror = function(){ reject(new Error('photo')); };
      fr.onload = function(){
        var im = new Image();
        im.onerror = function(){ resolve({name: file.name, type: file.type, data: String(fr.result).split(',')[1]}); };
        im.onload = function(){
          var max = 2000, w = im.naturalWidth, h = im.naturalHeight, s = Math.min(1, max / Math.max(w, h));
          var c = document.createElement('canvas'); c.width = Math.round(w * s); c.height = Math.round(h * s);
          c.getContext('2d').drawImage(im, 0, 0, c.width, c.height);
          resolve({name: file.name.replace(/\.[^.]+$/, '') + '.jpg', type: 'image/jpeg', data: c.toDataURL('image/jpeg', 0.88).split(',')[1]});
        };
        im.src = fr.result;
      };
      fr.readAsDataURL(file);
    });
  }

  function el(tag, props, text){
    var n = document.createElement(tag);
    for (var k in props) n[k] = props[k];
    if (text != null) n.textContent = text;
    return n;
  }
})();
