import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

app_module = None
flask_app = None
i18n = None
_origin = None
_workdir = None


def setUpModule():
    """Import the app with a disposable configuration as the working directory.

    ``app.app`` reads ``config.yaml`` relative to the process working directory
    at import time, so the chdir has to happen before the import.
    """
    global app_module, flask_app, i18n, _origin, _workdir

    _origin = os.getcwd()
    _workdir = tempfile.mkdtemp(prefix="portfolio-routes-")
    shutil.copy(
        REPO_ROOT / "app" / "config.sample.yaml", Path(_workdir) / "config.yaml"
    )
    os.chdir(_workdir)

    from app import app as imported_module
    from app.utils import i18n as imported_i18n

    app_module = imported_module
    flask_app = imported_module.app
    i18n = imported_i18n
    flask_app.config["NASA_API_KEY"] = None


def tearDownModule():
    os.chdir(_origin)
    shutil.rmtree(_workdir, ignore_errors=True)


class AppRouteMixin:
    """Shared setup. A mixin rather than a TestCase subclass, so that every
    test class below still names ``unittest.TestCase`` as a direct base — the
    lint guardrail in tests/lint/ does not resolve inherited aliases."""

    def setUp(self):
        self.client = flask_app.test_client()
        self.addCleanup(i18n.clear_catalogs)
        self.addCleanup(flask_app.config["TRANSLATED_CONFIG"].clear)


class TestRouting(AppRouteMixin, unittest.TestCase):
    def test_unrelated_single_segment_paths_are_not_redirected(self):
        for path in ("/robots.txt", "/favicon.ico", "/sitemap.xml"):
            with self.subTest(path=path):
                self.assertEqual(self.client.get(path).status_code, 404)

    def test_language_path_redirects_to_the_canonical_trailing_slash(self):
        response = self.client.get("/de")

        self.assertEqual(response.status_code, 308)
        self.assertTrue(response.headers["Location"].endswith("/de/"))

    def test_supported_language_renders(self):
        response = self.client.get("/de/")

        self.assertEqual(response.status_code, 200)
        self.assertIn('<html lang="de"', response.get_data(as_text=True))

    def test_unsupported_language_is_not_found(self):
        self.assertEqual(self.client.get("/xx/").status_code, 404)


class TestNegotiation(AppRouteMixin, unittest.TestCase):
    def test_regional_tag_beats_a_lower_ranked_exact_match(self):
        response = self.client.get("/", headers={"Accept-Language": "de-DE,en;q=0.8"})

        self.assertIn('<html lang="de"', response.get_data(as_text=True))

    def test_negotiated_route_declares_that_it_varies(self):
        response = self.client.get("/", headers={"Accept-Language": "de-DE"})

        self.assertEqual(response.headers.get("Vary"), "Accept-Language")


class TestEscaping(AppRouteMixin, unittest.TestCase):
    def test_catalog_content_is_html_escaped(self):
        i18n._catalogs["de"] = {"Imprint": "<script>alert(1)</script>"}

        body = self.client.get("/de/").get_data(as_text=True)

        self.assertNotIn("<script>alert(1)</script>", body)
        self.assertIn("&lt;script&gt;alert(1)", body)


class TestExternalUrls(AppRouteMixin, unittest.TestCase):
    def test_forwarded_scheme_reaches_the_canonical_and_alternates(self):
        body = self.client.get(
            "/en/",
            headers={"Host": "portfolio.example.org", "X-Forwarded-Proto": "https"},
        ).get_data(as_text=True)

        self.assertIn(
            '<link rel="canonical" href="https://portfolio.example.org/en/">', body
        )
        self.assertIn('hreflang="ja" href="https://portfolio.example.org/ja/"', body)
        self.assertNotIn("http://portfolio.example.org", body)

    def test_trusted_hosts_are_parsed_from_a_comma_separated_list(self):
        self.assertEqual(
            app_module.trusted_hosts("a.test, b.test ,"), ["a.test", "b.test"]
        )

    def test_an_unset_trusted_hosts_value_disables_the_check(self):
        self.assertIsNone(app_module.trusted_hosts(""))
        self.assertIsNone(app_module.trusted_hosts("  ,  "))

    def test_a_forged_host_is_rejected_once_trusted_hosts_are_named(self):
        self.addCleanup(flask_app.config.__setitem__, "TRUSTED_HOSTS", None)
        flask_app.config["TRUSTED_HOSTS"] = ["portfolio.example.org"]

        forged = self.client.get("/de", headers={"Host": "evil.test"})
        honest = self.client.get("/de/", headers={"Host": "portfolio.example.org"})

        self.assertEqual(forged.status_code, 400)
        self.assertEqual(honest.status_code, 200)

    def test_forwarded_host_is_not_trusted(self):
        response = self.client.get(
            "/de",
            headers={"Host": "portfolio.example.org", "X-Forwarded-Host": "evil.test"},
        )

        self.assertNotIn("evil.test", response.headers["Location"])

        body = self.client.get(
            "/en/",
            headers={"Host": "portfolio.example.org", "X-Forwarded-Host": "evil.test"},
        ).get_data(as_text=True)

        self.assertNotIn("evil.test", body)


class TestConfigurationReload(AppRouteMixin, unittest.TestCase):
    def test_reloading_the_configuration_drops_the_catalog_memo(self):
        i18n.catalog("de")
        self.assertIn("de", i18n._catalogs)

        app_module.load_config(flask_app)

        self.assertEqual(i18n._catalogs, {})

    def test_reloading_the_configuration_drops_the_translation_memo(self):
        self.client.get("/de/")
        self.assertIn("de", flask_app.config["TRANSLATED_CONFIG"])

        app_module.load_config(flask_app)

        self.assertEqual(flask_app.config["TRANSLATED_CONFIG"], {})


class TestTrustedHostsWiring(unittest.TestCase):
    def test_the_environment_reaches_the_flask_configuration(self):
        script = (
            "import json, sys;"
            f"sys.path.insert(0, {str(REPO_ROOT)!r});"
            "from app.app import app;"
            "print('TRUSTED=' + json.dumps(app.config['TRUSTED_HOSTS']))"
        )
        result = subprocess.run(
            [sys.executable, "-c", script],
            cwd=_workdir,
            env={**os.environ, "TRUSTED_HOSTS": "a.test, b.test"},
            capture_output=True,
            text=True,
            check=True,
        )

        reported = [
            line for line in result.stdout.splitlines() if line.startswith("TRUSTED=")
        ]
        self.assertEqual(
            json.loads(reported[-1][len("TRUSTED=") :]), ["a.test", "b.test"]
        )


if __name__ == "__main__":
    unittest.main()
