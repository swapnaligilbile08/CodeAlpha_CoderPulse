/* Dark mode, login card, like button and follow button. */
(function () {
  'use strict';
  var root = document.documentElement;

  /* dark mode (saved in localStorage) */
  document.addEventListener('click', function (e) {
    if (!e.target.closest('[data-theme-toggle]')) return;
    var next = root.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
    root.setAttribute('data-theme', next);
    try { localStorage.setItem('cp-theme', next); } catch (err) {}
  });

  /* login card: slide between Login and Registration without a reload */
  document.addEventListener('click', function (e) {
    var link = e.target.closest('[data-auth-switch]');
    var box = document.querySelector('[data-auth]');
    if (!link || !box) return;
    e.preventDefault();
    var toRegister = link.dataset.authSwitch === 'register';
    box.classList.toggle('active', toRegister);
    document.title = (toRegister ? 'Sign up' : 'Log in') + ' \u00b7 CoderPulse';
    try { history.replaceState(null, '', link.href); } catch (err) {}
  });

  /* send a POST and read the JSON answer */
  function csrf() { return document.querySelector('meta[name="csrf-token"]').content; }

  function toggle(url) {
    return fetch(url, { method: 'POST', credentials: 'same-origin', headers: { 'X-CSRFToken': csrf() } })
      .then(function (r) {
        if (r.redirected) { window.location.href = r.url; throw new Error('Please log in.'); }
        return r.json().then(function (data) {
          if (!r.ok) throw new Error(data.error || 'Something went wrong.');
          return data;
        });
      });
  }

  function setOn(btn, on, cls) {
    btn.classList.toggle(cls, on);
    btn.setAttribute('aria-pressed', String(on));
  }

  document.addEventListener('click', function (e) {
    var like = e.target.closest('[data-like]');
    var follow = e.target.closest('[data-follow]');
    var btn = like || follow;
    if (!btn || btn.disabled) return;
    btn.disabled = true;

    toggle(btn.dataset.url).then(function (d) {
      if (like) {
        setOn(btn, d.liked, 'on');
        btn.classList.remove('pop');
        if (d.liked) { void btn.offsetWidth; btn.classList.add('pop'); }   // little heart pop
        btn.querySelector('.count').textContent = d.count;
      } else {
        setOn(btn, d.following, 'is-on');
        btn.textContent = d.following ? 'Following' : 'Follow';
        document.querySelectorAll('[data-followers-count]').forEach(function (el) { el.textContent = d.followers; });
      }
    }).catch(function (err) { alert(err.message); })
      .then(function () { btn.disabled = false; });
  });
})();
