import unittest

from app.utils import i18n


class TestUiTranslationCoverage(unittest.TestCase):
    def test_every_language_translates_every_interface_string(self):
        without_catalog = []
        with_gaps = {}

        for code in i18n.LANGUAGES:
            if code == i18n.SOURCE_LANGUAGE:
                continue
            path = i18n.UI_DIR / f"{code}.yaml"
            if not path.exists():
                without_catalog.append(code)
                continue
            entries = i18n.read_catalog(path)
            gaps = [
                source
                for source in i18n.UI_STRINGS
                if not entries.get(source, "").strip()
            ]
            if gaps:
                with_gaps[code] = gaps

        if without_catalog or with_gaps:
            self.fail(
                f"{len(without_catalog) + len(with_gaps)} of "
                f"{len(i18n.LANGUAGES) - 1} languages lack interface translations.\n"
                f"No catalogue ({len(without_catalog)}): {' '.join(without_catalog)}\n"
                f"Missing entries: {with_gaps}"
            )


if __name__ == "__main__":
    unittest.main()
