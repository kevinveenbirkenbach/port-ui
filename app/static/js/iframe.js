// Global variables to store elements and original state
let mainElement, originalContent, originalMainStyle, container, customScrollbar, scrollbarContainer;
let currentIframeUrl = null;

function allowedIframeUrl(url) {
  const candidate = safeUrl(url);
  if (candidate === null) {
    return null;
  }
  const allowedOrigins = new Set([window.location.origin]);
  document.querySelectorAll('a.iframe-link[href]').forEach((link) => allowedOrigins.add(link.origin));
  return allowedOrigins.has(new URL(candidate).origin) ? candidate : null;
}

// === Auto-open iframe if URL parameter is present ===
window.addEventListener('DOMContentLoaded', () => {
  const paramUrl = new URLSearchParams(window.location.search).get('iframe');
  if (paramUrl && allowedIframeUrl(paramUrl)) {
    currentIframeUrl = paramUrl;
    enterFullscreen();
    openIframe(paramUrl);
  }
});

// Synchronize the height of the iframe to match the scroll-container or main element
function syncIframeHeight() {
    const iframe = mainElement.querySelector("iframe");
    if (iframe) {
        if (scrollbarContainer) {
            // Prefer inline height, otherwise inline max-height
            const inlineHeight = scrollbarContainer.style.height;
            const inlineMax = scrollbarContainer.style.maxHeight;
            const target = inlineHeight || inlineMax;
            if (target) {
                iframe.style.height = target;
            } else {
                iframe.style.height = mainElement.style.height;
            }
        } else {
            iframe.style.height = mainElement.style.height;
        }
    }
}

let openToken = 0;
let openPending = false;

// A fresh element per target: changing src on a live iframe adds a joint session history entry, so Back would step the frame instead of the page.
function frameFor(target, visible) {
    return $('<iframe>', {
        width: '100%',
        frameborder: 0,
        scrolling: 'auto',
        src: target
    }).css({ overflow: 'auto', display: visible ? '' : 'none' });
}

function cancelPendingOpen() {
    openToken += 1;
    openPending = false;
    if (scrollbarContainer) $(scrollbarContainer).stop(true);
    if (customScrollbar) $(customScrollbar).stop(true);
}

// Function to open a URL in an iframe (jQuery version mit 1500 ms Fade)
function openIframe(url) {
    const target = safeUrl(url);
    if (target === null) {
        return;
    }

    var $container    = scrollbarContainer    ? $(scrollbarContainer)    : null;
    var $customScroll = customScrollbar       ? $(customScrollbar)       : null;
    var $main         = $(mainElement);
    var token         = ++openToken;
    openPending = true;

    // Original-Content ausblenden mit 1500 ms
    var promises = [];
    if ($container)    promises.push($container.fadeOut(1500).promise());
    if ($customScroll) promises.push($customScroll.fadeOut(1500).promise());

    $.when.apply($, promises).done(function() {
        if (token !== openToken) {
            return;
        }
        openPending = false;
        // now that scroll areas are hidden, go fullscreen
        enterFullscreen();
        var $old = $main.find('iframe');
        if ($old.length === 0) {
            originalMainStyle = $main.attr('style') || null;
        }
        var $iframe = frameFor(target, $old.length > 0);
        if ($old.length) {
            $old.replaceWith($iframe);
        } else {
            $main.append($iframe);
        }

        $iframe
            .fadeIn(1500, function() {
                syncIframeHeight();
                observeIframeNavigation();
            });

        // URL-State pushen
        var newUrl = new URL(window.location);
        var alreadyListed = newUrl.searchParams.get('iframe') === url;
        newUrl.searchParams.set('iframe', url);
        if (alreadyListed) {
            window.history.replaceState({ iframe: url }, '', newUrl);
        } else {
            window.history.pushState({ iframe: url }, '', newUrl);
        }
    });
}

/**
 * Restore the original <main> content and exit fullscreen.
 */
function restoreOriginal() {
  cancelPendingOpen();
  // Exit fullscreen (collapse header/footer and run recalcs)
  exitFullscreen();

  // Replace <main> innerHTML with the snapshot we took on load
  mainElement.innerHTML = originalContent;
  scrollbarContainer = container.querySelector(".scroll-container");
  if (customScrollbar) customScrollbar.style.display = '';

  // Reset any inline styles on mainElement
  if (originalMainStyle !== null) {
    mainElement.setAttribute('style', originalMainStyle);
  } else {
    mainElement.removeAttribute('style');
  }

  // Re-run height adjustments for scroll container & thumb
  adjustScrollContainerHeight();
  updateCustomScrollbar();

  // Clear iframe state and URL param
  currentIframeUrl = null;
  dropIframeParam();
  document.dispatchEvent(new CustomEvent('portui:restored'));
}

