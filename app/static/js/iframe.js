// Global variables to store elements and original state
let mainElement, originalContent, originalMainStyle, container, customScrollbar, scrollbarContainer;
let currentIframeUrl = null;

// === Auto-open iframe if URL parameter is present ===
window.addEventListener('DOMContentLoaded', () => {
  const paramUrl = new URLSearchParams(window.location.search).get('iframe');
  if (paramUrl) {
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

// Function to open a URL in an iframe (jQuery version mit 1500 ms Fade)
function openIframe(url) {
    if (!isSafeUrl(url)) {
        return;
    }

    var $container    = scrollbarContainer    ? $(scrollbarContainer)    : null;
    var $customScroll = customScrollbar       ? $(customScrollbar)       : null;
    var $main         = $(mainElement);

    // Original-Content ausblenden mit 1500 ms
    var promises = [];
    if ($container)    promises.push($container.fadeOut(1500).promise());
    if ($customScroll) promises.push($customScroll.fadeOut(1500).promise());

    $.when.apply($, promises).done(function() {
        // now that scroll areas are hidden, go fullscreen
        enterFullscreen();
        // create iframe if it doesn’t exist yet
        var $iframe = $main.find('iframe');
        if ($iframe.length === 0) {
            originalMainStyle = $main.attr('style') || null;
            $iframe = $('<iframe>', {
                width: '100%',
                frameborder: 0,
                scrolling: 'auto'
            }).css({ overflow: 'auto', display: 'none' });
            $main.append($iframe);
        }

        // Quelle setzen und mit 1500 ms einblenden
        $iframe
            .attr('src', url)
            .fadeIn(1500, function() {
                syncIframeHeight();
                observeIframeNavigation();
            });

        // URL-State pushen
        var newUrl = new URL(window.location);
        newUrl.searchParams.set('iframe', url);
        window.history.pushState({ iframe: url }, '', newUrl);
    });
}

/**
 * Restore the original <main> content and exit fullscreen.
 */
function restoreOriginal() {
  // Exit fullscreen (collapse header/footer and run recalcs)
  exitFullscreen();

  // Replace <main> innerHTML with the snapshot we took on load
  mainElement.innerHTML = originalContent;

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
  history.replaceState(null, '', window.location.pathname);
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
        history.replaceState(null, '', window.location.pathname);
      });
    });

});

/**
 * Opens the current iframe URL in a new browser tab.
 */
function openIframeInNewTab() {
  const params = new URLSearchParams(window.location.search);
  const iframeUrl = params.get('iframe');
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

  let lastUrl = iframe.contentWindow.location.href;

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

// Remember, open iframe, enter fullscreen, AND set the URL param immediately
document.querySelectorAll(".iframe-link").forEach(link => {
  link.addEventListener("click", function(event) {
    event.preventDefault();
    currentIframeUrl = this.href;

    enterFullscreen();
    openIframe(currentIframeUrl);

    // Update the browser URL right away
    const newUrl = new URL(window.location);
    newUrl.searchParams.set('iframe', currentIframeUrl);
    window.history.replaceState({ iframe: currentIframeUrl }, '', newUrl);
  });
});
