"""Guards for configuration that no other test observes.

Each assertion here stands for a defect that was found by deleting the line it
checks: the deletion is invisible to every suite, and its effect only shows up
in production or in a fresh checkout.
"""

import json
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


class TestLintCoverage(unittest.TestCase):
    def setUp(self):
        self.makefile = (REPO_ROOT / "Makefile").read_text(encoding="utf-8")

    def test_the_lint_target_runs_every_linter(self):
        prerequisites = re.search(r"^lint: (.+)$", self.makefile, re.MULTILINE).group(1)

        self.assertGreaterEqual(
            set(prerequisites.split()),
            {"lint-actions", "lint-python", "lint-yaml", "lint-js", "lint-shell"},
        )

    def test_every_linter_has_a_ci_job(self):
        workflow = yaml.safe_load(
            (REPO_ROOT / ".github" / "workflows" / "lint.yml").read_text(
                encoding="utf-8"
            )
        )

        self.assertGreaterEqual(
            set(workflow["jobs"]),
            {"lint-actions", "lint-python", "lint-yaml", "lint-js", "lint-shell"},
        )

    def test_the_javascript_linter_is_declared(self):
        package = json.loads(
            (REPO_ROOT / "app" / "package.json").read_text(encoding="utf-8")
        )

        self.assertGreaterEqual(
            set(package["devDependencies"]), {"eslint", "@eslint/js", "globals"}
        )

    def test_the_documented_environment_keys_exist(self):
        example = (REPO_ROOT / "env.example").read_text(encoding="utf-8")

        for key in ("PORT", "IMAGE_NAME", "TRUSTED_HOSTS", "LIBRETRANSLATE_URL"):
            with self.subTest(key=key):
                self.assertRegex(example, rf"(?m)^{key}=")


class TestEndToEndRunner(unittest.TestCase):
    def setUp(self):
        self.script = (REPO_ROOT / "scripts" / "run-e2e.sh").read_text(encoding="utf-8")

    def test_a_foreign_listener_stops_the_run(self):
        self.assertIn("already serves port", self.script)

    def test_cypress_is_pinned_to_the_origin_flask_binds(self):
        self.assertIn("CYPRESS_baseUrl", self.script)
        self.assertIn("127.0.0.1", self.script)

    def test_the_electron_node_flag_is_dropped(self):
        self.assertIn("env -u ELECTRON_RUN_AS_NODE", self.script)

    def test_every_probe_bypasses_a_proxy_and_is_bounded(self):
        probes = [line for line in self.script.splitlines() if "curl " in line]

        self.assertTrue(probes)
        for probe in probes:
            with self.subTest(probe=probe.strip()):
                self.assertIn("--noproxy", probe)
                self.assertIn("--max-time", probe)


class TestVendoredAssets(unittest.TestCase):
    def test_the_right_to_left_stylesheet_is_vendored(self):
        script = (REPO_ROOT / "app" / "scripts" / "copy-vendor.js").read_text(
            encoding="utf-8"
        )

        self.assertEqual(
            script.count("bootstrap.rtl.min.css"),
            2,
            "the RTL stylesheet needs both a source and a destination path",
        )


class TestPackagedCatalogs(unittest.TestCase):
    def test_the_interface_catalogs_are_declared_as_package_data(self):
        with (REPO_ROOT / "pyproject.toml").open("rb") as handle:
            pyproject = tomllib.load(handle)

        package_data = pyproject["tool"]["setuptools"]["package-data"]["app"]

        self.assertIn("i18n/ui/*.yaml", package_data)


if __name__ == "__main__":
    unittest.main()
