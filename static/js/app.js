/* SwingTrader Pro — Core JS */

// Toast notifications
function showToast(msg, type = 'info') {
  const t = document.createElement('div');
  t.className = `toast ${type}`;
  t.textContent = msg;
  document.body.appendChild(t);
  requestAnimationFrame(() => t.classList.add('show'));
  setTimeout(() => { t.classList.remove('show'); setTimeout(() => t.remove(), 300); }, 3000);
}

// API helper
async function api(url, method = 'GET', body = null) {
  const opts = { method, headers: { 'Content-Type': 'application/json' } };
  if (body) opts.body = JSON.stringify(body);
  const r = await fetch(url, opts);
  if (!r.ok) throw new Error(`HTTP ${r.status}`);
  return r.json();
}

// Live IST clock
function startClock() {
  const el = document.getElementById('live-clock');
  if (!el) return;
  const update = () => {
    const now = new Date().toLocaleString('en-IN', {
      timeZone: 'Asia/Kolkata',
      hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false
    });
    el.textContent = `IST ${now}`;
  };
  update();
  setInterval(update, 1000);
}

// ─── Risk Calculator ───────────────────────────────────────
function calcRisk() {
  const capital   = parseFloat(document.getElementById('rc-capital')?.value) || 0;
  const riskPct   = parseFloat(document.getElementById('rc-risk')?.value) || 0;
  const entry     = parseFloat(document.getElementById('rc-entry')?.value) || 0;
  const sl        = parseFloat(document.getElementById('rc-sl')?.value) || 0;
  const target    = parseFloat(document.getElementById('rc-target')?.value) || 0;

  if (!capital || !riskPct || !entry || !sl) {
    document.getElementById('rc-results')?.classList.add('hidden');
    return;
  }

  const riskAmount    = capital * (riskPct / 100);
  const slPoints      = Math.abs(entry - sl);
  const positionSize  = slPoints > 0 ? Math.floor(riskAmount / slPoints) : 0;
  const maxLoss       = +(positionSize * slPoints).toFixed(2);

  let rr = 0, profit = 0;
  if (target && slPoints > 0) {
    const rewardPoints = Math.abs(target - entry);
    rr     = +(rewardPoints / slPoints).toFixed(2);
    profit = +(positionSize * rewardPoints).toFixed(2);
  }

  // Show results
  document.getElementById('rc-qty').textContent     = positionSize;
  document.getElementById('rc-maxloss').textContent = `₹${maxLoss.toLocaleString('en-IN')}`;
  document.getElementById('rc-rr').textContent      = rr ? `1 : ${rr}` : 'N/A';
  document.getElementById('rc-profit').textContent  = profit ? `₹${profit.toLocaleString('en-IN')}` : '—';

  // Color rr
  const rrEl = document.getElementById('rc-rr');
  rrEl.style.color = rr >= 2 ? 'var(--green)' : rr >= 1 ? 'var(--yellow)' : 'var(--red)';

  document.getElementById('rc-results')?.classList.remove('hidden');
}

// ─── Trade Modal ───────────────────────────────────────────
function openTradeModal() {
  document.getElementById('trade-modal')?.classList.add('show');
}
function closeTradeModal() {
  document.getElementById('trade-modal')?.classList.remove('show');
}

async function submitTrade(e) {
  e.preventDefault();
  const form = e.target;
  const fd = new FormData(form);
  try {
    const r = await fetch('/journal/add', { method: 'POST', body: fd });
    const data = await r.json();
    if (data.success) {
      showToast('Trade saved!', 'success');
      closeTradeModal();
      form.reset();
      setTimeout(() => location.reload(), 800);
    } else {
      showToast('Failed to save trade', 'error');
    }
  } catch(err) {
    showToast('Error: ' + err.message, 'error');
  }
}

async function deleteTrade(id) {
  if (!confirm('Delete this trade?')) return;
  try {
    await api(`/journal/delete/${id}`, 'DELETE');
    showToast('Trade deleted', 'success');
    document.getElementById(`trade-row-${id}`)?.remove();
  } catch {
    showToast('Delete failed', 'error');
  }
}

// ─── Admin ─────────────────────────────────────────────────
async function userAction(uid, action) {
  try {
    await api(`/admin/user/${uid}/action`, 'POST', { action });
    showToast(`Done!`, 'success');
    setTimeout(() => location.reload(), 800);
  } catch {
    showToast('Action failed', 'error');
  }
}

// ─── News ──────────────────────────────────────────────────
async function refreshNews() {
  const btn = document.getElementById('refresh-news-btn');
  if (btn) btn.textContent = 'Refreshing...';
  try {
    const d = await api('/news/refresh');
    showToast(`${d.count} articles loaded!`, 'success');
    setTimeout(() => location.reload(), 1000);
  } catch {
    showToast('Refresh failed', 'error');
  }
  if (btn) btn.textContent = '↻ Refresh';
}

// ─── Algo Scan ─────────────────────────────────────────────
async function runScan() {
  const btn = document.getElementById('run-scan-btn');
  if (btn) { btn.textContent = 'Scanning...'; btn.disabled = true; }
  try {
    const d = await api('/algo/run', 'POST');
    showToast(d.message || 'Scan complete!', 'success');
    setTimeout(() => location.reload(), 1000);
  } catch(err) {
    showToast('Scan failed: ' + err.message, 'error');
  }
  if (btn) { btn.textContent = '▶ Run Scan'; btn.disabled = false; }
}

// ─── Init ──────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  startClock();

  // Active nav highlight
  const path = window.location.pathname;
  document.querySelectorAll('.nav-item').forEach(a => {
    if (a.getAttribute('href') === path) a.classList.add('active');
  });

  // Risk calc — live update on any input change
  ['rc-capital','rc-risk','rc-entry','rc-sl','rc-target'].forEach(id => {
    document.getElementById(id)?.addEventListener('input', calcRisk);
  });

  // Set today's date in trade form
  const dateInput = document.querySelector('[name="trade_date"]');
  if (dateInput && !dateInput.value) {
    dateInput.value = new Date().toISOString().slice(0, 10);
  }
});