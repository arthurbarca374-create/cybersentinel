const API = '';

let currentView = 'overview';

function escapeHtml(str) {
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}

function getToken() {
  const match = document.cookie.match(/(?:^|;\s*)cs_token=([^;]*)/);
  return match ? match[1] : localStorage.getItem('cs_token');
}

function apiFetch(path, options = {}) {
  const token = getToken();
  const headers = { ...options.headers };
  if (token) headers['Authorization'] = `Bearer ${token}`;
  if (!options.body) headers['Content-Type'] = 'application/json';
  return fetch(`${API}${path}`, { ...options, headers }).then(async res => {
    if (res.status === 401) {
      localStorage.removeItem('cs_token');
      window.location.href = '/login';
      return null;
    }
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || `HTTP ${res.status}`);
    }
    return res.json();
  });
}

// Auth: check for token in cookie (set by backend OAuth callback) or URL hash
(function initAuth() {
  const token = getToken();
  if (!token) {
    const hash = window.location.hash;
    if (hash && hash.startsWith('#token=')) {
      const t = hash.substring(7);
      localStorage.setItem('cs_token', t);
      document.cookie = `cs_token=${t}; path=/; max-age=86400; samesite=lax`;
      window.location.hash = '';
    }
  }
  if (!getToken()) {
    window.location.href = '/login';
  }
})();

document.addEventListener('DOMContentLoaded', async () => {
  await loadProfile();
  setupNavigation();
  showView('overview');
});

async function loadProfile() {
  try {
    const user = await apiFetch('/api/auth/me');
    if (!user) return;
    const avatarEl = document.getElementById('user-avatar');
    if (avatarEl) {
      avatarEl.src = user.avatar_url || `https://ui-avatars.com/api/?name=${encodeURIComponent(user.username)}&background=00ff88&color=0a0a0a&bold=true`;
      avatarEl.alt = escapeHtml(user.username);
    }
    const usernameEl = document.getElementById('user-username');
    if (usernameEl) usernameEl.textContent = escapeHtml(user.username);
    const greetEl = document.getElementById('greet-name');
    if (greetEl) greetEl.textContent = escapeHtml(user.username);

    const trialData = await apiFetch('/api/users/trial/status');
    if (trialData) {
      const banner = document.getElementById('trial-banner');
      if (banner) {
        if (trialData.is_active) {
          const daysLeft = Math.ceil((new Date(trialData.expires_at) - new Date()) / (1000 * 60 * 60 * 24));
          banner.querySelector('strong').textContent = `${daysLeft} days remaining`;
          banner.style.display = 'block';
        } else {
          banner.style.display = 'none';
        }
      }
      updateScanUI(trialData);
    }
  } catch (err) {
    console.error('Profile load failed:', err);
  }
}

function updateScanUI(trialData) {
  const maxScans = trialData.max_scans || 10;
  const remaining = trialData.scans_remaining ?? maxScans;
  const used = Math.max(0, maxScans - remaining);

  const creditsEl = document.getElementById('scan-credits');
  if (creditsEl) creditsEl.textContent = `${remaining} / ${maxScans}`;

  const barEl = document.getElementById('scan-bar');
  if (barEl) {
    const pct = maxScans > 0 ? (used / maxScans) * 100 : 0;
    barEl.style.width = `${Math.min(100, Math.max(0, pct))}%`;
  }

  const btn = document.getElementById('run-scan-btn');
  if (btn) {
    btn.disabled = remaining <= 0;
    btn.textContent = remaining > 0 ? `Run Scan (${remaining} credits)` : 'No scans remaining';
  }
}

function setupNavigation() {
  document.querySelectorAll('.nav-link').forEach(link => {
    link.addEventListener('click', e => {
      e.preventDefault();
      const view = link.dataset.view;
      if (view) showView(view);
    });
  });
}

function showView(view) {
  currentView = view;
  document.querySelectorAll('.view').forEach(el => el.style.display = 'none');
  document.querySelectorAll('.nav-link').forEach(el => el.classList.remove('active'));
  const targetView = document.getElementById(`view-${view}`);
  if (targetView) targetView.style.display = 'block';
  const navLink = document.querySelector(`.nav-link[data-view="${view}"]`);
  if (navLink) navLink.classList.add('active');

  if (view === 'overview') loadOverview();
  else if (view === 'scan') loadScanView();
  else if (view === 'community') loadCommunityMembers();
}

async function loadOverview() {
  try {
    const [scanData, threatStats] = await Promise.all([
      apiFetch('/api/scans'),
      apiFetch('/api/threat/stats').catch(() => null),
    ]);
    document.getElementById('total-scans').textContent = Array.isArray(scanData) ? scanData.length : '0';
    if (threatStats) {
      document.getElementById('threat-indicators').textContent = threatStats.total_indicators ?? '0';
    }
  } catch (_) { /* ignore */ }
}

