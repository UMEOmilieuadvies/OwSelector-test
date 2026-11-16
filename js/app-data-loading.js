'use strict';
/* Centrale, testbare laadregels voor statische juridische gegevens. */
(() => {
  async function json(path, options = {}) {
    const response = await fetch(path, {cache:'no-store', ...options});
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return response.json();
  }
  async function regulations(regulations, load) {
    return Promise.all(regulations.map(async regulation => {
      try { await load(regulation); return {regulation, ok:true}; }
      catch (error) { return {regulation, ok:false, error}; }
    }));
  }
  globalThis.OWZ_DATA_LOADING = Object.freeze({json, regulations});
})();
