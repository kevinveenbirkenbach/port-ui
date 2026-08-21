import unittest
from html.parser import HTMLParser
from pathlib import Path

from jinja2 import Environment, FileSystemLoader


class AnchorCollector(HTMLParser):
    def __init__(self):
        super().__init__()
        self.anchors = []

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            self.anchors.append(dict(attrs))


class TestNavigationTemplate(unittest.TestCase):
    def test_top_level_dropdowns_have_bootstrap_toggle_attribute(self):
        template_dir = Path(__file__).resolve().parents[2] / "app" / "templates"
        environment = Environment(
            loader=FileSystemLoader(template_dir),
            autoescape=True,
        )
        environment.globals["url_for"] = lambda endpoint, **kwargs: (
            f"/static/{kwargs['filename']}"
            if endpoint == "static"
            else f"/{kwargs['lang']}/"
        )
        environment.globals["asset_src"] = lambda asset: (
            (asset or {}).get("external_url")
            or (
                f"/static/{(asset or {}).get('cache')}"
                if (asset or {}).get("cache")
                else ""
            )
        )

        rendered = environment.get_template("moduls/navigation.html.j2").render(
            menu_type="header",
            lang="en",
            languages={"en": "English", "de": "Deutsch"},
            t=lambda source: source,
            platform={
                "titel": "Portfolio",
                "logo": {"cache": "logo.png"},
            },
            navigation={
                "header": {
                    "children": [
                        {
                            "name": "Apps",
                            "description": "Application menu",
                            "icon": {"class": "fa-solid fa-grid"},
                            "children": [
                                {
                                    "name": "Example",
                                    "description": "Example app",
                                    "icon": {"class": "fa-solid fa-link"},
                                    "url": "https://example.test",
                                }
                            ],
                        }
                    ]
                }
            },
        )

        parser = AnchorCollector()
        parser.feed(rendered)
        dropdown_toggles = [
            anchor
            for anchor in parser.anchors
            if "nav-link" in anchor.get("class", "")
            and "dropdown-toggle" in anchor.get("class", "")
        ]

        self.assertEqual(len(dropdown_toggles), 2)
        for toggle in dropdown_toggles:
            self.assertEqual(toggle.get("data-bs-toggle"), "dropdown")

        language_links = [
            anchor for anchor in parser.anchors if anchor.get("hreflang") == "de"
        ]
        self.assertEqual(len(language_links), 1)
        self.assertEqual(language_links[0]["href"], "/de/")


if __name__ == "__main__":
    unittest.main()
