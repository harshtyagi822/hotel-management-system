// Register page behavior — fetch-based registration with client-side validation
(function () {
  var form = document.getElementById('registerForm');
  var submitBtn = document.getElementById('registerSubmitBtn');
  var loadingEl = document.getElementById('registerLoading');
  var messageEl = document.getElementById('authMessage');

  var fullNameEl = document.getElementById('fullName');
  var emailEl = document.getElementById('registerEmail');
  var phoneEl = document.getElementById('phone');
  var passEl = document.getElementById('registerPassword');
  var confirmEl = document.getElementById('confirmPassword');

  var togglePassBtn = document.getElementById('toggleRegisterPassword');
  var toggleConfirmBtn = document.getElementById('toggleConfirmPassword');

  var togglePassIcon = togglePassBtn ? togglePassBtn.querySelector('i') : null;
  var toggleConfirmIcon = toggleConfirmBtn ? toggleConfirmBtn.querySelector('i') : null;

  var isSubmitting = false;
  var redirectTimer = null;

  function setMessage(type, text) {
    if (!messageEl) return;
    messageEl.style.display = 'block';
    messageEl.classList.remove('success', 'error');
    if (type) messageEl.classList.add(type);
    messageEl.textContent = text;
  }

  function setSubmitting(isBusy) {
    isSubmitting = isBusy;
    if (!submitBtn || !loadingEl) return;
    submitBtn.disabled = isBusy;
    loadingEl.style.display = isBusy ? 'inline-block' : 'none';

    var label = submitBtn.querySelector('.btn-label');
    if (label) label.style.opacity = isBusy ? '0.75' : '1';
  }

  function setInvalid(el, invalid) {
    if (!el) return;
    el.classList.toggle('is-invalid', !!invalid);
  }

  // Show/hide password toggles
  function setupEyeToggle(btn, input, icon, showAria, hideAria) {
    if (!btn || !input) return;

    btn.addEventListener('click', function () {
      var isPassword = input.type === 'password';
      input.type = isPassword ? 'text' : 'password';

      if (icon) {
        icon.classList.toggle('fa-eye', !isPassword);
        icon.classList.toggle('fa-eye-slash', isPassword);
      }

      btn.setAttribute('aria-label', isPassword ? hideAria : showAria);
    });
  }

  setupEyeToggle(togglePassBtn, passEl, togglePassIcon, 'Show password', 'Hide password');
  setupEyeToggle(toggleConfirmBtn, confirmEl, toggleConfirmIcon, 'Show confirm password', 'Hide confirm password');

  function validateForm() {
    // Note: backend /api/auth/register requires password length >= 8.

    if (!form) return false;

    var ok = true;

    var fullName = (fullNameEl && fullNameEl.value ? fullNameEl.value.trim() : '');
    var email = (emailEl && emailEl.value ? emailEl.value.trim() : '');
    var phone = (phoneEl && phoneEl.value ? phoneEl.value.trim() : '');
    var pass = passEl ? (passEl.value || '') : '';
    var confirm = confirmEl ? (confirmEl.value || '') : '';

    // reset invalid flags
    [fullNameEl, emailEl, phoneEl, passEl, confirmEl].forEach(function (el) {
      if (!el) return;
      el.classList.remove('is-invalid');
    });

    // Full name
    if (!fullNameEl || fullName.length < 2) {
      ok = false;
      setInvalid(fullNameEl, true);
    }

    // Email
    if (!emailEl || !emailEl.checkValidity()) {
      ok = false;
      setInvalid(emailEl, true);
    }

    // Phone: must be exactly 10 digits
    if (!phoneEl || !/^\d{10}$/.test(phone)) {
      ok = false;
      setInvalid(phoneEl, true);
    }

    // Password
    // Backend requires at least 8 characters.
    if (!passEl || pass.length < 8) {
      ok = false;
      setInvalid(passEl, true);
    }


    // Confirm password
    if (!confirmEl || confirm.length < 8 || pass !== confirm) {
      ok = false;
      setInvalid(confirmEl, true);
    }


    return ok;
  }

  // Live confirm match feedback
  if (confirmEl && passEl) {
    var onCheck = function () {
      if (!confirmEl || !passEl) return;
      var isMatch = (confirmEl.value || '') === (passEl.value || '');
      if (confirmEl.value.length === 0) {
        setInvalid(confirmEl, false);
        return;
      }
      setInvalid(confirmEl, !isMatch);
    };
    confirmEl.addEventListener('input', onCheck);
    passEl.addEventListener('input', onCheck);
  }

  if (form) {
    form.addEventListener('submit', function (ev) {
      ev.preventDefault();

      setMessage(null, '');

      if (isSubmitting) return;
      if (redirectTimer) clearTimeout(redirectTimer);

      if (!validateForm()) {
        form.classList.add('was-validated');
        return;
      }

      setSubmitting(true);

      // Backend /api/auth/register expects: full_name, email, phone, password
      // confirm_password is not required by backend.
      var payload = {
        full_name: (fullNameEl.value || '').trim(),
        email: (emailEl.value || '').trim(),
        phone: (phoneEl.value || '').trim(),
        password: passEl.value || ''
      };

      fetch('http://127.0.0.1:5000/api/auth/register', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
      })
        .then(function (res) {
          return res.json().then(function (data) {
            return { ok: res.ok, status: res.status, data: data };
          }).catch(function () {
            return { ok: res.ok, status: res.status, data: null };
          });
        })
        .then(function (result) {
          if (!result.ok) {
            var errMsg = 'Registration failed. Please try again.';
            var d = result.data;

            if (d) {
              if (typeof d.message === 'string') errMsg = d.message;
              else if (typeof d.error === 'string') errMsg = d.error;
              else if (typeof d.detail === 'string') errMsg = d.detail;
            }

            // Some backends return { errors: {...} }
            if (d && d.errors) {
              try {
                var firstKey = Object.keys(d.errors)[0];
                if (firstKey && Array.isArray(d.errors[firstKey]) && d.errors[firstKey][0]) {
                  errMsg = d.errors[firstKey][0];
                } else if (firstKey && typeof d.errors[firstKey] === 'string') {
                  errMsg = d.errors[firstKey];
                }
              } catch (e) {}
            }

            setMessage('error', errMsg);
            return;
          }

          // Success message
          var msg = 'Registration successful! Redirecting to login...';
          var data = result.data || {};
          if (data) {
            if (typeof data.message === 'string') msg = data.message + ' Redirecting to login...';
            else if (typeof data.detail === 'string') msg = data.detail;
          }

          setMessage('success', msg);

          redirectTimer = setTimeout(function () {
            window.location.href = 'login.html';
          }, 2000);
        })
        .catch(function () {
          setMessage('error', 'Could not reach the registration service. Check your backend server.');
        })
        .finally(function () {
          setSubmitting(false);
        });
    });
  }
})();

