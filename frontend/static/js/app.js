const API = '';

// Sanitize user-provided strings for safe HTML insertion
function escapeHtml(str) {
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}

async function fetchStats() {
  try {
    const res = await fetch(`${API}/api/users/community/members`);
    if (!res.ok) return;
    const data = await res.json();
    document.getElementById('stat-members').textContent = data.total_members ?? '—';
    const avatarsEl = document.getElementById('member-avatars');
    if (avatarsEl && data.recent_members) {
      avatarsEl.innerHTML = data.recent_members.map(m => {
        const name = escapeHtml(m.username || 'User');
        const avatar = m.avatar_url
          ? `src="${escapeHtml(m.avatar_url)}"`
          : `data-initial="${name[0]}"`;
        const imgTag = m.avatar_url
          ? `<img ${avatar} alt="${name}" title="${name}">`
          : `<div class="avatar-initial" title="${name}">${name[0]}</div>`;
        return imgTag;
      }).join('');
    }
  } catch (_) {
    // API not reachable yet
  }
}

document.addEventListener('DOMContentLoaded', () => {
  fetchStats();
  document.querySelectorAll('a[href^="#"]').forEach(a => {
    a.addEventListener('click', e => {
      e.preventDefault();
      document.querySelector(a.getAttribute('href'))?.scrollIntoView({ behavior: 'smooth' });
    });
  });
});
