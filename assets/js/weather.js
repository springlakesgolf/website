/* Members page: 7-day forecast from Environment and Climate Change Canada.
   City page weather for Markham (on-85), the nearest ECCC site to the club.
   The API allows cross-origin reads; commercial use is fine with attribution. */
(function(){
  var box = document.getElementById('wx-days');
  if (!box) return;
  var URL = 'https://api.weather.gc.ca/collections/citypageweather-realtime/items/on-85?f=json&lang=en';
  var KIND = {sun: [0, 1, 30], part: [2, 3, 4, 5, 22, 31, 32, 33, 34, 35], cloud: [10, 23, 24, 44, 45],
              rain: [6, 11, 12, 13, 28, 36], storm: [9, 19, 39, 41, 42, 46, 47, 48],
              snow: [7, 8, 14, 15, 16, 17, 18, 25, 26, 27, 37, 38, 40]};
  var G = 'fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"';
  var CLOUD = '<path d="M9 19h9a4 4 0 0 0 .5-8 5.5 5.5 0 0 0-10.6 1.6A3.3 3.3 0 0 0 9 19z"/>';
  var SVG = {
    sun: '<circle cx="12" cy="12" r="4.2"/><path d="M12 2.5v2.2M12 19.3v2.2M2.5 12h2.2M19.3 12h2.2M5.3 5.3l1.6 1.6M17.1 17.1l1.6 1.6M5.3 18.7l1.6-1.6M17.1 6.9l1.6-1.6"/>',
    part: '<circle cx="8.5" cy="8.5" r="3.2"/><path d="M8.5 2.6v1.4M2.6 8.5h1.4M4.3 4.3l1 1M12.7 4.3l-1 1"/>' + CLOUD,
    cloud: CLOUD,
    rain: CLOUD.replace('19h', '15.5h').replace('0 0 9 19z', '0 0 9 15.5z') + '<path d="M9 18.5l-1 2.5M13 18.5l-1 2.5M17 18.5l-1 2.5"/>',
    storm: CLOUD.replace('19h', '15.5h').replace('0 0 9 19z', '0 0 9 15.5z') + '<path d="M13 16.5l-2 3h3l-2 3"/>',
    snow: CLOUD.replace('19h', '15.5h').replace('0 0 9 19z', '0 0 9 15.5z') + '<path d="M9 19.5h.01M13 21h.01M17 19.5h.01M11 22.5h.01"/>'
  };
  function kind(code){
    for (var k in KIND) if (KIND[k].indexOf(code) >= 0) return k;
    return 'cloud';
  }
  function en(o){ return o == null ? '' : (typeof o === 'object' ? (o.en != null ? o.en : '') : o); }
  function temp(f, cls){
    var t = ((f.temperatures || {}).temperature || []).filter(function(x){ return en(x['class']) === cls; })[0];
    return t ? en(t.value) : null;
  }
  function esc(s){ return String(s).replace(/[&<>"]/g, function(c){ return {'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;'}[c]; }); }

  fetch(URL).then(function(r){ if (!r.ok) throw 0; return r.json(); }).then(function(d){
    var list = d.properties.forecastGroup.forecasts, days = [], byName = {};
    list.forEach(function(f){
      var name = en(f.period.value), night = / night$/i.test(name), base = name.replace(/ night$/i, '');
      var day = byName[base];
      if (!day) { day = byName[base] = {name: base, label: night ? 'Tonight' : (days.length ? base.slice(0, 3) : 'Today')}; days.push(day); }
      var ab = f.abbreviatedForecast || {}, pop = ab.pop && en(ab.pop.value);
      if (night) { day.low = temp(f, 'low'); if (!day.code && day.code !== 0) { day.code = en(ab.icon && ab.icon.value); day.text = en(ab.textSummary); day.pop = pop; } }
      else { day.high = temp(f, 'high'); day.code = en(ab.icon && ab.icon.value); day.text = en(ab.textSummary); day.pop = pop; }
    });
    box.innerHTML = days.slice(0, 7).map(function(x){
      var k = kind(Number(x.code));
      return '<div class="wx-day"><div class="wx-name">' + esc(x.label) + '</div>'
        + '<svg class="wx-ico" viewBox="0 0 24 24" aria-hidden="true" ' + G + '>' + SVG[k] + '</svg>'
        + '<div class="wx-temp">' + (x.high != null ? '<b>' + esc(x.high) + '&deg;</b>' : '') + (x.low != null ? '<span>' + esc(x.low) + '&deg;</span>' : '') + '</div>'
        + '<div class="wx-text">' + esc(x.text) + (x.pop ? ' <em>' + esc(x.pop) + '%</em>' : '') + '</div></div>';
    }).join('');
    box.setAttribute('aria-busy', 'false');
  }).catch(function(){
    box.innerHTML = '<p class="wx-off">The forecast is not loading right now. See <a href="https://weather.gc.ca/en/location/index.html?coords=43.977,-79.258" target="_blank" rel="noopener">weather.gc.ca</a>.</p>';
    box.setAttribute('aria-busy', 'false');
  });
})();
