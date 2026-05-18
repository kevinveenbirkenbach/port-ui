"""Split asset resolution into distinct fields so the template can
render the right URL.

Strategy
--------

1. **Probe** the source URL with a HEAD request. If it responds with an
   ``image/*`` content type, embed it directly via ``external_url``
   (no download necessary — the browser fetches it itself).
2. **Cache** as a fallback: when the probe fails (404, non-image,
   network error, …) try ``cache_manager.cache_file()`` to download
   and serve via ``/static/cache/<file>``.
3. **External fallback**: if the download fails too, still expose the
   source URL via ``external_url`` so the browser shows at least the
   alt-text or broken-image icon instead of an empty ``src``.

Type safety
-----------

``cache`` only ever holds a relative path the static handler can serve;
absolute URLs land in ``external_url`` and are rendered as-is. The
previous fallback ``asset['cache'] = cached or asset['source']`` mixed
both shapes — and the template's ``url_for('static', filename=...)``
wrapper produced broken ``/static/https://…`` URLs when the source
was an absolute URL the container couldn't fetch.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Optional

import requests

_PROBE_TIMEOUT_SECONDS = 3


def _probe_image_url(url: str) -> bool:
    """Return True if a HEAD request to ``url`` succeeds with an
    ``image/*`` content type, suggesting the URL is safe to embed
    directly as ``<img src>``."""
    try:
        resp = requests.head(url, allow_redirects=True, timeout=_PROBE_TIMEOUT_SECONDS)
        resp.raise_for_status()
    except requests.RequestException:
        return False
    content_type = resp.headers.get("Content-Type", "").lower()
    return content_type.split(";", 1)[0].strip().startswith("image/")


def resolve_asset_cache(
    asset: dict,
    cache_manager,
    probe: Callable[[str], bool] = _probe_image_url,
) -> None:
    """Set ``asset['cache']`` (local, served via /static/) or
    ``asset['external_url']`` (rendered as-is). Never both.

    Tries the cheap direct-embed path first (``probe``) before falling
    back to downloading via ``cache_manager``. See module docstring."""
    source = asset.get("source")
    asset["cache"] = None
    asset["external_url"] = None
    if not source:
        return
    if probe(source):
        asset["external_url"] = source
        return
    cached = cache_manager.cache_file(source)
    if cached:
        asset["cache"] = cached
    else:
        asset["external_url"] = source


def asset_src(asset: Optional[dict], url_for_static: Callable[[str], str]) -> str:
    """Return the final URL for an asset dict prepared by
    :func:`resolve_asset_cache`. ``url_for_static`` is a callable that
    maps a relative cache path to its served URL (typically a partial
    of Flask's ``url_for('static', filename=...)``)."""
    if not asset:
        return ""
    external = asset.get("external_url")
    if external:
        return external
    cached = asset.get("cache")
    if cached:
        return url_for_static(cached)
    return ""
