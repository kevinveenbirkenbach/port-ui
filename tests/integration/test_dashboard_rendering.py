import json
import os
import re
import shutil
import tempfile
import unittest
from html.parser import HTMLParser
from pathlib import Path

import yaml

app_module = None
flask_app = None
i18n = None
_origin = None
_workdir = None

BASE = {
    "platform": {
        "titel": "Portal",
        "subtitel": "Apps",
        "logo": {"class": "fa-solid fa-cube"},
        "favicon": {"class": "fa-solid fa-cube"},
    },
    "company": {
        "titel": "Example",
        "subtitel": "Company",
        "logo": {"class": "fa-solid fa-cube"},
        "address": {"city": "Berlin"},
        "imprint_url": "https://example.test/imprint",
    },
    "navigation": {"header": {"children": []}, "footer": {"children": []}},
    "cards": [
        {
            "icon": {"class": "fa-solid fa-cloud"},
            "title": "Nextcloud",
            "text": "Files and calendars",
            "url": "https://cloud.example.test",
            "link_text": "cloud",
            "id": "web-app-nextcloud",
            "tags": ["files"],
            "folders": ["office/cloud"],
        },
        {
            "icon": {"class": "fa-solid fa-comments"},
            "title": "Matrix",
            "text": "Chat",
            "url": "https://chat.example.test",
            "link_text": "chat",
            "id": "web-app-matrix",
        },
    ],
}

DASHBOARD = {
    "folders": [
        {
            "slug": "office",
            "name": "Office",
            "description": "Documents",
            "icon": {"class": "fa-solid fa-briefcase"},
            "children": [
                {"slug": "cloud", "name": "Cloud", "description": "Files"},
                {"slug": "unused", "name": "Unused", "description": "Nothing"},
            ],
        }
    ],
    "new_days": 14,
}


def write_config(with_dashboard):
    config = dict(BASE)
    if with_dashboard:
        config["dashboard"] = DASHBOARD
    Path(_workdir, "config.yaml").write_text(yaml.safe_dump(config), encoding="utf-8")


def setUpModule():
    """Import the app against a disposable configuration without remote assets.

    ``app.app`` reads ``config.yaml`` from the working directory, so the chdir
    has to happen before the import, and every test reloads after rewriting it.
    """
    global app_module, flask_app, i18n, _origin, _workdir

    _origin = os.getcwd()
    _workdir = tempfile.mkdtemp(prefix="portfolio-dashboard-")
    os.chdir(_workdir)
    write_config(with_dashboard=False)

    from app import app as imported_module
    from app.utils import i18n as imported_i18n

    app_module = imported_module
    flask_app = imported_module.app
    i18n = imported_i18n
    flask_app.config["NASA_API_KEY"] = None


def tearDownModule():
    os.chdir(_origin)
    shutil.rmtree(_workdir, ignore_errors=True)


class FrameCollector(HTMLParser):
    VOID = {"img", "br", "hr", "input", "link", "meta", "source"}

    def __init__(self):
        super().__init__()
        self.stack = []
        self.wrapped = {"portui-frame-top": [], "portui-frame-bottom": []}

    @classmethod
    def collect(cls, body):
        collector = cls()
        collector.feed(body)
        return collector.wrapped

    def handle_starttag(self, tag, attrs):
        if tag in self.VOID:
            return
        classes = (dict(attrs).get("class") or "").split()
        frame = next((name for name in self.wrapped if name in classes), None)
        inside = next((entry for _, entry in reversed(self.stack) if entry), None)
        if inside and tag in ("header", "footer"):
            self.wrapped[inside].append(tag)
        if inside and tag == "nav" and "navbar" in classes:
            menu = next(name for name in classes if name.startswith("menu-"))
            self.wrapped[inside].append(f"nav.{menu}")
        self.stack.append((tag, frame))

    def handle_endtag(self, tag):
        open_tags = [name for name, _ in self.stack]
        if tag in open_tags:
            del self.stack[len(open_tags) - 1 - open_tags[::-1].index(tag) :]


def data_block(body):
    match = re.search(
        r'<script id="portui-dashboard-data" type="application/json">(.*?)</script>',
        body,
        re.S,
    )
    return json.loads(match.group(1)) if match else None


class TestWithoutDashboard(unittest.TestCase):
    def setUp(self):
        write_config(with_dashboard=False)
        app_module.load_config(flask_app)
        self.body = flask_app.test_client().get("/en/").get_data(as_text=True)

    def test_the_page_carries_no_dashboard_markup_or_assets(self):
        for marker in (
            "portui-dashboard",
            "portui-search",
            "css/dashboard.css",
            "js/dashboard.js",
            "data-portui-card",
        ):
            with self.subTest(marker=marker):
                self.assertNotIn(marker, self.body)

    def test_the_cards_render_in_the_flat_grid(self):
        self.assertIn("Nextcloud", self.body)
        self.assertIn("Matrix", self.body)

    def test_the_frame_hooks_wrap_header_and_footer(self):
        wrapped = FrameCollector.collect(self.body)

        self.assertEqual(wrapped["portui-frame-top"], ["header", "nav.menu-header"])
        self.assertEqual(wrapped["portui-frame-bottom"], ["nav.menu-footer", "footer"])


