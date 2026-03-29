import unittest
from pathlib import Path

import yaml

SKIP_DIR_NAMES = {".git", ".ruff_cache", "__pycache__", "node_modules"}
SKIP_FILES = {"app/config.yaml"}
YAML_SUFFIXES = {".yml", ".yaml"}


class TestYamlSyntax(unittest.TestCase):
    def test_all_repository_yaml_files_are_valid(self):
        repo_root = Path(__file__).resolve().parents[2]
        invalid_files = []

        for path in repo_root.rglob("*"):
            if not path.is_file() or path.suffix not in YAML_SUFFIXES:
                continue

            relative_path = path.relative_to(repo_root).as_posix()
            if relative_path in SKIP_FILES:
                continue

            if any(part in SKIP_DIR_NAMES for part in path.parts):
                continue

            try:
                with path.open("r", encoding="utf-8") as handle:
                    yaml.safe_load(handle)
            except yaml.YAMLError as error:
                invalid_files.append((relative_path, str(error).splitlines()[0]))
            except Exception as error:
                invalid_files.append((relative_path, f"Unexpected error: {error}"))

        self.assertFalse(
            invalid_files,
            "Found invalid YAML files:\n"
            + "\n".join(f"- {path}: {error}" for path, error in invalid_files),
        )


if __name__ == "__main__":
    unittest.main()
