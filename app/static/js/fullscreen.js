/**
 * Add or remove the `fullscreen=1` URL parameter.
 * @param {boolean} enabled
 */
function updateUrlFullscreen(enabled) {
  var url = new URL(window.location);
  if (enabled) url.searchParams.set('fullscreen', '1');
  else         url.searchParams.delete('fullscreen');
  window.history.replaceState({}, '', url);
}

function recalcWhileCollapsing() {
  const header = document.querySelector('header');
  if (!header) return;

  const step = () => {
    adjustScrollContainerHeight();
    updateCustomScrollbar();
    if (header.getAnimations().length > 0) requestAnimationFrame(step);
  };
  step();
}

function enterFullscreen() {
  document.body.classList.add('fullscreen');
  setFullWidth(true);
  updateUrlFullscreen(true);

  // Nur jetzt sichtbar machen
  const logo = document.getElementById('navbar_logo');
  if (logo) {
    logo.classList.add('visible');
  }
  recalcWhileCollapsing();
}

function exitFullscreen() {
  document.body.classList.remove('fullscreen');
  setFullWidth(false);
  updateUrlFullscreen(false);

  // Jetzt wieder verstecken
  const logo = document.getElementById('navbar_logo');
  if (logo) {
    logo.classList.remove('visible');
  }
  recalcWhileCollapsing();
}

/**
 * Toggle between enter and exit fullscreen.
 */
function toggleFullscreen() {
  const params = new URLSearchParams(window.location.search);
  const isFull = params.get('fullscreen') === '1';

  if (isFull) exitFullscreen();
  else        enterFullscreen();
}

/**
 * Read `fullscreen` flag from URL on load.
 * @returns {boolean}
 */
function initFullscreenFromUrl() {
  return new URLSearchParams(window.location.search).get('fullscreen') === '1';
}

// On page load: apply fullwidth & fullscreen flags
window.addEventListener('DOMContentLoaded', function() {
  // first fullwidth
  var wasFullWidth = initFullWidthFromUrl();
  setFullWidth(wasFullWidth);

  // now fullscreen
  if (initFullscreenFromUrl()) {
    enterFullscreen();
  }
});

// Mirror native F11/fullscreen API events
document.addEventListener('fullscreenchange', function() {
  if (document.fullscreenElement) enterFullscreen();
  else                            exitFullscreen();
});
window.addEventListener('resize', function() {
  var isUiFs = Math.abs(window.innerHeight - screen.height) < 2;
  if (isUiFs === document.body.classList.contains('fullscreen')) return;
  if (isUiFs) enterFullscreen();
  else         exitFullscreen();
});

// Expose globally
window.fullscreen       = enterFullscreen;
window.exitFullscreen   = exitFullscreen;
window.toggleFullscreen = toggleFullscreen;
