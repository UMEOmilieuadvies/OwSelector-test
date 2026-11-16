'use strict';
/* Zuivere navigatieregels: geen DOM of applicatiestatus. */
(() => {
  function roots(nodes, parentId, type) {
    return [...nodes].filter(node => !parentId(node) && ['chapter','appendix'].includes(type(node)));
  }
  function visibleChildren(node, children, type) {
    if (type(node) === 'article') return [];
    return children(node).filter(child => ['chapter','section','paragraph','subparagraph','article'].includes(type(child)));
  }
  globalThis.OWZ_NAVIGATION = Object.freeze({roots, visibleChildren});
})();