class TestWithDashboard(unittest.TestCase):
    def setUp(self):
        write_config(with_dashboard=True)
        app_module.load_config(flask_app)
        self.addCleanup(i18n.clear_catalogs)
        self.client = flask_app.test_client()

    def test_the_search_field_sits_in_the_header_navigation(self):
        body = self.client.get("/en/").get_data(as_text=True)
        header_nav = body[body.index("menu-header") : body.index("menu-footer")]

        self.assertIn('id="portui-search"', header_nav)
        self.assertIn("js/dashboard.js", body)
        self.assertIn("css/dashboard.css", body)

    def test_only_folders_with_applications_are_rendered(self):
        body = self.client.get("/en/").get_data(as_text=True)

        self.assertIn('data-portui-folder="office"', body)
        self.assertIn('data-portui-folder="office/cloud"', body)
        self.assertNotIn('data-portui-folder="office/unused"', body)

    def test_the_requested_folder_renders_without_javascript(self):
        body = self.client.get("/en/?folder=office/cloud").get_data(as_text=True)

        self.assertIn('data-portui-folder="office" hidden', body)
        self.assertIn('data-portui-card="0" data-portui-id="web-app-nextcloud">', body)
        self.assertIn(
            'data-portui-card="1" data-portui-id="web-app-matrix" hidden', body
        )
        self.assertIn(
            'href="?folder=office" data-portui-folder-link="office">Office<', body
        )
        self.assertIn(
            'href="?folder=office/cloud" data-portui-folder-link="office/cloud">Cloud<',
            body,
        )

    def test_an_unknown_requested_folder_renders_the_top_level(self):
        body = self.client.get("/en/?folder=nowhere").get_data(as_text=True)

        self.assertRegex(body, r'data-portui-folder="office">')
        self.assertIn(
            'data-portui-card="0" data-portui-id="web-app-nextcloud" hidden', body
        )
        self.assertNotIn('data-portui-folder-link="nowhere"', body)

    def test_the_frame_check_notices_a_navbar_outside_its_wrapper(self):
        misplaced = (
            '<div class="portui-frame-bottom"></div>'
            '<nav class="navbar menu-footer"></nav><footer></footer>'
        )

        self.assertEqual(FrameCollector.collect(misplaced)["portui-frame-bottom"], [])

    def test_a_filed_card_starts_hidden_and_an_unfiled_one_visible(self):
        body = self.client.get("/en/").get_data(as_text=True)

        self.assertIn(
            'data-portui-card="0" data-portui-id="web-app-nextcloud" hidden', body
        )
        self.assertIn('data-portui-card="1" data-portui-id="web-app-matrix">', body)

    def test_folder_names_translate_while_slugs_and_paths_do_not(self):
        i18n._catalogs["de"] = {"Office": "Büro", "office": "buero", "cloud": "wolke"}

        body = self.client.get("/de/").get_data(as_text=True)
        data = data_block(body)

        self.assertIn("Büro", body)
        self.assertEqual(data["folders"]["office"]["name"], "Büro")
        self.assertEqual(data["folders"]["office"]["name_en"], "Office")
        self.assertEqual(data["cards"][0]["folders"], ["office/cloud"])
        self.assertIn("Büro", data["cards"][0]["search"])
        self.assertIn("Office", data["cards"][0]["search"])

    def test_the_client_data_reaches_the_browser_as_json(self):
        body = self.client.get("/en/").get_data(as_text=True)
        data = data_block(body)

        self.assertEqual(data["cards"][0]["key"], "web-app-nextcloud")
        self.assertEqual(data["new_days"], 14)
        self.assertIn('data-portui-chips="web-app-nextcloud"', body)
        self.assertIn("js/chips.js", body)

    def test_the_chip_labels_core_uses_ship_translated(self):
        body = self.client.get("/de/").get_data(as_text=True)
        block = re.search(
            r'<script id="i18n" type="application/json">(.*?)</script>', body, re.S
        )
        strings = json.loads(block.group(1))

        for source in ("Sign in", "Request access", "No access", "Paused", "Down"):
            with self.subTest(source=source):
                self.assertNotEqual(strings[source], source)

    def test_a_reload_without_the_section_switches_the_dashboard_off(self):
        write_config(with_dashboard=False)
        app_module.load_config(flask_app)

        body = self.client.get("/en/").get_data(as_text=True)

        self.assertNotIn("portui-dashboard", body)

    def test_new_interface_strings_ship_to_the_browser(self):
        body = self.client.get("/de/").get_data(as_text=True)
        block = re.search(
            r'<script id="i18n" type="application/json">(.*?)</script>', body, re.S
        )
        strings = json.loads(block.group(1))

        self.assertEqual(strings["Search applications"], "Anwendungen durchsuchen")
        self.assertEqual(strings["Running"], "Läuft")


if __name__ == "__main__":
    unittest.main()
