import copy
import datetime
import unittest

from app.utils import dashboard

FOLDERS = [
    {
        "slug": "office",
        "name": "Office",
        "description": "Documents",
        "icon": {"class": "fa-solid fa-briefcase"},
        "children": [
            {"slug": "cloud", "name": "Cloud", "description": "Files"},
            {"slug": "empty", "name": "Empty", "description": "Nothing here"},
        ],
    },
    {"slug": "chat", "name": "Chat", "description": "Talk"},
]


def config(**dashboard_section):
    return {
        "dashboard": {"folders": copy.deepcopy(FOLDERS), **dashboard_section},
        "cards": [
            {
                "title": "Nextcloud",
                "text": "Files and calendars",
                "id": "web-app-nextcloud",
                "tags": ["cloud"],
                "folders": ["office/cloud", "chat"],
                "added": "2026-11-01",
            },
            {
                "title": "Matrix",
                "text": "Chat",
                "id": "web-app-matrix",
                "folders": ["chat"],
            },
            {"title": "Unfiled", "text": "No folder"},
        ],
    }


class TestValidate(unittest.TestCase):
    def test_a_config_without_dashboard_is_left_alone(self):
        dashboard.validate({"cards": [{"folders": "not even a list"}]})

    def test_a_well_formed_dashboard_passes(self):
        dashboard.validate(config(new_days=14))

    def test_a_slug_outside_the_allowed_alphabet_is_rejected(self):
        broken = config()
        broken["dashboard"]["folders"][1]["slug"] = "Chat Room"

        with self.assertRaisesRegex(ValueError, "slug"):
            dashboard.validate(broken)

    def test_a_card_pointing_at_an_unknown_folder_is_rejected(self):
        broken = config()
        broken["cards"][1]["folders"] = ["office/missing"]

        with self.assertRaisesRegex(ValueError, "office/missing"):
            dashboard.validate(broken)

    def test_card_folders_are_ignored_while_the_folder_view_is_off(self):
        flat = config()
        del flat["dashboard"]["folders"]

        dashboard.validate(flat)

    def test_a_duplicated_folder_path_is_rejected(self):
        broken = config()
        broken["dashboard"]["folders"].append({"slug": "chat", "name": "Again"})

        with self.assertRaisesRegex(ValueError, "twice"):
            dashboard.validate(broken)

    def test_tags_must_be_a_list_of_strings(self):
        broken = config()
        broken["cards"][0]["tags"] = "cloud"

        with self.assertRaisesRegex(ValueError, "tags"):
            dashboard.validate(broken)

    def test_new_days_must_be_positive(self):
        with self.assertRaisesRegex(ValueError, "new_days"):
            dashboard.validate(config(new_days=0))

    def test_an_unparsable_added_date_is_rejected(self):
        broken = config()
        broken["cards"][0]["added"] = "yesterday"

        with self.assertRaisesRegex(ValueError, "ISO date"):
            dashboard.validate(broken)

    def test_a_folder_icon_that_is_not_a_class_mapping_is_rejected(self):
        for icon in ("fa-solid fa-cloud", ["fa-solid"], {"source": "x.png"}):
            with self.subTest(icon=icon):
                broken = config()
                broken["dashboard"]["folders"][1]["icon"] = icon

                with self.assertRaisesRegex(ValueError, "icon"):
                    dashboard.validate(broken)

    def test_a_card_id_used_twice_is_rejected(self):
        broken = config()
        broken["cards"][1]["id"] = "web-app-nextcloud"

        with self.assertRaisesRegex(ValueError, "used twice"):
            dashboard.validate(broken)


class TestLocate(unittest.TestCase):
    def setUp(self):
        self.model = dashboard.build(config(), config())

    def test_a_known_folder_opens_with_its_trail(self):
        self.assertEqual(
            dashboard.locate(self.model, "office/cloud"),
            ("office/cloud", [("office", "Office"), ("office/cloud", "Cloud")]),
        )

    def test_an_unknown_hidden_or_missing_folder_opens_the_top(self):
        for requested in (None, "", "nowhere", "office/empty"):
            with self.subTest(requested=requested):
                self.assertEqual(dashboard.locate(self.model, requested), ("", []))


class TestBuild(unittest.TestCase):
    def build(self, source=None, translated=None):
        source = source or config()
        return dashboard.build(translated or source, source)

    def test_no_dashboard_section_means_no_model(self):
        self.assertIsNone(dashboard.build({"cards": []}, {"cards": []}))

    def test_counts_distinct_applications_recursively(self):
        folders = {folder["path"]: folder for folder in self.build()["folders"]}

        self.assertEqual(folders["office"]["count"], 1)
        self.assertEqual(folders["office/cloud"]["count"], 1)
        self.assertEqual(folders["chat"]["count"], 2)

    def test_a_folder_without_applications_is_not_shown(self):
        paths = [folder["path"] for folder in self.build()["folders"]]

        self.assertNotIn("office/empty", paths)
        self.assertEqual(paths, ["office", "office/cloud", "chat"])

    def test_search_ships_translated_and_english_strings(self):
        source = config()
        translated = copy.deepcopy(source)
        translated["cards"][0]["text"] = "Dateien und Kalender"
        translated["dashboard"]["folders"][0]["name"] = "Büro"

        card = dashboard.build(translated, source)["cards"][0]

        for expected in (
            "Dateien und Kalender",
            "Files and calendars",
            "Büro",
            "Office",
            "cloud",
        ):
            self.assertIn(expected, card["search"])

    def test_the_client_data_carries_ids_folders_and_the_new_window(self):
        client = self.build(config(new_days=14))["client"]

        self.assertTrue(client["folder_view"])
        self.assertEqual(client["cards"][0]["key"], "web-app-nextcloud")
        self.assertIsNone(client["cards"][2]["key"])
        self.assertEqual(client["new_days"], 14)
        self.assertEqual(client["folders"]["office/cloud"]["parent"], "office")
        self.assertEqual(set(client), {"folder_view", "folders", "cards", "new_days"})

    def test_a_yaml_date_becomes_an_iso_string(self):
        source = config()
        source["cards"][0]["added"] = datetime.date(2026, 11, 1)

        self.assertEqual(self.build(source)["cards"][0]["added"], "2026-11-01")

    def test_a_yaml_datetime_becomes_its_date(self):
        source = config()
        source["cards"][0]["added"] = datetime.datetime(2026, 11, 1, 9, 30)

        dashboard.validate(source)
        self.assertEqual(self.build(source)["cards"][0]["added"], "2026-11-01")

    def test_without_folders_the_view_stays_flat(self):
        source = config()
        del source["dashboard"]["folders"]

        model = self.build(source)

        self.assertFalse(model["folder_view"])
        self.assertEqual(model["folders"], [])
        self.assertEqual(model["cards"][0]["folders"], [])


if __name__ == "__main__":
    unittest.main()
