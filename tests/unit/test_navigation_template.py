import unittest
from html.parser import HTMLParser
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape


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
            autoescape=select_autoescape(),
        )
        environment.globals["url_for"] = lambda _endpoint, filename: (
            f"/static/{filename}"
        )

        rendered = environment.get_template("moduls/navigation.html.j2").render(
            menu_type="header",
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

        self.assertEqual(len(dropdown_toggles), 1)
        self.assertEqual(dropdown_toggles[0].get("data-bs-toggle"), "dropdown")


if __name__ == "__main__":
    unittest.main()
