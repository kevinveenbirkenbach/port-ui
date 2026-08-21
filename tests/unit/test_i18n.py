import re
import shutil
import tempfile
import unittest
from pathlib import Path

import yaml

from app.utils import i18n


class TestNegotiate(unittest.TestCase):
    def test_regional_tag_beats_a_lower_ranked_exact_match(self):
        self.assertEqual(i18n.negotiate([("de-DE", 1.0), ("en", 0.8)]), "de")

    def test_underscore_separated_tag_is_accepted(self):
        self.assertEqual(i18n.negotiate([("pt_BR", 1.0)]), "pt")

    def test_highest_quality_supported_tag_wins(self):
        self.assertEqual(
            i18n.negotiate([("xx", 1.0), ("fr", 0.9), ("es", 0.5)]),
            "fr",
        )

    def test_unsupported_tags_fall_back_to_the_default(self):
        self.assertEqual(i18n.negotiate([("xx", 1.0)]), "en")
        self.assertEqual(i18n.negotiate([], default="de"), "de")

    def test_a_refused_language_is_not_selected(self):
        self.assertEqual(i18n.negotiate([("de", 0.0)]), "en")

    def test_the_first_of_two_equal_tags_wins(self):
        self.assertEqual(i18n.negotiate([("fr", 0.9), ("es", 0.9)]), "fr")


class TestDirection(unittest.TestCase):
    def test_every_right_to_left_language_is_marked(self):
        for code in ("ar", "fa", "he", "ur"):
            with self.subTest(code=code):
                self.assertEqual(i18n.direction(code), "rtl")

    def test_other_languages_are_left_to_right(self):
        for code in set(i18n.LANGUAGES) - {"ar", "fa", "he", "ur"}:
            with self.subTest(code=code):
                self.assertEqual(i18n.direction(code), "ltr")


class TestTranslateTree(unittest.TestCase):
    def setUp(self):
        self.addCleanup(i18n._catalogs.clear)
        i18n._catalogs["xx"] = {"A card": "Eine Karte", "Pictures": "Bilder"}

    def test_only_translatable_keys_are_replaced(self):
        tree = {
            "cards": [
                {
                    "title": "Pictures",
                    "text": "A card",
                    "url": "A card",
                    "icon": {"class": "Pictures"},
                }
            ]
        }

        translated = i18n.translate_tree(tree, "xx")

        card = translated["cards"][0]
        self.assertEqual(card["title"], "Bilder")
        self.assertEqual(card["text"], "Eine Karte")
        self.assertEqual(card["url"], "A card")
        self.assertEqual(card["icon"]["class"], "Pictures")

    def test_unknown_strings_keep_their_source_value(self):
        translated = i18n.translate_tree({"description": "Untranslated"}, "xx")

        self.assertEqual(translated["description"], "Untranslated")

    def test_source_tree_is_left_untouched(self):
        tree = {"name": "Pictures"}

        i18n.translate_tree(tree, "xx")

        self.assertEqual(tree["name"], "Pictures")

    def test_non_string_leaves_survive(self):
        tree = {"name": 1, "text": None, "info": True}

        self.assertEqual(i18n.translate_tree(tree, "xx"), tree)


