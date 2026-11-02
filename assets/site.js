// Gian Franco Morini — small site behaviours (menu, video players, lightbox, back-to-top)
(function () {
  // Mobile menu
  var toggle = document.querySelector('.menu-toggle');
  var menu = document.getElementById('menu');
  if (toggle && menu) {
    toggle.addEventListener('click', function () {
      var open = menu.classList.toggle('open');
      toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
    });
  }

  // Video thumbnails: YouTube thumbnails are set at build time; Vimeo ones are fetched here.
  var facades = document.querySelectorAll('.video-facade');
  facades.forEach(function (el) {
    if (el.dataset.provider !== 'vimeo') return;
    var page = 'https://vimeo.com/' + el.dataset.id + (el.dataset.hash ? '/' + el.dataset.hash : '');
    fetch('https://vimeo.com/api/oembed.json?width=1280&url=' + encodeURIComponent(page))
      .then(function (r) { return r.ok ? r.json() : null; })
      .then(function (d) {
        if (!d) return;
        if (d.thumbnail_url && !el.querySelector('img')) {
          var img = new Image();
          img.alt = '';
          img.loading = 'lazy';
          img.src = d.thumbnail_url.replace(/_\d+x\d+/, '_1280x720');
          el.insertBefore(img, el.firstChild);
        }
        var t = el.querySelector('.video-title');
        if (t && d.title) { t.textContent = d.title; t.classList.add('has-title'); el.setAttribute('aria-label', 'Play ' + d.title); }
      })
      .catch(function () {});
  });

  function withAutoplay(src) {
    return src + (src.indexOf('?') > -1 ? '&' : '?') + 'autoplay=1';
  }
  function makeIframe(src) {
    var f = document.createElement('iframe');
    f.src = withAutoplay(src);
    f.allow = 'autoplay; fullscreen; picture-in-picture; encrypted-media';
    f.allowFullscreen = true;
    f.title = 'Video player';
    return f;
  }

  // Lightbox for popup galleries
  var lb = document.querySelector('.lightbox');
  var lbFrame = lb && lb.querySelector('.lightbox-frame');
  function closeLb() { if (!lb) return; lb.hidden = true; lbFrame.innerHTML = ''; document.body.style.overflow = ''; }
  if (lb) {
    lb.addEventListener('click', function (e) { if (e.target === lb || e.target.classList.contains('lightbox-close')) closeLb(); });
    document.addEventListener('keydown', function (e) { if (e.key === 'Escape') closeLb(); });
  }

  facades.forEach(function (el) {
    el.addEventListener('click', function () {
      if (el.dataset.mode === 'popup' && lb) {
        lbFrame.innerHTML = '';
        lbFrame.appendChild(makeIframe(el.dataset.embed));
        lb.hidden = false;
        document.body.style.overflow = 'hidden';
        return;
      }
      if (el.classList.contains('playing')) return;
      el.classList.add('playing');
      el.appendChild(makeIframe(el.dataset.embed));
    });
  });

  // Back to top
  var top = document.querySelector('.to-top');
  if (top) {
    var onScroll = function () { top.classList.toggle('show', window.scrollY > 800); };
    window.addEventListener('scroll', onScroll, { passive: true });
    top.addEventListener('click', function (e) { e.preventDefault(); window.scrollTo({ top: 0, behavior: 'smooth' }); });
  }
})();
