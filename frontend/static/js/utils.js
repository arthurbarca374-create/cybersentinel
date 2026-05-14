const API = '';

function escapeHtml(str) {
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}

function getToken() {
  const match = document.cookie.match(/(?:^|;\s*)cs_token=([^;]*)/);
  return match ? match[1] : localStorage.getItem('cs_token');
}

function saveToken(token) {
  localStorage.setItem('cs_token', token);
  document.cookie = `cs_token=${token}; path=/; max-age=86400; samesite=lax`;
}

function removeToken() {
  localStorage.removeItem('cs_token');
  document.cookie = 'cs_token=; path=/; max-age=0';
}

async function apiFetch(path, options = {}) {
  const token = getToken();
  const headers = { ...options.headers };
  if (token) headers['Authorization'] = `Bearer ${token}`;
  if (!options.body || options.body instanceof FormData) {
    if (!(options.body instanceof FormData)) headers['Content-Type'] = 'application/json';
  }
  try {
    const res = await fetch(`${API}${path}`, { ...options, headers });
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
