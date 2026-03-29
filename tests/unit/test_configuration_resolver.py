import unittest

from app.utils.configuration_resolver import ConfigurationResolver


class TestConfigurationResolver(unittest.TestCase):
    def test_resolve_links_replaces_mapping_link_with_target_object(self):
        config = {
            "profiles": [
                {"name": "Mastodon", "url": "https://example.com/@user"},
            ],
            "featured": {"link": "profiles.mastodon"},
        }

        resolver = ConfigurationResolver(config)
        resolver.resolve_links()

        self.assertEqual(
            resolver.get_config()["featured"],
            {"name": "Mastodon", "url": "https://example.com/@user"},
        )

    def test_resolve_links_expands_children_link_to_list_entries(self):
        config = {
            "accounts": {
                "children": [
                    {"name": "Matrix", "url": "https://matrix.example"},
                    {"name": "Signal", "url": "https://signal.example"},
                ]
            },
            "navigation": {
                "children": [
                    {"link": "accounts.children"},
                ]
            },
        }

        resolver = ConfigurationResolver(config)
        resolver.resolve_links()

        self.assertEqual(
            resolver.get_config()["navigation"]["children"],
            [
                {"name": "Matrix", "url": "https://matrix.example"},
                {"name": "Signal", "url": "https://signal.example"},
            ],
        )

    def test_resolve_links_rejects_non_list_children(self):
        config = {"navigation": {"children": {"name": "Invalid"}}}

        resolver = ConfigurationResolver(config)

        with self.assertRaises(ValueError):
            resolver.resolve_links()

    def test_find_entry_handles_case_and_space_insensitive_paths(self):
        config = {
            "Social Networks": {
                "children": [
                    {"name": "Friendica", "url": "https://friendica.example"},
                ]
            }
        }

        resolver = ConfigurationResolver(config)

        entry = resolver._find_entry(config, "socialnetworks.friendica", False)

        self.assertEqual(entry["url"], "https://friendica.example")


if __name__ == "__main__":
    unittest.main()