function dropIframeParam() {
  const url = new URL(window.location);
  url.searchParams.delete('iframe');
  history.replaceState(history.state, '', url);
}

// Initialize event listeners after DOM content is loaded
document.addEventListener("DOMContentLoaded", function() {
    // Cache references to elements and original state
    mainElement = document.querySelector("main");
    originalContent = mainElement.innerHTML;
    originalMainStyle = mainElement.getAttribute("style");  // may be null
    container = document.querySelector(".container");
    customScrollbar = document.getElementById("custom-scrollbar");
    scrollbarContainer = container.querySelector(".scroll-container")

    document.querySelectorAll(".js-restore").forEach(el => {
        el.style.cursor = "pointer";
        el.addEventListener("click", restoreOriginal);
    });

    // === Close iframe & exit fullscreen when any .js-restore is clicked ===
    document.querySelectorAll('.js-restore').forEach(el => {
      el.style.cursor = 'pointer';
      el.addEventListener('click', () => {
        // first collapse header/footer and recalc container
        exitFullscreen();
        // then fade out and remove the iframe, fade content back
        restoreOriginal();
        // clear stored URL and reset browser address
        currentIframeUrl = null;
        dropIframeParam();
      });
    });

});

/**
 * Opens the current iframe URL in a new browser tab.
 */
function openIframeInNewTab() {
  const params = new URLSearchParams(window.location.search);
  const iframeUrl = allowedIframeUrl(params.get('iframe'));
  if (iframeUrl) {
    window.open(iframeUrl, '_blank');
  } else {
    alert('No iframe is currently open.');
  }
}
// expose globally so your template’s onclick can find it
window.openIframeInNewTab = openIframeInNewTab;

// Adjust iframe height on window resize
window.addEventListener('resize', syncIframeHeight);

/**
 * Observe iframe location changes (Same-Origin only).
 */
function observeIframeNavigation() {
  const iframe = mainElement.querySelector("iframe");
  if (!iframe || !iframe.contentWindow) return;

  let lastUrl;
  try {
    lastUrl = iframe.contentWindow.location.href;
  } catch (e) {
    return;
  }

  setInterval(() => {
    try {
      const currentUrl = iframe.contentWindow.location.href;
      if (currentUrl !== lastUrl) {
        lastUrl = currentUrl;
        const newUrl = new URL(window.location);
        newUrl.searchParams.set('iframe', currentUrl);
        window.history.replaceState({}, '', newUrl);
      }
    } catch (e) {
      // Cross-origin – ignore
    }
  }, 500);
}

// Capture phase and delegated: navigation.js stops propagation inside dropdowns, restoreOriginal() rebuilds <main>, and the dashboard clones tiles after load.
document.addEventListener("click", function(event) {
  const link = event.target.closest(".iframe-link");
  if (!link || event.defaultPrevented || event.button !== 0 || event.ctrlKey || event.metaKey || event.shiftKey) {
    return;
  }
  event.preventDefault();
  currentIframeUrl = link.href;

  const newUrl = new URL(window.location);
  newUrl.searchParams.set('iframe', currentIframeUrl);
  window.history.pushState({ iframe: currentIframeUrl }, '', newUrl);

  enterFullscreen();
  openIframe(currentIframeUrl);
}, true);

window.addEventListener('popstate', function() {
  const wanted = allowedIframeUrl(new URLSearchParams(window.location.search).get('iframe'));
  const frame = mainElement.querySelector('iframe');
  if (wanted === null) {
    if (frame || openPending) {
      restoreOriginal();
    }
    return;
  }
  currentIframeUrl = wanted;
  if (frame) {
    if (frame.getAttribute('src') !== wanted) {
      const $fresh = frameFor(wanted, true);
      $(frame).replaceWith($fresh);
      syncIframeHeight();
    }
    return;
  }
  if (!openPending) {
    enterFullscreen();
    openIframe(new URLSearchParams(window.location.search).get('iframe'));
  }
});
