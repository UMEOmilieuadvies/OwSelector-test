'use strict';
/*
 * Kleine, zuivere gedragslaag voor de hoofdapplicatie.
 *
 * Deze functies kennen geen DOM, netwerk of opslag. Daardoor zijn de
 * kritieke regels voor favorieten, zoekgeschiedenis en terugverwijzingen
 * afzonderlijk te testen en kan app.js zich beperken tot bediening en weergave.
 */
(() => {
  function favoriteRecord(items, candidate) {
    const nodeId = String(candidate?.nodeId || '');
    const reg = String(candidate?.reg || '');
    if (!nodeId || !reg) return Array.isArray(items) ? [...items] : [];
    const current = Array.isArray(items) ? items.filter(item => item && item.nodeId && item.reg) : [];
    const index = current.findIndex(item => String(item.nodeId) === nodeId && String(item.reg) === reg);
    if (index >= 0) return current.filter((_, itemIndex) => itemIndex !== index);
    return [{nodeId, reg, label: String(candidate.label || '')}, ...current];
  }

  function historyRecord(items, candidate, limit) {
    const current = Array.isArray(items) ? items : [];
    const query = String(candidate?.query || '').trim();
    const reg = String(candidate?.reg || '').trim();
    if (!query || !reg) return [...current];
    const unique = current.filter(item => !(String(item?.query || '') === query && String(item?.reg || '') === reg));
    return [{query, reg, label: String(candidate.label || `${query} — ${reg}`)}, ...unique]
      .slice(0, Math.max(1, Number(limit) || 1));
  }

  function referenceContext(articleLabel, targetLabel, anchor) {
    const article = String(articleLabel || '').trim();
    const target = String(targetLabel || '').trim();
    const location = String(anchor || '').trim();
    if (!article || !target) return '';
    return `Dit volledige artikel (${article}) verwijst naar ${target}.${location ? ` Vindplaats: ${location}.` : ''}`;
  }

  globalThis.OWZ_BEHAVIOR = Object.freeze({favoriteRecord, historyRecord, referenceContext});
})();
