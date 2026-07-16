// Booking page behavior: validation + summary + URL query prefill
(function () {
  var params = new URLSearchParams(window.location.search);
  function q(name) { return params.get(name) || ''; }

  var form = document.getElementById('bookingForm');
  var summaryBox = document.getElementById('bookingSummary');

  var nameEl = document.getElementById('guestName');
  var emailEl = document.getElementById('guestEmail');
  var phoneEl = document.getElementById('guestPhone');
  var checkInEl = document.getElementById('checkIn');
  var checkOutEl = document.getElementById('checkOut');
  var guestsEl = document.getElementById('guestCount');
  var roomEl = document.getElementById('roomType');

  if (nameEl && q('name')) nameEl.value = q('name');
  if (phoneEl && q('phone')) phoneEl.value = q('phone');
  if (roomEl && q('room')) roomEl.value = q('room');
  if (checkInEl && q('checkin')) checkInEl.value = q('checkin');
  if (checkOutEl && q('checkout')) checkOutEl.value = q('checkout');

  function nightsBetween(a, b) {
    if (!a || !b) return 0;
    var da = new Date(a);
    var db = new Date(b);
    if (isNaN(da) || isNaN(db)) return 0;
    var diff = db.getTime() - da.getTime();
    return Math.max(0, Math.round(diff / (1000 * 60 * 60 * 24)));
  }

  function parseIntSafe(v) {
    var n = parseInt(v, 10);
    return isNaN(n) ? 0 : n;
  }

  var priceMap = {
    'Deluxe Room': 25000,
    'Executive Room': 35000,
    'Family Suite': 55000,
    'Presidential Suite': 85000,
  };

  function formatINR(n) {
    try {
      return new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(n);
    } catch {
      return '₹' + n.toLocaleString('en-IN');
    }
  }

  function updateSummary() {
    if (!summaryBox) return;

    var room = roomEl ? roomEl.value : '';
    var price = priceMap[room] || 25000;
    var nights = nightsBetween(checkInEl.value, checkOutEl.value);

    var subtotal = price * Math.max(1, nights);
    var gst = Math.round(subtotal * 0.18);
    var total = subtotal + gst;

    summaryBox.innerHTML =
      '<div class="d-flex justify-content-between"><span class="text-white-50">Room</span><span class="fw-bold">' + room + '</span></div>' +
      '<div class="d-flex justify-content-between mt-2"><span class="text-white-50">Stay Duration</span><span class="fw-bold">' + (nights || 1) + ' night(s)</span></div>' +
      '<div class="d-flex justify-content-between mt-2"><span class="text-white-50">Room Rate</span><span class="fw-bold">' + formatINR(price) + ' / night</span></div>' +
      '<div class="divider"></div>' +
      '<div class="d-flex justify-content-between"><span class="text-white-50">Subtotal</span><span class="fw-bold">' + formatINR(subtotal) + '</span></div>' +
      '<div class="d-flex justify-content-between mt-2"><span class="text-white-50">GST (18%)</span><span class="fw-bold">' + formatINR(gst) + '</span></div>' +
      '<div class="d-flex justify-content-between mt-3"><span class="text-white-50">Grand Total</span><span class="fw-bold price-gold">' + formatINR(total) + '</span></div>';
  }

  function setInvalid(el, state) {
    if (!el) return;
    if (state) el.classList.add('is-invalid');
    else el.classList.remove('is-invalid');
  }

  if (checkInEl && checkOutEl) {
    checkInEl.addEventListener('change', updateSummary);
    checkOutEl.addEventListener('change', updateSummary);
  }
  if (roomEl) roomEl.addEventListener('change', updateSummary);

  if (form) {
    form.addEventListener('submit', function (e) {
      e.preventDefault();

      var ok = true;

      var name = (nameEl && nameEl.value || '').trim();
      var email = (emailEl && emailEl.value || '').trim();
      var phone = (phoneEl && phoneEl.value || '').trim();
      var guests = parseIntSafe(guestsEl && guestsEl.value);
      var checkIn = checkInEl && checkInEl.value;
      var checkOut = checkOutEl && checkOutEl.value;

      ok = ok && name.length >= 2;
      ok = ok && /^\S+@\S+\.\S+$/.test(email);
      ok = ok && /^\d{10}$/.test(phone);
      ok = ok && guests >= 1;

      if (checkIn && checkOut) {
        ok = ok && new Date(checkOut) > new Date(checkIn);
      }

      setInvalid(nameEl, !(name.length >= 2));
      setInvalid(emailEl, !/^\S+@\S+\.\S+$/.test(email));
      setInvalid(phoneEl, !/^\d{10}$/.test(phone));

      if (!ok) return;

      // Production-ready: simulate reservation confirmation
      var msg = document.getElementById('bookingMessage');
      if (msg) {
        msg.classList.remove('d-none');
        msg.innerHTML = '<i class="fa-solid fa-circle-check text-warning me-2"></i> Request received. Our concierge will confirm shortly. In this demo, no server call is made.';
      }

      updateSummary();
    });
  }

  updateSummary();
})();

