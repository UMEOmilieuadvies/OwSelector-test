'use strict';
/* Zuivere weergavefragmenten voor de documentviewer. */
(() => {
  function breadcrumbs(trail, {label, regName, esc}) {
    return trail.map((node, index) => {
      const prefix = index === 0 || trail[index - 1]?.regId !== node.regId ? `${regName(node.regId)} — ` : '';
      const text = esc(prefix + label(node));
      return index === trail.length - 1
        ? `<div class="breadcrumbStep current"><span>${text}</span></div>`
        : `<div class="breadcrumbStep"><button data-crumb="${index}">${text}</button></div>`;
    }).join('');
  }
  function referenceNotice(text, esc) {
    return text ? `<div class="referenceArticleContext">${esc(text)} De vindplaats is hieronder gemarkeerd.</div>` : '';
  }
  globalThis.OWZ_VIEWER = Object.freeze({breadcrumbs, referenceNotice});
})();
