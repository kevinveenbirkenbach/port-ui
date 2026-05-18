"""Live network verification of the probe-first asset resolution path.

The unit tests in ``tests/unit/test_asset_resolver.py`` cover every
branch with mocks. This integration test exercises the real
``https://file.infinito.nexus/assets/img/logo.png`` endpoint that
``app/config.sample.yaml`` references for the Infinito.Nexus card. A
green run proves the production resolver behaviour end-to-end:

* probe (HEAD ``image/*``) succeeds against the canonical Infinito.Nexus
  asset host, so ``external_url`` is populated directly and **no**
  download is performed (the cache directory stays empty).

The download-fallback branch (probe fails → ``cache_manager.cache_file``
serves the asset locally) is intentionally not exercised against a live
endpoint here — it is covered by mocked unit tests because every
candidate "HEAD-fails, GET-succeeds" public URL we tried was flaky
(Nextcloud's ``/download`` endpoint sporadically times out on HEAD even
when GET works), which would make this guard test non-deterministic.
"""

from __future__ import annotations

import os
import unittest
from tempfile import TemporaryDirectory
from urllib.parse import urlparse

import requests

from app.utils.asset_resolver import resolve_asset_cache
from app.utils.cache_manager import CacheManager

INFINITO_LOGO_URL = "https://file.infinito.nexus/assets/img/logo.png"

_SKIP_LIVE_NETWORK = os.environ.get("PORTFOLIO_SKIP_LIVE_NETWORK_TESTS") == "1"


def _reachable(url: str) -> bool:
    try:
        return requests.head(url, allow_redirects=True, timeout=5).ok
    except requests.RequestException:
        return False


@unittest.skipIf(
    _SKIP_LIVE_NETWORK,
    "PORTFOLIO_SKIP_LIVE_NETWORK_TESTS=1 — skipping live network tests",
)
class TestAssetResolverLive(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not _reachable(INFINITO_LOGO_URL):
            raise unittest.SkipTest(
                f"{urlparse(INFINITO_LOGO_URL).netloc} unreachable from this runner"
            )

    def test_infinito_nexus_logo_resolves_via_external_url_without_download(self):
        with TemporaryDirectory() as tmp:
            cache_dir = os.path.join(tmp, "cache")
            cache_manager = CacheManager(cache_dir)
            asset = {"source": INFINITO_LOGO_URL}

            resolve_asset_cache(asset, cache_manager)

            self.assertIsNone(
                asset["cache"],
                f"Expected probe-first path to skip download for {INFINITO_LOGO_URL}",
            )
            self.assertEqual(
                asset["external_url"],
                INFINITO_LOGO_URL,
                "Probe-success URL must land in external_url so the template "
                "embeds it directly instead of routing through /static/.",
            )
            self.assertEqual(
                os.listdir(cache_dir),
                [],
                "Cache directory must stay empty when probe succeeds — "
                "downloading would waste bandwidth.",
            )


if __name__ == "__main__":
    unittest.main()
