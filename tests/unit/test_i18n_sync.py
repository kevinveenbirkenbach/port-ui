import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import yaml

from app.utils import i18n
from utils import i18n_sync


class TestCollectSources(unittest.TestCase):
    def test_prose_keys_are_collected_from_nested_structures(self):
        config = {
            "cards": [
                {"title": "Agile Coach", "text": "I lead transformations."},
                {"text": "Another card."},
            ],
            "navigation": {
                "header": {
                    "children": [
                        {"name": "Apps", "description": "Application menu"},
                    ]
                }
            },
            "platform": {"titel": "Someone", "subtitel": "A tagline"},
        }

        self.assertEqual(
            i18n_sync.collect_sources(config),
            {
                "I lead transformations.",
                "Another card.",
                "Application menu",
                "A tagline",
            },
        )

    def test_label_and_structural_keys_are_left_alone(self):
        config = {
            "name": "Mastodon",
            "title": "Cybermaster",
            "url": "https://example.test",
            "link_text": "www.example.test",
        }

        self.assertEqual(i18n_sync.collect_sources(config), set())

    def test_blank_values_are_ignored(self):
        self.assertEqual(i18n_sync.collect_sources({"text": "   "}), set())


class TestTranslate(unittest.TestCase):
    def _session(self, ok, payload=None, status=200, text=""):
        response = Mock(ok=ok, status_code=status, text=text)
        response.json.return_value = payload or {}
        return Mock(post=Mock(return_value=response))

    def test_successful_response_returns_the_translation(self):
        session = self._session(True, {"translatedText": "Hallo"})

        result = i18n_sync.translate(session, "http://lt", "", "Hello", "de")

        self.assertEqual(result, "Hallo")

    def test_api_key_is_only_sent_when_configured(self):
        session = self._session(True, {"translatedText": "Hallo"})

        i18n_sync.translate(session, "http://lt", "secret", "Hello", "de")

        self.assertEqual(session.post.call_args.kwargs["data"]["api_key"], "secret")

    def test_no_api_key_is_sent_when_none_is_configured(self):
        session = self._session(True, {"translatedText": "Hallo"})

        i18n_sync.translate(session, "http://lt", "", "Hello", "de")

        self.assertNotIn("api_key", session.post.call_args.kwargs["data"])

    def test_failed_response_returns_none(self):
        session = self._session(False, status=403, text="denied")

        self.assertIsNone(i18n_sync.translate(session, "http://lt", "", "Hi", "de"))

    def test_a_non_json_success_response_returns_none(self):
        response = Mock(ok=True)
        response.json.side_effect = ValueError("no json")
        session = Mock(post=Mock(return_value=response))

        self.assertIsNone(i18n_sync.translate(session, "http://lt", "", "Hi", "de"))

    def test_a_transport_failure_returns_none(self):
        session = Mock(
            post=Mock(side_effect=i18n_sync.requests.ConnectionError("reset"))
        )

        self.assertIsNone(i18n_sync.translate(session, "http://lt", "", "Hi", "de"))

    def test_a_non_string_translation_is_refused(self):
        session = self._session(True, {"translatedText": ["Hallo", "Welt"]})

        self.assertIsNone(i18n_sync.translate(session, "http://lt", "", "Hi", "de"))


class TestSupportedLanguages(unittest.TestCase):
    def _session(self, payload=None, side_effect=None):
        response = Mock(raise_for_status=Mock())
        if side_effect is not None:
            response.json.side_effect = side_effect
        else:
            response.json.return_value = payload
        return Mock(get=Mock(return_value=response))

    def test_the_offered_codes_are_returned(self):
        session = self._session([{"code": "de"}, {"code": "fr"}])

        self.assertEqual(
            i18n_sync.supported_languages("http://lt", session), {"de", "fr"}
        )

    def test_an_unreachable_instance_is_reported(self):
        session = Mock(get=Mock(side_effect=i18n_sync.requests.ConnectTimeout("slow")))

        with self.assertRaises(i18n_sync.BackendError):
            i18n_sync.supported_languages("http://lt", session)

    def test_a_non_json_listing_is_reported(self):
        session = self._session(side_effect=ValueError("no json"))

        with self.assertRaises(i18n_sync.BackendError):
            i18n_sync.supported_languages("http://lt", session)

    def test_json_of_the_wrong_shape_is_reported(self):
        for payload in ({"error": "Slow down"}, ["de", "fr"], None, [{"name": "de"}]):
            with self.subTest(payload=payload):
                with self.assertRaises(i18n_sync.BackendError):
                    i18n_sync.supported_languages("http://lt", self._session(payload))


