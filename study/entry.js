(function (root) {
  'use strict';
  function destination(href) {
    const current = new URL(href);
    // Explicit Task links keep opening the original C-Test trainer.
    if (current.searchParams.has('task') || current.searchParams.has('classic')) return null;
    return new URL('study/index.html', current).href;
  }
  if (typeof module === 'object' && module.exports) module.exports = destination;
  else {
    const target = destination(root.location.href);
    if (target) root.location.replace(target);
  }
})(typeof window === 'object' ? window : globalThis);
