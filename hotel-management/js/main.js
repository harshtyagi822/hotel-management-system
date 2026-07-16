// Royal Palace Luxury Hotel — main front-end behaviors
// Requires: GSAP, ScrollTrigger, AOS, Swiper

(function () {
  // Footer year
  var yearEl = document.getElementById('year');
  if (yearEl) yearEl.textContent = new Date().getFullYear();

  // AOS
  if (window.AOS && typeof window.AOS.init === 'function') {
    AOS.init({
      once: true,
      duration: 900,
      easing: 'ease-out-cubic',
    });
  }

  // GSAP: subtle hero parallax + floating effects
  if (window.gsap) {
    try {
      gsap.registerPlugin(window.ScrollTrigger);

      var heroMedia = document.querySelector('.hero-media');
      if (heroMedia) {
        gsap.to(heroMedia, {
          yPercent: 3,
          ease: 'none',
          scrollTrigger: {
            trigger: 'header.hero',
            start: 'top top',
            end: 'bottom top',
            scrub: true,
          },
        });
      }

      // Animated counters on scroll for any [data-counter]
      var counterEls = document.querySelectorAll('[data-counter]');
      if (counterEls.length) {
        counterEls.forEach(function (el) {
          var target = parseInt(el.getAttribute('data-counter') || '0', 10);
          if (!target) return;
          var started = false;

          ScrollTrigger.create({
            trigger: el.closest('.counter-grid') || el,
            start: 'top 80%',
            onEnter: function () {
              if (started) return;
              started = true;

              gsap.fromTo(
                { val: 0 },
                {
                  val: target,
                  duration: 1.8,
                  ease: 'power3.out',
                  onUpdate: function () {
                    el.textContent = Math.round(this.targets()[0].val).toString();
                  },
                }
              );
            },
          });
        });
      }

      // Floating booking glass
      var bookingGlass = document.querySelector('.booking-glass');
      if (bookingGlass) {
        gsap.to(bookingGlass, {
          y: -6,
          duration: 2.6,
          ease: 'power1.inOut',
          repeat: -1,
          yoyo: true,
        });
      }

      // Button ripple-like glow
      document.addEventListener('click', function (e) {
        var btn = e.target.closest('a.btn, button.btn, button');
        if (!btn) return;

        if (btn.classList.contains('btn-gold') || btn.classList.contains('btn-outline-gold')) {
          var ripple = document.createElement('span');
          ripple.className = 'ripple';
          ripple.style.position = 'absolute';
          ripple.style.left = e.clientX - btn.getBoundingClientRect().left + 'px';
          ripple.style.top = e.clientY - btn.getBoundingClientRect().top + 'px';
          ripple.style.width = ripple.style.height = '8px';
          ripple.style.borderRadius = '999px';
          ripple.style.background = 'rgba(212,175,55,.35)';
          ripple.style.transform = 'translate(-50%,-50%)';
          ripple.style.pointerEvents = 'none';
          ripple.style.zIndex = '1';
          btn.style.position = 'relative';
          btn.appendChild(ripple);

          gsap.to(ripple, {
            scale: 30,
            opacity: 0,
            duration: 0.6,
            ease: 'power2.out',
            onComplete: function () {
              ripple.remove();
            },
          });
        }
      });
    } catch (err) {
      // Fail silently for student environment / CDNs not loaded.
    }
  }

  // Simple hero booking form validation
  var form = document.getElementById('heroBookingForm');
  if (form) {
    form.addEventListener('submit', function (ev) {
      ev.preventDefault();

      var name = document.getElementById('heroName');
      var room = document.getElementById('heroRoom');
      var checkIn = document.getElementById('heroCheckIn');
      var checkOut = document.getElementById('heroCheckOut');
      var phone = document.getElementById('heroPhone');

      var ok = true;
      var phoneVal = (phone.value || '').trim();
      var nameVal = (name.value || '').trim();

      var dateIn = checkIn.value;
      var dateOut = checkOut.value;

      ok = ok && nameVal.length >= 2;
      ok = ok && room.value;
      ok = ok && phoneVal.length === 10 && /^\d{10}$/.test(phoneVal);

      if (dateIn && dateOut) {
        ok = ok && new Date(dateOut) > new Date(dateIn);
      }

      if (!ok) {
        // Bootstrap styles
        [name, phone, checkIn, checkOut].forEach(function (el) {
          if (!el) return;
          el.classList.add('is-invalid');
          setTimeout(function () {
            el.classList.remove('is-invalid');
          }, 1200);
        });
        return;
      }

      // Production-ready behavior: open Booking page prefilled via query string
      var qs = new URLSearchParams({
        name: nameVal,
        room: room.value,
        checkin: dateIn,
        checkout: dateOut,
        phone: phoneVal,
      });
      window.location.href = 'booking.html?' + qs.toString();
    });
  }
})();