class TestReadCatalog(unittest.TestCase):
    def setUp(self):
        self.directory = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.directory, True)
        self.path = self.directory / "de.yaml"

    def _read(self, text):
        self.path.write_text(text, encoding="utf-8")
        with self.assertLogs(level="WARNING"):
            return i18n.read_catalog(self.path)

    def test_absent_file_is_an_empty_catalog(self):
        self.assertEqual(i18n.read_catalog(self.directory / "missing.yaml"), {})

    def test_unparsable_yaml_is_an_empty_catalog(self):
        self.assertEqual(self._read("Close: [unclosed"), {})

    def test_tab_indentation_is_an_empty_catalog(self):
        self.assertEqual(self._read("a:\n\tb: 1"), {})

    def test_non_mapping_document_is_an_empty_catalog(self):
        self.assertEqual(self._read("- a\n- b"), {})

    def test_a_non_utf8_catalog_is_an_empty_catalog(self):
        self.path.write_bytes(b"\xffClose: Schliessen\n")

        with self.assertLogs(level="WARNING"):
            self.assertEqual(i18n.read_catalog(self.path), {})

    def test_a_directory_at_the_catalog_path_is_an_empty_catalog(self):
        (self.directory / "sub.yaml").mkdir()

        with self.assertLogs(level="WARNING"):
            self.assertEqual(i18n.read_catalog(self.directory / "sub.yaml"), {})

    def test_non_string_entries_are_dropped(self):
        self.path.write_text(
            "Close: 42\nOpen:\nCopy: yes\nImprint: Impressum\n", encoding="utf-8"
        )

        self.assertEqual(i18n.read_catalog(self.path), {"Imprint": "Impressum"})


class TestCatalogMerge(unittest.TestCase):
    def setUp(self):
        directory = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, directory, True)
        (directory / "ui").mkdir()
        (directory / "content").mkdir()

        self.addCleanup(setattr, i18n, "UI_DIR", i18n.UI_DIR)
        self.addCleanup(setattr, i18n, "CONTENT_DIR", i18n.CONTENT_DIR)
        self.addCleanup(i18n.clear_catalogs)
        i18n.UI_DIR = directory / "ui"
        i18n.CONTENT_DIR = directory / "content"
        i18n.clear_catalogs()

    def test_the_content_catalog_overrides_the_shipped_interface_string(self):
        (i18n.UI_DIR / "de.yaml").write_text(
            "Close: Schliessen\nImprint: Impressum\n", encoding="utf-8"
        )
        (i18n.CONTENT_DIR / "de.yaml").write_text("Close: Zumachen\n", encoding="utf-8")

        self.assertEqual(
            i18n.catalog("de"), {"Close": "Zumachen", "Imprint": "Impressum"}
        )


class TestShippedCatalogs(unittest.TestCase):
    def test_thirty_languages_are_offered(self):
        self.assertEqual(len(i18n.LANGUAGES), 30)
        self.assertIn(i18n.SOURCE_LANGUAGE, i18n.LANGUAGES)

    def test_every_code_is_usable_in_the_route_converter(self):
        offenders = [
            code for code in i18n.LANGUAGES if not re.fullmatch(r"[a-z]+", code)
        ]

        self.assertFalse(offenders, f"Not usable in the route converter: {offenders}")

    def test_every_language_but_the_source_ships_a_ui_catalog(self):
        missing = [
            code
            for code in i18n.LANGUAGES
            if code != i18n.SOURCE_LANGUAGE
            and not (i18n.UI_DIR / f"{code}.yaml").is_file()
        ]

        self.assertFalse(missing, f"No UI catalogue for: {missing}")

    def test_ui_catalogs_cover_exactly_the_interface_strings(self):
        expected = set(i18n.UI_STRINGS)
        mismatched = {}

        for code in i18n.LANGUAGES:
            if code == i18n.SOURCE_LANGUAGE:
                continue
            path = i18n.UI_DIR / f"{code}.yaml"
            entries = yaml.safe_load(path.read_text(encoding="utf-8"))
            if set(entries) != expected:
                mismatched[code] = {
                    "missing": sorted(expected - set(entries)),
                    "unexpected": sorted(set(entries) - expected),
                }

        self.assertFalse(mismatched, f"UI catalogues out of sync: {mismatched}")

    def test_ui_strings_of_the_source_language_are_the_source(self):
        self.assertEqual(
            i18n.ui_strings("en"),
            {source: source for source in i18n.UI_STRINGS},
        )

    def test_ui_strings_are_translated_for_a_shipped_language(self):
        strings = i18n.ui_strings("de")

        self.assertEqual(strings["Close"], "Schließen")
        self.assertEqual(strings["Imprint"], "Impressum")


if __name__ == "__main__":
    unittest.main()
