import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from utils import export_runtime_requirements


class TestExportRuntimeRequirements(unittest.TestCase):
    def test_load_runtime_requirements_reads_project_dependencies(self):
        pyproject_content = """
[project]
dependencies = [
    "flask",
    "requests>=2",
]
""".lstrip()

        with TemporaryDirectory() as temp_dir:
            pyproject_path = Path(temp_dir) / "pyproject.toml"
            pyproject_path.write_text(pyproject_content, encoding="utf-8")

            requirements = export_runtime_requirements.load_runtime_requirements(
                pyproject_path
            )

        self.assertEqual(requirements, ["flask", "requests>=2"])

    def test_main_prints_requirements_from_selected_pyproject(self):
        pyproject_content = """
[project]
dependencies = [
    "pyyaml",
]
""".lstrip()

        with TemporaryDirectory() as temp_dir:
            pyproject_path = Path(temp_dir) / "pyproject.toml"
            pyproject_path.write_text(pyproject_content, encoding="utf-8")

            with patch("builtins.print") as mock_print:
                exit_code = export_runtime_requirements.main([str(pyproject_path)])

        self.assertEqual(exit_code, 0)
        mock_print.assert_called_once_with("pyyaml")
