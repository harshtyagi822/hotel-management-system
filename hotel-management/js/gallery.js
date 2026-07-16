// Gallery interactions: filter + lightbox
(function () {
  var lightbox = document.getElementById('lightbox');
  var lightboxImg = document.getElementById('lightboxImg');
  var lightboxCaption = document.getElementById('lightboxCaption');
  var closeBtn = document.querySelector('.lightbox-close');

  function openLightbox(src, caption) {
    if (!lightbox || !lightboxImg) return;
    lightboxImg.src = src;
    lightboxCaption.textContent = caption || '';
    lightbox.classList.add('show');
    lightbox.setAttribute('aria-hidden', 'false');
  }

  function closeLightbox() {
    if (!lightbox) return;
    lightbox.classList.remove('show');
    lightbox.setAttribute('aria-hidden', 'true');
    if (lightboxImg) lightboxImg.src = '';
    if (lightboxCaption) lightboxCaption.textContent = '';
  }

  if (closeBtn) closeBtn.addEventListener('click', closeLightbox);
  if (lightbox) lightbox.addEventListener('click', function (e) {
    if (e.target === lightbox) closeLightbox();
  });
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') closeLightbox();
  });

  // Filter
  var filterBtns = document.querySelectorAll('[data-filter]');
  var tiles = document.querySelectorAll('[data-category]');

  function setVisible(category) {
    tiles.forEach(function (t) {
      var tileCat = t.getAttribute('data-category');
      if (category === 'all' || tileCat === category) {
        t.style.display = '';
        t.setAttribute('data-visible', '1');
      } else {
        t.style.display = 'none';
        t.setAttribute('data-visible', '0');
      }
    });
  }

  filterBtns.forEach(function (btn) {
    btn.addEventListener('click', function () {
      var cat = btn.getAttribute('data-filter') || 'all';
      setVisible(cat);
      filterBtns.forEach(function (b) {
        b.classList.toggle('active', b === btn);
      });
    });
  });

  // Lightbox binding on tiles
  document.addEventListener('click', function (e) {
    var tile = e.target.closest('[data-full]');
    if (!tile) return;
    var full = tile.getAttribute('data-full');
    var cap = tile.getAttribute('data-caption') || '';
    openLightbox(full, cap);
  });

  // Masonry-ish layout using CSS columns if present.
})();

