import re
import tomllib
import unittest
from pathlib import Path


def distributions(requirements):
    """Return the distribution names of PEP 508 requirement strings."""
    return {
        re.split(r"[<>=!~\[; ]", requirement, maxsplit=1)[0]
        for requirement in requirements
    }


class TestPythonPackaging(unittest.TestCase):
    def setUp(self) -> None:
        self.repo_root = Path(__file__).resolve().parents[2]
        self.pyproject_path = self.repo_root / "pyproject.toml"

        with self.pyproject_path.open("rb") as handle:
            self.pyproject = tomllib.load(handle)

    def test_pyproject_defines_build_system_and_runtime_dependencies(self):
        build_system = self.pyproject["build-system"]
        project = self.pyproject["project"]

        self.assertEqual(build_system["build-backend"], "setuptools.build_meta")
        self.assertIn("setuptools>=69", build_system["requires"])
        self.assertGreaterEqual(
            distributions(project["dependencies"]),
            {"flask", "pyyaml", "requests"},
        )
        self.assertEqual(project["requires-python"], ">=3.12")

    def test_flask_is_pinned_to_a_version_that_honours_trusted_hosts(self):
        requirement = next(
            item
            for item in self.pyproject["project"]["dependencies"]
            if item.startswith("flask")
        )

        self.assertIn(">=3.1", requirement)

    def test_pyproject_defines_dev_dependencies_and_package_contents(self):
        project = self.pyproject["project"]
        setuptools_config = self.pyproject["tool"]["setuptools"]
        package_find = setuptools_config["packages"]["find"]
        package_data = setuptools_config["package-data"]["app"]

        self.assertGreaterEqual(
            distributions(project["optional-dependencies"]["dev"]),
            {"bandit", "pip-audit", "ruff", "yamllint"},
        )
        self.assertEqual(setuptools_config["py-modules"], ["main"])
        self.assertEqual(package_find["include"], ["app", "app.*"])
        self.assertIn("config.sample.yaml", package_data)
        self.assertIn("templates/**/*.j2", package_data)
        self.assertIn("static/css/*.css", package_data)
        self.assertIn("static/js/*.js", package_data)

    def test_legacy_requirements_files_are_removed(self):
        self.assertFalse((self.repo_root / "requirements.txt").exists())
        self.assertFalse((self.repo_root / "requirements-dev.txt").exists())
        self.assertFalse((self.repo_root / "app" / "requirements.txt").exists())

    def test_package_init_files_exist(self):
        self.assertTrue((self.repo_root / "app" / "__init__.py").is_file())
        self.assertTrue((self.repo_root / "app" / "utils" / "__init__.py").is_file())


if __name__ == "__main__":
    unittest.main()
