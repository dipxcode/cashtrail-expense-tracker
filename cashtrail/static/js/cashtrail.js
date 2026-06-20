/* ============================================================
   CashTrail  –  Main JavaScript  v2.0
   ============================================================ */

document.addEventListener('DOMContentLoaded', () => {

  /* ── Animated stat counters ── */
  document.querySelectorAll('.s-val').forEach(el => {
    const raw = el.textContent.replace(/[^0-9.]/g, '');
    const target = parseFloat(raw);
    if (isNaN(target) || target === 0) return;
    const prefix = el.textContent.match(/^[^\d]*/)?.[0] || '';
    const suffix = el.textContent.match(/[^\d.]*$/)?.[0] || '';
    let current = 0, steps = 50, inc = target / steps;
    const timer = setInterval(() => {
      current = Math.min(current + inc, target);
      el.textContent = prefix + Math.round(current).toLocaleString('en-IN') + suffix;
      if (current >= target) clearInterval(timer);
    }, 16);
  });

  /* ── Receipt file preview ── */
  const receiptInput = document.querySelector('input[name="receipt"]');
  if (receiptInput) {
    receiptInput.addEventListener('change', function () {
      const file = this.files[0];
      if (!file) return;
      const reader = new FileReader();
      reader.onload = e => {
        let img = document.getElementById('receiptPreview');
        if (!img) {
          img = Object.assign(document.createElement('img'), { id: 'receiptPreview', className: 'receipt-preview' });
          this.parentNode.appendChild(img);
        }
        img.src = e.target.result;
      };
      reader.readAsDataURL(file);
    });
  }

  /* ── Recurring field toggle ── */
  const recurCheck = document.getElementById('id_is_recurring');
  const recurField = document.getElementById('id_recurrence');
  if (recurCheck && recurField) {
    const wrap = recurField.closest('.mb-3') || recurField.parentElement;
    const sync = () => wrap.style.display = recurCheck.checked ? '' : 'none';
    sync(); recurCheck.addEventListener('change', sync);
  }

  /* ── Auto-dismiss toasts ── */
  setTimeout(() => {
    document.querySelectorAll('.ct-toast').forEach(t => {
      t.style.opacity = '0'; t.style.transition = 'opacity .3s';
      setTimeout(() => t.remove(), 300);
    });
  }, 4500);

  /* ── Budget month/year autofill ── */
  const monthF = document.getElementById('id_month');
  const yearF  = document.getElementById('id_year');
  if (monthF && !monthF.value) {
    const n = new Date();
    monthF.value = n.getMonth() + 1;
    if (yearF && !yearF.value) yearF.value = n.getFullYear();
  }

  /* ── Scroll active nav into view ── */
  document.querySelector('.ct-nav-item.active')?.scrollIntoView({ block: 'nearest' });

  /* ── Chart.js theme sync ── */
  function syncChartTheme() {
    if (typeof Chart === 'undefined') return;
    const dark = document.documentElement.dataset.bsTheme === 'dark';
    Chart.defaults.color       = dark ? '#9491B4' : '#6B7280';
    Chart.defaults.borderColor = dark ? '#2D2B4E' : '#EDE9FE';
  }
  syncChartTheme();
  new MutationObserver(syncChartTheme).observe(
    document.documentElement, { attributes: true, attributeFilter: ['data-bs-theme'] }
  );

  console.log('%c💸 CashTrail v2.0', 'color:#7C3AED;font-weight:800;font-size:14px');
});

/* ── Global helpers ── */
window.showToast = (msg, type = 'success') => {
  const colors = { success: '#10B981', error: '#EF4444', warning: '#F59E0B', info: '#7C3AED' };
  const wrap = document.querySelector('.ct-toasts') || (() => {
    const c = document.createElement('div'); c.className = 'ct-toasts'; document.body.appendChild(c); return c;
  })();
  const t = document.createElement('div');
  t.className = 'ct-toast';
  t.style.background = colors[type] || colors.info;
  t.textContent = msg;
  wrap.appendChild(t);
  setTimeout(() => { t.style.opacity = '0'; t.style.transition = 'opacity .3s'; setTimeout(() => t.remove(), 300); }, 3500);
};
