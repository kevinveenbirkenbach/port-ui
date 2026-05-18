import unittest
from unittest.mock import Mock, patch

import requests

from app.utils.asset_resolver import (
    _probe_image_url,
    asset_src,
    resolve_asset_cache,
)


def _url_for_static(filename):
    return f"/static/{filename}"


def _always_probes_false(_url):
    return False


def _always_probes_true(_url):
    return True


class TestResolveAssetCache(unittest.TestCase):
    def test_probe_success_skips_cache_and_embeds_directly(self):
        cache_manager = Mock()
        asset = {"source": "https://example.test/logo.png"}

        resolve_asset_cache(asset, cache_manager, probe=_always_probes_true)

        self.assertIsNone(asset["cache"])
        self.assertEqual(asset["external_url"], "https://example.test/logo.png")
        cache_manager.cache_file.assert_not_called()

    def test_local_cache_path_assigned_when_probe_fails_but_download_succeeds(self):
        cache_manager = Mock()
        cache_manager.cache_file.return_value = "cache/logo_abc.png"
        asset = {"source": "https://example.test/logo.png"}

        resolve_asset_cache(asset, cache_manager, probe=_always_probes_false)

        self.assertEqual(asset["cache"], "cache/logo_abc.png")
        self.assertIsNone(asset["external_url"])
        cache_manager.cache_file.assert_called_once_with(
            "https://example.test/logo.png"
        )

    def test_external_url_fallback_when_probe_and_download_both_fail(self):
        cache_manager = Mock()
        cache_manager.cache_file.return_value = None
        asset = {"source": "https://file.infinito.nexus/assets/img/logo.png"}

        resolve_asset_cache(asset, cache_manager, probe=_always_probes_false)

        self.assertIsNone(asset["cache"])
        self.assertEqual(
            asset["external_url"],
            "https://file.infinito.nexus/assets/img/logo.png",
        )

    def test_missing_source_leaves_both_fields_none(self):
        cache_manager = Mock()
        probe = Mock()
        asset = {"class": "fa-solid fa-link"}

        resolve_asset_cache(asset, cache_manager, probe=probe)

        self.assertIsNone(asset["cache"])
        self.assertIsNone(asset["external_url"])
        cache_manager.cache_file.assert_not_called()
        probe.assert_not_called()

    def test_empty_source_treated_as_missing(self):
        cache_manager = Mock()
        probe = Mock()
        asset = {"source": ""}

        resolve_asset_cache(asset, cache_manager, probe=probe)

        self.assertIsNone(asset["cache"])
        self.assertIsNone(asset["external_url"])
        cache_manager.cache_file.assert_not_called()
        probe.assert_not_called()


class TestProbeImageUrl(unittest.TestCase):
    def _response(self, content_type, raise_exc=None):
        resp = Mock()
        if raise_exc:
            resp.raise_for_status.side_effect = raise_exc
        else:
            resp.raise_for_status.return_value = None
        resp.headers = {"Content-Type": content_type}
        return resp

    @patch("app.utils.asset_resolver.requests.head")
    def test_returns_true_for_image_content_type(self, mock_head):
        mock_head.return_value = self._response("image/png")

        self.assertTrue(_probe_image_url("https://example.test/logo.png"))

    @patch("app.utils.asset_resolver.requests.head")
    def test_returns_true_for_svg_with_charset_suffix(self, mock_head):
        mock_head.return_value = self._response("image/svg+xml; charset=utf-8")

        self.assertTrue(_probe_image_url("https://example.test/logo.svg"))

    @patch("app.utils.asset_resolver.requests.head")
    def test_returns_false_for_non_image_content_type(self, mock_head):
        mock_head.return_value = self._response("text/html")

        self.assertFalse(_probe_image_url("https://example.test/404"))

    @patch("app.utils.asset_resolver.requests.head")
    def test_returns_false_when_http_status_not_ok(self, mock_head):
        mock_head.return_value = self._response(
            "image/png",
            raise_exc=requests.HTTPError("404 Not Found"),
        )

        self.assertFalse(_probe_image_url("https://example.test/missing.png"))

    @patch("app.utils.asset_resolver.requests.head")
    def test_returns_false_on_network_error(self, mock_head):
        mock_head.side_effect = requests.ConnectionError("dns failure")

        self.assertFalse(_probe_image_url("https://unreachable.test/logo.png"))

    @patch("app.utils.asset_resolver.requests.head")
    def test_follows_redirects_with_short_timeout(self, mock_head):
        mock_head.return_value = self._response("image/png")

        _probe_image_url("https://example.test/logo.png")

        mock_head.assert_called_once_with(
            "https://example.test/logo.png",
            allow_redirects=True,
            timeout=3,
        )


class TestAssetSrc(unittest.TestCase):
    def test_returns_static_url_for_local_cache_path(self):
        asset = {"cache": "cache/logo_abc.png", "external_url": None}

        self.assertEqual(
            asset_src(asset, _url_for_static),
            "/static/cache/logo_abc.png",
        )

    def test_returns_absolute_url_unchanged_for_external_url(self):
        # Regression: previously the template wrapped this through
        # url_for('static', ...) and produced /static/https://... — a
        # URL-in-URL the browser resolved against the dashboard host.
        asset = {
            "cache": None,
            "external_url": "https://file.infinito.nexus/assets/img/logo.png",
        }

        self.assertEqual(
            asset_src(asset, _url_for_static),
            "https://file.infinito.nexus/assets/img/logo.png",
        )

    def test_external_url_wins_over_cache_when_both_present(self):
        asset = {
            "cache": "cache/logo.png",
            "external_url": "https://override.test/logo.png",
        }

        self.assertEqual(
            asset_src(asset, _url_for_static),
            "https://override.test/logo.png",
        )

    def test_returns_empty_string_when_neither_field_is_set(self):
        asset = {"cache": None, "external_url": None}

        self.assertEqual(asset_src(asset, _url_for_static), "")

    def test_returns_empty_string_for_none_or_empty_asset(self):
        self.assertEqual(asset_src(None, _url_for_static), "")
        self.assertEqual(asset_src({}, _url_for_static), "")


if __name__ == "__main__":
    unittest.main()
