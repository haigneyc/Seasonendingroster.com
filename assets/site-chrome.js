<script>
(function(){
  // Inject shared CSS once
  (function ensureCSS(){
    if (!document.querySelector('link[data-site-chrome]')) {
      const link = document.createElement('link');
      link.rel = 'stylesheet';
      link.href = '/assets/site-chrome.css';
      link.setAttribute('data-site-chrome','1');
      document.head.appendChild(link);
    }
  })();

  // Build + inject top tabs
  function installHeader(){
    if (document.querySelector('.sitebar')) return;
    const nav = [
      {href:'index.html',       text:'Home'},
      {href:'franchises.html',  text:'Franchises'},
      {href:'playoffs.html',    text:'Playoffs'},
      {href:'brackets.html',    text:'Brackets'},
      {href:'h2h.html',         text:'H2H'},
    ];
    const here = location.pathname.split('/').pop() || 'index.html';
    const el = document.createElement('div');
    el.className = 'sitebar';
    el.innerHTML = `
      <div class="bar-inner">
        <div class="brand">Season Ending Roster</div>
        <nav class="tabs" aria-label="Primary">
          ${nav.map(n => `<a href="${n.href}" ${n.href===here?'aria-current="page"':''}>${n.text}</a>`).join('')}
        </nav>
      </div>`;
    document.body.prepend(el);
  }

  // Install footer with version info
  function installFooter(){
    if (document.querySelector('.site-footer')) return;
    const foot = document.createElement('footer');
    foot.className = 'site-footer';
    foot.id = 'siteFoot';
    foot.innerHTML = `
      <div>© 2004–<span id="footYear"></span> Season Ending Roster</div>
      <div class="foot-meta">Data <span class="v">v—</span> • Updated <span class="u">—</span>
        <span class="src-wrap"> • <span class="src"></span></span>
      </div>`;
    document.body.appendChild(foot);
    document.getElementById('footYear').textContent = new Date().getFullYear();
    showDataVersion();
  }

  // Size sticky header correctly
  function setStickyOffset(){
    const bar = document.querySelector('.sitebar');
    const h = bar ? Math.ceil(bar.getBoundingClientRect().height) : 56;
    document.documentElement.style.setProperty('--stickyTop', (h + 8) + 'px');
  }

  // Compute a short data version + show source
  async function showDataVersion(){
    const CAND = p => [`data/processed/${p}`,`/data/processed/${p}`,`data/proccessed/${p}`,`/data/proccessed/${p}`];
    const sources = [...CAND('playoff_metrics.json'), ...CAND('metrics.json'), ...CAND('franchise_career_stats.csv')];
    async function fetchFirst(paths){
      for (const url of paths){
        try {
          const r = await fetch(url, {cache:'no-store'});
          if (r.ok) return {url, text: await r.text(), lastModified: r.headers.get('last-modified')};
        } catch {}
      }
      return null;
    }
    const res = await fetchFirst(sources);
    const foot = document.getElementById('siteFoot');
    if (!foot) return;
    const vEl = foot.querySelector('.v'), uEl = foot.querySelector('.u'), sEl = foot.querySelector('.src');
    if (!res){ vEl.textContent='v–'; uEl.textContent='no data'; sEl.textContent='not found'; return; }
    const enc = new TextEncoder().encode(res.text);
    const buf = await crypto.subtle.digest('SHA-256', enc);
    const ver = Array.from(new Uint8Array(buf)).map(b=>b.toString(16).padStart(2,'0')).join('').slice(0,8);
    vEl.textContent = 'v'+ver;
    uEl.textContent = res.lastModified ? new Date(res.lastModified).toLocaleString() : new Date().toLocaleString();
    sEl.textContent = res.url.replace(location.origin,'');
  }

  // Boot
  function boot(){
    installHeader();
    installFooter();
    setStickyOffset();
    addEventListener('resize', setStickyOffset, {passive:true});
  }
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot);
  } else {
    boot();
  }
})();
</script>
