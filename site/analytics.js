// Google Analytics 4, set up like the portfolio's (portfolio/src/lib/analytics.ts):
// one shared property (filter reports by hostname), ad features off, no
// analytics cookies for visitors in the EEA, the UK or Switzerland, and
// Google's script fetched only once the page has loaded and the browser is idle.
// Leave GA_ID empty to turn analytics off.
(() => {
  const GA_ID = 'G-LNBMSHVG6Q';
  if (!GA_ID) return;
  const CONSENT_REGIONS = ['AT', 'BE', 'BG', 'HR', 'CY', 'CZ', 'DK', 'EE', 'FI', 'FR', 'DE', 'GR', 'HU', 'IS', 'IE', 'IT',
    'LV', 'LI', 'LT', 'LU', 'MT', 'NL', 'NO', 'PL', 'PT', 'RO', 'SK', 'SI', 'ES', 'SE', 'GB', 'CH'];
  const denied = { analytics_storage: 'denied', ad_storage: 'denied', ad_user_data: 'denied', ad_personalization: 'denied' };

  window.dataLayer = window.dataLayer || [];
  function gtag() { window.dataLayer.push(arguments); }
  window.gtag = gtag;
  gtag('consent', 'default', { ...denied, region: CONSENT_REGIONS });
  gtag('consent', 'default', { ...denied, analytics_storage: 'granted' });
  gtag('js', new Date());
  gtag('config', GA_ID, { allow_google_signals: false, allow_ad_personalization_signals: false });

  const load = () => {
    const s = document.createElement('script');
    s.async = true;
    s.src = `https://www.googletagmanager.com/gtag/js?id=${GA_ID}`;
    document.head.appendChild(s);
  };
  addEventListener('load', () => ('requestIdleCallback' in window ? requestIdleCallback(load, { timeout: 2000 }) : setTimeout(load, 1)));

  // Filters: which one changed and its new value.
  document.addEventListener('change', (e) => {
    const t = e.target;
    if (!t.closest?.('#filters') || t.id === 'q') return;
    gtag('event', 'filter_change', { filter: t.id, value: t.type === 'checkbox' ? String(t.checked) : t.value || 'all' });
  }, true);

  // Search terms, once the visitor stops typing.
  let typing;
  document.addEventListener('input', (e) => {
    if (e.target.id !== 'q') return;
    clearTimeout(typing);
    typing = setTimeout(() => {
      const term = e.target.value.trim();
      if (term.length >= 2) gtag('event', 'search', { search_term: term.slice(0, 100) });
    }, 1500);
  }, true);

  // A job posting opened on the company's careers page.
  document.addEventListener('click', (e) => {
    const a = e.target.closest?.('a.ttl[href]');
    if (!a) return;
    gtag('event', 'job_click', {
      company: a.closest('tr')?.querySelector('.co')?.textContent ?? '',
      link_domain: new URL(a.href, location.href).hostname,
    });
  }, true);
})();
