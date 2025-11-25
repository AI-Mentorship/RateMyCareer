// Global fetch wrapper: emits window events for loading start/end and tracks concurrent requests.
(() => {
  if (typeof window === 'undefined' || !window.fetch) return;

  const originalFetch = window.fetch.bind(window);
  let inFlight = 0;

  function emitStart() {
    try { window.dispatchEvent(new CustomEvent('app:loadingStart', { detail: { inFlight } })); } catch(e){}
  }
  function emitEnd() {
    try { window.dispatchEvent(new CustomEvent('app:loadingEnd', { detail: { inFlight } })); } catch(e){}
  }

  window.fetch = async function (...args) {
    // Increment and emit
    inFlight += 1;
    emitStart();
    try {
      const res = await originalFetch(...args);
      return res;
    } catch (e) {
      throw e;
    } finally {
      // Decrement after microtask to allow callers to await response.json() etc.
      setTimeout(() => {
        inFlight = Math.max(0, inFlight - 1);
        emitEnd();
      }, 0);
    }
  }

})();

export default null;
