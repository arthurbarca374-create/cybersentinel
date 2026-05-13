const API = '';

function getToken() {
  // Try cookie first, then localStorage fallback
  const match = document.cookie.match(/(?:^|;\s*)cs_token=([^;]*)/);
  return match ? match[1] : localStorage.getItem('cs_token');
}

function saveToken(token) {
  // Use HttpOnly cookie via backend is ideal, but for SPA fallback store in localStorage
  localStorage.setItem('cs_token', token);
  document.cookie = `cs_token=${token}; path=/; max-age=86400; samesite=lax`;
}

function removeToken() {
  localStorage.removeItem('cs_token');
  document.cookie = 'cs_token=; path=/; max-age=0';
}

function escapeHtml(str) {
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}

function getAPIPath(path) {
  return `${API}${path}`;
}

async function apiFetch(path, options = {}) {
  const token = getToken();
  const headers = { ...options.headers };
  if (token) headers['Authorization'] = `Bearer ${token}`;
  if (!options.body || options.body instanceof FormData) {
    if (!(options.body instanceof FormData)) headers['Content-Type'] = 'application/json';
  }
  try {
    const res = await fetch(getAPIPath(path), { ...options, headers });
    if (res.status === 401) {
      removeToken();
      if (!window.location.pathname.includes('/login')) {
        window.location.href = '/login';
      }
      return null;
    }
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || `HTTP ${res.status}`);
    }
    return res.json();
  } catch (e) {
    if (e.message !== 'Failed to fetch') throw e;
    return null;
  }
}

// Auth check on page load
(function checkAuth() {
  const token = getToken();
  const onLoginPage = window.location.pathname.includes('/login') || window.location.pathname.includes('/register');
  if (token && onLoginPage) {
    window.location.href = '/dashboard';
  } else if (!token && !onLoginPage && window.location.pathname !== '/' && !window.location.pathname.includes('/dashboard')) {
    window.location.href = '/login';
  }
})();

document.addEventListener('DOMContentLoaded', () => {
  // Login form
  const loginForm = document.getElementById('login-form');
  if (loginForm) {
    loginForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const username = document.getElementById('username')?.value?.trim();
      const password = document.getElementById('password')?.value?.trim();
      const errEl = document.getElementById('login-error');
      if (!username || !password) {
        errEl.textContent = 'Username and password are required';
        errEl.style.display = 'block';
        return;
      }
      try {
        const data = await apiFetch('/api/auth/login', {
          method: 'POST',
          body: JSON.stringify({ username, password }),
        });
        if (data?.access_token) {
          saveToken(data.access_token);
          window.location.href = '/dashboard';
        }
      } catch (err) {
        errEl.textContent = err.message || 'Login failed';
        errEl.style.display = 'block';
      }
    });
  }

  // Register form
  const registerForm = document.getElementById('register-form');
  if (registerForm) {
    registerForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const username = document.getElementById('username')?.value?.trim();
      const email = document.getElementById('email')?.value?.trim();
      const password = document.getElementById('password')?.value;
      const errEl = document.getElementById('register-error');
      if (!username || username.length < 3) {
        errEl.textContent = 'Username must be at least 3 characters';
        errEl.style.display = 'block';
        return;
      }
      if (!email || !email.includes('@')) {
        errEl.textContent = 'Valid email is required';
        errEl.style.display = 'block';
        return;
      }
      if (!password || password.length < 6) {
        errEl.textContent = 'Password must be at least 6 characters';
        errEl.style.display = 'block';
        return;
      }
      try {
        const data = await apiFetch('/api/auth/register', {
          method: 'POST',
          body: JSON.stringify({ username, email, password }),
        });
        if (data?.access_token) {
          saveToken(data.access_token);
          window.location.href = '/dashboard';
        }
      } catch (err) {
        errEl.textContent = err.message || 'Registration failed';
        errEl.style.display = 'block';
      }
    });
  }

  // Github OAuth link
  document.querySelectorAll('.github-oauth').forEach(el => {
    el.addEventListener('click', (e) => {
      e.preventDefault();
      window.location.href = '/api/auth/github';
    });
  });
});
