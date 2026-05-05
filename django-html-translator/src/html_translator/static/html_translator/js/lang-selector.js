// Alpine.js component: langSelector
// Maneja selección de idioma con polling hasta que la traducción esté lista.
//
// Uso en template:
//   {% load translations %}
//   <div x-data="langSelector()">...</div>
//   {% html_translator_assets %}
//
// Configuración opcional mediante parámetros:
//   langSelector({
//     pageKey: 'mi-pagina',           // detectado automáticamente si no se indica
//     requestUrl: '/translations/request/',  // URL del endpoint (por defecto)
//     defaultLang: 'es',              // idioma base (no se traduce)
//     pollInterval: 5000,             // ms entre polls (por defecto 5000)
//     pollTimeout: 180000,            // ms máximos de espera (por defecto 3 min)
//   })

let _autoTranslateTriggered = false;

function langSelector(options = {}) {
  const {
    pageKey: _pageKey = null,
    requestUrl = '/translations/request/',
    defaultLang = 'es',
    pollInterval = 5000,
    pollTimeout = 180000,
  } = options;

  const LANG_DISPLAY = { 'pt': 'PT' };
  const langLabel = code => LANG_DISPLAY[code] || code.toUpperCase();

  // Detectar idioma actual desde la URL
  const pathLang = window.location.pathname.match(/^\/([a-z]{2}(?:-[a-z]{2})?)\//)?.[1];
  const cookieLang = (document.cookie.split('; ').find(c => c.startsWith('lang=')) || '').split('=')[1];
  const initial = pathLang || cookieLang || defaultLang;

  // Detectar page_key automáticamente si no fue provisto
  function detectPageKey() {
    if (_pageKey) return _pageKey;
    const path = window.location.pathname.replace(/^\/[a-z]{2}(?:-[a-z]{2})?\//, '/');
    // Intenta detectar rutas de detalle: /{seccion}/{slug}/
    const detailMatch = path.match(/^\/([\w-]+)\/([\w-]+)\/?$/);
    if (detailMatch) return `${detailMatch[1]}-${detailMatch[2]}`;
    return 'home';
  }

  const pageKey = detectPageKey();

  // Genera la URL para un idioma dado
  function getUrl(lang) {
    const currentPath = window.location.pathname;
    // Elimina prefijo de idioma existente si lo hay
    const cleanPath = currentPath.replace(/^\/[a-z]{2}(?:-[a-z]{2})?\//, '/');
    if (lang === defaultLang) return cleanPath;
    return `/${lang}${cleanPath}`;
  }

  function requestTranslation(pk, l) {
    return fetch(requestUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ page_key: pk, lang: l }),
    });
  }

  return {
    currentLang: initial,
    langLabel,
    targetLang: null,
    loading: false,
    error: false,

    // Auto-request al cargar la página si el idioma activo no está en caché todavía
    async init() {
      if (initial === defaultLang || _autoTranslateTriggered) return;
      _autoTranslateTriggered = true;
      try {
        const resp = await requestTranslation(pageKey, initial);
        if (!resp.ok) {
          // Server error (4xx, 5xx) - stop auto-translate
          return;
        }
        const data = await resp.json();
        if (data.status === 'generating') {
          this.loading = true;
          this.targetLang = initial;
          const deadline = Date.now() + pollTimeout;
          while (Date.now() < deadline) {
            await new Promise(r => setTimeout(r, pollInterval));
            try {
              const pr = await requestTranslation(pageKey, initial);
              if (!pr.ok) {
                // Stop polling on server errors (4xx, 5xx)
                this.error = true;
                this.loading = false;
                return;
              }
              const pd = await pr.json();
              if (pd.status === 'cached') { window.location.reload(); return; }
              if (pd.status !== 'generating') {
                // Unexpected status - stop polling
                this.error = true;
                this.loading = false;
                return;
              }
            } catch (e) {
              // Network error - stop polling
              this.error = true;
              this.loading = false;
              return;
            }
          }
          this.error = true;
          this.loading = false;
        }
      } catch { /* ignore init errors */ }
    },

    async choose(lang) {
      if (this.currentLang === lang) return;
      
      // Establecer cookie para TODOS los idiomas, no solo el default
      document.cookie = `lang=${lang}; path=/; max-age=31536000; SameSite=Lax`;
      
      if (lang === defaultLang) {
        window.location.href = getUrl(lang);
        return;
      }
      this.targetLang = lang;
      this.error = false;
      this.loading = true;

      const deadline = Date.now() + pollTimeout;
      try {
        const resp = await requestTranslation(pageKey, lang);
        if (!resp.ok) {
          // Server error (4xx, 5xx)
          this.error = true;
          this.loading = false;
          return;
        }
        const data = await resp.json();
        if (data.status === 'cached') {
          window.location.href = getUrl(lang);
        } else if (data.status === 'generating') {
          while (Date.now() < deadline) {
            await new Promise(r => setTimeout(r, pollInterval));
            try {
              const pr = await requestTranslation(pageKey, lang);
              if (!pr.ok) {
                // Stop polling on server errors (4xx, 5xx)
                this.error = true;
                this.loading = false;
                return;
              }
              const pd = await pr.json();
              if (pd.status === 'cached') { window.location.href = getUrl(lang); return; }
              if (pd.status !== 'generating') {
                // Unexpected status - stop polling
                this.error = true;
                this.loading = false;
                return;
              }
            } catch (e) {
              // Network error - stop polling
              this.error = true;
              this.loading = false;
              return;
            }
          }
          this.error = true;
          this.loading = false;
        } else {
          this.error = true;
          this.loading = false;
        }
      } catch {
        this.error = true;
        this.loading = false;
      }
    },

    retry() {
      if (this.targetLang) this.choose(this.targetLang);
    },
  };
}
