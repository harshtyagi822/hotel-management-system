// Login page behavior — fetch-based auth with JWT storage

(function () {
  var form = document.getElementById('loginForm');
  var submitBtn = document.getElementById('loginSubmitBtn');
  var loadingEl = document.getElementById('loginLoading');
  var messageEl = document.getElementById('authMessage');

  var emailEl = document.getElementById('loginEmail');
  var passEl = document.getElementById('loginPassword');
  var rememberEl = document.getElementById('rememberMe');

  var toggleBtn = document.getElementById('toggleLoginPassword');
  var toggleIcon = toggleBtn ? toggleBtn.querySelector('i') : null;

  var isSubmitting = false;

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

  // Show/hide password toggle
  if (toggleBtn && passEl) {
    toggleBtn.addEventListener('click', function () {
      var isPassword = passEl.type === 'password';
      passEl.type = isPassword ? 'text' : 'password';

      if (toggleIcon) {
        toggleIcon.classList.toggle('fa-eye', !isPassword);
        toggleIcon.classList.toggle('fa-eye-slash', isPassword);
      }

      toggleBtn.setAttribute('aria-label', isPassword ? 'Hide password' : 'Show password');
    });
  }

  // Native + JS validation helpers
  function validateForm() {
    if (!form) return false;

    // Bootstrap-like validation classes
    var ok = true;

    var email = (emailEl && emailEl.value ? emailEl.value.trim() : '');
    var password = (passEl && passEl.value ? passEl.value : '');

    // Email
    if (!emailEl || !emailEl.checkValidity()) ok = false;

    // Password
    if (!passEl || password.length < 6) ok = false;

    // Mark invalid fields for user feedback
    [emailEl, passEl].forEach(function (el) {
      if (!el) return;
      if (ok && el === passEl) {
        // still ensure validity
        if (!el.checkValidity()) el.classList.add('is-invalid');
      }
    });

    return ok && (form.checkValidity ? form.checkValidity() : true);
  }

  if (form) {
    form.addEventListener('submit', function (ev) {
      ev.preventDefault();

      setMessage(null, '');

      if (isSubmitting) return;

      // Client-side validation
      var valid = validateForm();
      if (!valid) {
        form.classList.add('was-validated');
        // Let browser show invalid-feedback
        return;
      }

      setSubmitting(true);

      var payload = {
        email: (emailEl.value || '').trim(),
        password: passEl.value || ''
      };

      // IMPORTANT: only fetch() used (per requirement)
      fetch('http://127.0.0.1:5000/api/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
      })
        .then(function (res) {
          // Attempt to read JSON either way
          return res.json().then(function (data) {
            return { ok: res.ok, status: res.status, data: data };
          }).catch(function () {
            return { ok: res.ok, status: res.status, data: null };
          });
        })
        .then(function (result) {
          if (!result.ok) {
            var errMsg = 'Login failed. Please try again.';
            var d = result.data;

            // Best-effort extraction of backend error message
            if (d) {
              if (typeof d.message === 'string') errMsg = d.message;
              else if (typeof d.error === 'string') errMsg = d.error;
              else if (typeof d.detail === 'string') errMsg = d.detail;
            }

            setMessage('error', errMsg);
            return;
          }

          var data = result.data || {};

          // Best-effort JWT extraction
          var token = data.token || data.access_token || data.jwt || (typeof data === 'string' ? data : null);
          if (!token && data.data && (data.data.token || data.data.access_token)) {
            token = data.data.token || data.data.access_token;
          }

          if (!token) {
            setMessage('error', 'Login succeeded but token was not returned by the server.');
            return;
          }

          // Store token in localStorage (remember me controls token persistence only)
          // Since requirement says localStorage, we store there either way.
          try {
            localStorage.setItem('token', token);
            if (rememberEl && rememberEl.checked) {
              localStorage.setItem('rememberMe', '1');
            } else {
              localStorage.setItem('rememberMe', '0');
            }
          } catch (e) {
            // If localStorage fails, still redirect but show message
          }

          // Redirect to dashboard.html
          window.location.href = 'dashboard.html';
        })
        .catch(function () {
          setMessage('error', 'Could not reach the login service. Check your backend server.');
        })
        .finally(function () {
          setSubmitting(false);
        });
    });
  }
})();

