// tools/dining/api.js
// Talks to the Dining Apps Script. Google's /exec redirect drops about one
// reply in five, so every call retries with the same request id and the
// script replays the saved answer instead of booking twice.
(function () {
  var EXEC = 'https://script.google.com/macros/s/AKfycbyrxVewvuGqzrvWIlWTQs1E16ngeR6L6QOyE98IPhdx6t1s3YQ4O7e88EW_Php5iwV4/exec';
  // 16 random bytes as hex; the older time plus Math.random id only if crypto is missing.
  function rid() {
    try {
      var c = window.crypto || window.msCrypto;
      if (c && c.getRandomValues) {
        var a = c.getRandomValues(new Uint8Array(16)), h = '';
        for (var i = 0; i < a.length; i++) h += (a[i] < 16 ? '0' : '') + a[i].toString(16);
        return h;
      }
    } catch (e) {}
    return Date.now().toString(36) + Math.random().toString(36).slice(2, 8);
  }
  function call(make, check) {
    var tries = 0;
    function once() {
      tries++;
      var ctl = window.AbortController ? new AbortController() : null;
      var t = setTimeout(function () { if (ctl) ctl.abort(); }, 25000);
      return make(ctl).then(function (r) { return r.json(); }).then(function (j) {
        clearTimeout(t); if (!check(j)) throw new Error('reply'); return j;
      }).catch(function (e) {
        clearTimeout(t);
        if (tries >= 4) throw e;
        return new Promise(function (res) { setTimeout(res, 1200 * tries); }).then(once);
      });
    }
    return once();
  }
  window.DiningAPI = {
    rid: rid,
    get: function (params) {
      var q = Object.keys(params).map(function (k) { return k + '=' + encodeURIComponent(params[k]); }).join('&');
      return call(function (ctl) { return fetch(EXEC + '?' + q + '&t=' + Date.now(), {signal: ctl && ctl.signal}); },
                  function (j) { return j && typeof j.ok === 'boolean'; });
    },
    post: function (body) {
      if (!body.rid) body.rid = rid();
      var data = JSON.stringify(body);
      return call(function (ctl) { return fetch(EXEC, {method: 'POST', headers: {'Content-Type': 'text/plain;charset=utf-8'}, body: data, signal: ctl && ctl.signal}); },
                  function (j) { return j && typeof j.ok === 'boolean' && (!j.rid || j.rid === body.rid); });
    }
  };
})();
