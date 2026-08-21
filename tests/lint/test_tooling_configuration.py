"""Guards for configuration that no other test observes.

Each assertion here stands for a defect that was found by deleting the line it
checks: the deletion is invisible to every suite, and its effect only shows up
in production or in a fresh checkout.
"""

import re
import tomllib
import unittest
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]


class TestYamllintConfiguration(unittest.TestCase):
    def setUp(self):
        self.config = yaml.safe_load(
            (REPO_ROOT / ".yamllint").read_text(encoding="utf-8")
        )

    def test_duplicate_keys_are_an_error(self):
        self.assertEqual(self.config["rules"]["key-duplicates"], "enable")

    def test_the_directories_that_collect_foreign_yaml_are_ignored(self):
        ignored = self.config["ignore"].split()

        self.assertGreaterEqual(
            set(ignored),
            {".git/", ".venv/", "node_modules/", "app/node_modules/"},
        )


class TestRunTargets(unittest.TestCase):
    def setUp(self):
        self.makefile = (REPO_ROOT / "Makefile").read_text(encoding="utf-8")
        self.recipes = {
            name: body
            for name, body in re.findall(
                r"^(run-dev|run-prod):[^\n]*\n((?:\t[^\n]*\n)+)",
                self.makefile,
                re.MULTILINE,
            )
        }

    def test_both_run_targets_exist(self):
        self.assertEqual(set(self.recipes), {"run-dev", "run-prod"})

    def test_the_container_is_told_which_hosts_are_trusted(self):
        for name, body in self.recipes.items():
            with self.subTest(target=name):
                self.assertIn("TRUSTED_HOSTS", body)

    def test_the_container_is_told_which_port_to_bind(self):
        for name, body in self.recipes.items():
            with self.subTest(target=name):
                self.assertIn('-e PORT="$$PORT"', body)

    def test_the_whole_env_file_is_not_handed_to_the_web_container(self):
        for name, body in self.recipes.items():
            with self.subTest(target=name):
                self.assertNotIn("--env-file", body)


class TestPackagedCatalogs(unittest.TestCase):
    def test_the_interface_catalogs_are_declared_as_package_data(self):
        with (REPO_ROOT / "pyproject.toml").open("rb") as handle:
            pyproject = tomllib.load(handle)

        package_data = pyproject["tool"]["setuptools"]["package-data"]["app"]

        self.assertIn("i18n/ui/*.yaml", package_data)


if __name__ == "__main__":
    unittest.main()