class TestLoadExisting(unittest.TestCase):
    def setUp(self):
        self.directory = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.directory, True)
        self.path = self.directory / "de.yaml"

    def test_a_missing_file_is_an_empty_catalog(self):
        self.assertEqual(i18n_sync.load_existing(self.path), {})

    def test_a_readable_catalog_is_returned(self):
        self.path.write_text("Hi: Hallo\n", encoding="utf-8")

        self.assertEqual(i18n_sync.load_existing(self.path), {"Hi": "Hallo"})

    def test_an_unparsable_catalog_is_refused(self):
        self.path.write_text('Hi: "unterminated\n', encoding="utf-8")

        self.assertIsNone(i18n_sync.load_existing(self.path))

    def test_a_non_mapping_catalog_is_refused(self):
        self.path.write_text("- a\n- b\n", encoding="utf-8")

        self.assertIsNone(i18n_sync.load_existing(self.path))

    def test_a_non_utf8_catalog_is_refused(self):
        self.path.write_bytes(b"\xffHi: Hallo\n")

        self.assertIsNone(i18n_sync.load_existing(self.path))

    def test_a_directory_at_the_catalog_path_is_refused(self):
        (self.directory / "sub.yaml").mkdir()

        self.assertIsNone(i18n_sync.load_existing(self.directory / "sub.yaml"))

    def test_an_empty_or_comment_only_catalog_is_an_empty_catalog(self):
        for text in ("", "\n\n", "# only a comment\n"):
            with self.subTest(text=text):
                self.path.write_text(text, encoding="utf-8")
                self.assertEqual(i18n_sync.load_existing(self.path), {})


class TestWriteCatalog(unittest.TestCase):
    def setUp(self):
        self.directory = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.directory, True)
        self.path = self.directory / "de.yaml"

    def test_the_catalog_is_written_and_no_scratch_file_is_left(self):
        i18n_sync.write_catalog(self.path, {"Hi": "Hallo"})

        self.assertEqual(
            yaml.safe_load(self.path.read_text(encoding="utf-8")), {"Hi": "Hallo"}
        )
        self.assertEqual([p.name for p in self.directory.iterdir()], ["de.yaml"])

    def test_a_write_that_dies_halfway_leaves_the_previous_catalog_intact(self):
        self.path.write_text("Hi: HAND-EDITED\n", encoding="utf-8")
        complete = Path.write_text

        def dies_halfway(target, data, *args, **kwargs):
            complete(target, data[: len(data) // 2], *args, **kwargs)
            raise OSError("no space left on device")

        with patch.object(Path, "write_text", dies_halfway):
            with self.assertRaises(OSError):
                i18n_sync.write_catalog(self.path, {"Hi": "machine", "Zebra": "Zebra"})

        self.assertEqual(self.path.read_text(encoding="utf-8"), "Hi: HAND-EDITED\n")


class TestSync(unittest.TestCase):
    def setUp(self):
        self.directory = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.directory, True)
        self.addCleanup(setattr, i18n, "CONTENT_DIR", i18n.CONTENT_DIR)
        i18n.CONTENT_DIR = self.directory
        self.path = self.directory / "de.yaml"

    def _run(self, sources, offered=("de",), translated="UEBERSETZT"):
        listing = Mock(raise_for_status=Mock())
        listing.json.return_value = [{"code": code} for code in offered]
        answer = Mock(ok=True)
        answer.json.return_value = {"translatedText": translated}
        session = Mock(get=Mock(return_value=listing), post=Mock(return_value=answer))

        with patch.object(i18n_sync.requests, "Session", return_value=session):
            i18n_sync.sync("http://lt", "", set(sources), ["de"], self.directory)
        return session

    def test_missing_entries_are_written(self):
        self._run(["Hello"])

        self.assertEqual(
            yaml.safe_load(self.path.read_text(encoding="utf-8")),
            {"Hello": "UEBERSETZT"},
        )

    def test_existing_entries_are_never_overwritten(self):
        self.path.write_text("Hello: HAND-EDITED\n", encoding="utf-8")

        session = self._run(["Hello", "World"])

        catalog = yaml.safe_load(self.path.read_text(encoding="utf-8"))
        self.assertEqual(catalog["Hello"], "HAND-EDITED")
        self.assertEqual(session.post.call_count, 1)

    def test_an_unparsable_catalog_is_left_alone(self):
        broken = 'Hello: "unterminated\n'
        self.path.write_text(broken, encoding="utf-8")

        session = self._run(["Hello"])

        self.assertEqual(self.path.read_text(encoding="utf-8"), broken)
        session.post.assert_not_called()

    def test_a_language_the_instance_does_not_offer_is_skipped(self):
        session = self._run(["Hello"], offered=("fr",))

        self.assertFalse(self.path.exists())
        session.post.assert_not_called()

    def test_a_run_that_translated_nothing_leaves_the_file_untouched(self):
        original = "# Reviewed by a native speaker, keep the order.\nZebra: Zebra\n"
        self.path.write_text(original, encoding="utf-8")

        self._run(["Hello"], translated=None)

        self.assertEqual(self.path.read_text(encoding="utf-8"), original)

    def test_a_string_the_shipped_catalog_covers_is_not_requested(self):
        ui = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, ui, True)
        self.addCleanup(setattr, i18n, "UI_DIR", i18n.UI_DIR)
        i18n.UI_DIR = ui
        (ui / "de.yaml").write_text("Close: Schliessen\n", encoding="utf-8")

        session = self._run(["Close", "Hello"])

        self.assertEqual(session.post.call_count, 1)
        self.assertNotIn("Close", yaml.safe_load(self.path.read_text(encoding="utf-8")))

    def test_the_catalog_directory_is_created(self):
        nested = self.directory / "content"
        self.directory = nested
        self.path = nested / "de.yaml"

        self._run(["Hello"])

        self.assertTrue(self.path.is_file())


if __name__ == "__main__":
    unittest.main()
