/* Course gallery lightbox. Without JavaScript each tile is a plain link to the full photo. */
(function () {
  var links = [].slice.call(document.querySelectorAll('a[data-gal]'));
  if (!links.length || !window.HTMLDialogElement) return;
  var d = document.createElement('dialog');
  d.className = 'lb';
  d.setAttribute('aria-label', 'Photo viewer');
  var arrow = '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" aria-hidden="true"><path d="M5 12h14M13 6l6 6-6 6"/></svg>';
  d.innerHTML = '<figure class="lb-fig"><img alt=""><figcaption aria-live="polite"><span class="lb-cap"></span><span class="lb-n"></span></figcaption></figure>' +
    '<button type="button" class="lb-x" aria-label="Close"><svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" aria-hidden="true"><path d="M5 5l14 14M19 5L5 19"/></svg></button>' +
    '<button type="button" class="lb-p" aria-label="Previous photo">' + arrow + '</button>' +
    '<button type="button" class="lb-nx" aria-label="Next photo">' + arrow + '</button>';
  document.body.appendChild(d);
  var img = d.querySelector('img'), cap = d.querySelector('.lb-cap'), num = d.querySelector('.lb-n'), i = 0;

  function show(n) {
    i = (n + links.length) % links.length;
    var tile = links[i].querySelector('img'), alt = tile.alt;
    // The tile's width and height give the photo's shape, so the viewer holds its space while the full photo loads.
    ['width', 'height'].forEach(function (k) {
      var v = tile.getAttribute(k);
      if (v) img.setAttribute(k, v); else img.removeAttribute(k);
    });
    img.src = links[i].href; img.alt = alt;
    cap.textContent = alt; num.textContent = (i + 1) + ' of ' + links.length;
    new Image().src = links[(i + 1) % links.length].href;
  }
  links.forEach(function (a, n) {
    a.addEventListener('click', function (e) {
      if (e.metaKey || e.ctrlKey || e.shiftKey) return;
      e.preventDefault(); show(n);
      document.documentElement.style.overflow = 'hidden';
      d.showModal();
    });
  });
  d.querySelector('.lb-x').addEventListener('click', function () { d.close(); });
  d.querySelector('.lb-p').addEventListener('click', function () { show(i - 1); });
  d.querySelector('.lb-nx').addEventListener('click', function () { show(i + 1); });
  d.addEventListener('click', function (e) { if (e.target === d || e.target.classList.contains('lb-fig')) d.close(); });
  d.addEventListener('keydown', function (e) {
    if (e.key === 'ArrowLeft') show(i - 1);
    if (e.key === 'ArrowRight') show(i + 1);
  });
  d.addEventListener('close', function () {
    document.documentElement.style.overflow = '';
    img.removeAttribute('src');
    links[i].focus();
  });
  var x0 = null;
  d.addEventListener('touchstart', function (e) { x0 = e.touches[0].clientX; }, { passive: true });
  d.addEventListener('touchend', function (e) {
    if (x0 === null) return;
    var dx = e.changedTouches[0].clientX - x0; x0 = null;
    if (Math.abs(dx) > 50) show(i + (dx < 0 ? 1 : -1));
  });
})();