async function loadScanView() {
  const targetsEl = document.getElementById('targets-list');
  const scanLogEl = document.getElementById('scan-log');
  if (!targetsEl && !scanLogEl) return;

  try {
    const targets = await apiFetch('/api/scans/targets') || [];
    if (targetsEl) {
      if (targets.length === 0) {
        targetsEl.innerHTML = '<p class="text-muted">No targets added yet. Add one below.</p>';
      } else {
        targetsEl.innerHTML = targets.map(t =>
          `<div class="target-item">
            <span><strong>${escapeHtml(t.name)}</strong> (${escapeHtml(t.host)})</span>
            <button onclick="deleteTarget(${t.id})" class="btn-small btn-danger">Remove</button>
          </div>`
        ).join('');
      }
    }
    const scans = await apiFetch('/api/scans') || [];
    if (scanLogEl) {
      if (scans.length === 0) {
        scanLogEl.innerHTML = '<p class="text-muted">No scans yet.</p>';
      } else {
        scanLogEl.innerHTML = scans.slice(0, 10).map(s =>
          `<div class="scan-log-item">
            <span class="scan-status status-${s.status}">${s.status.toUpperCase()}</span>
            <span>${escapeHtml(s.scan_type)} scan</span>
            <span class="text-muted">${s.created_at ? new Date(s.created_at).toLocaleString() : ''}</span>
          </div>`
        ).join('');
      }
    }
  } catch (_) { /* ignore */ }
}

// Add target form
document.addEventListener('submit', async (e) => {
  if (e.target.id === 'add-target-form') {
    e.preventDefault();
    const name = document.getElementById('target-name')?.value?.trim();
    const host = document.getElementById('target-host')?.value?.trim();
    if (!name || !host) return;
    try {
      await apiFetch('/api/scans/targets', {
        method: 'POST',
        body: JSON.stringify({ name, host }),
      });
      document.getElementById('target-name').value = '';
      document.getElementById('target-host').value = '';
      loadScanView();
    } catch (err) {
      alert(err.message || 'Failed to add target');
    }
  }
});

async function deleteTarget(id) {
  try {
    await apiFetch(`/api/scans/targets/${id}`, { method: 'DELETE' });
    loadScanView();
  } catch (err) {
    alert(err.message || 'Failed to delete target');
  }
}

// Run scan handler
document.addEventListener('click', async (e) => {
  if (e.target.id === 'run-scan-btn') {
    const btn = e.target;
    btn.disabled = true;
    btn.textContent = 'Running...';
    try {
      const targets = await apiFetch('/api/scans/targets');
      if (!targets || targets.length === 0) {
        alert('Add a target first!');
        btn.disabled = false;
        updateScanUI(await apiFetch('/api/users/trial/status'));
        return;
      }
      const scan = await apiFetch('/api/scans/run', {
        method: 'POST',
        body: JSON.stringify({ target_id: targets[0].id, scan_type: 'quick' }),
      });
      if (scan) {
        document.getElementById('scan-result').innerHTML =
          `<div class="alert alert-success">Scan launched (ID: ${scan.id}). Check results in a moment.</div>`;
        setTimeout(async () => {
          loadScanView();
          const trialData = await apiFetch('/api/users/trial/status');
          if (trialData) updateScanUI(trialData);
        }, 3000);
      }
    } catch (err) {
      document.getElementById('scan-result').innerHTML =
        `<div class="alert alert-error">${escapeHtml(err.message || 'Scan failed')}</div>`;
    }
  }
});

async function loadCommunityMembers() {
  const grid = document.getElementById('community-grid');
  if (!grid) return;
  try {
    const data = await apiFetch('/api/users/community/members');
    if (!data?.recent_members) {
      grid.innerHTML = '<p class="text-muted">No community members yet. Be the first!</p>';
      return;
    }
    grid.innerHTML = data.recent_members.map(m => {
      const name = escapeHtml(m.username || 'Anonymous');
      return `<div class="member-card">
        <img src="${escapeHtml(m.avatar_url || `https://ui-avatars.com/api/?name=${encodeURIComponent(m.username)}&background=00ff88&color=0a0a0a&bold=true`)}"
             alt="${name}"
             title="${name}"
             onerror="this.outerHTML='<div class=\\'avatar-placeholder\\'>${name[0]}</div>'">
        <div class="member-name">${name}</div>
        <div class="member-joined">${m.joined ? new Date(m.joined).toLocaleDateString() : ''}</div>
      </div>`;
    }).join('');
  } catch (_) {
    grid.innerHTML = '<p class="text-muted">Failed to load community members.</p>';
  }
}

document.addEventListener('DOMContentLoaded', () => {
  const hash = window.location.hash;
  if (hash && hash.startsWith('#token=')) {
    const token = hash.substring(7);
    localStorage.setItem('cs_token', token);
    document.cookie = `cs_token=${token}; path=/; max-age=86400; samesite=lax`;
    window.location.hash = '';
  }
});
