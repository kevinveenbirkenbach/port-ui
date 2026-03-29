import subprocess
import unittest
from pathlib import Path

import yaml


class TestConfigHygiene(unittest.TestCase):
    def setUp(self) -> None:
        self.repo_root = Path(__file__).resolve().parents[2]
        self.sample_config_path = self.repo_root / "app" / "config.sample.yaml"

    def _is_tracked(self, path: str) -> bool:
        result = subprocess.run(
            ["git", "ls-files", "--error-unmatch", path],
            cwd=self.repo_root,
            check=False,
            capture_output=True,
            text=True,
        )
        return result.returncode == 0

    def _find_values_for_key(self, data, key_name: str):
        if isinstance(data, dict):
            for key, value in data.items():
                if key == key_name:
                    yield value
                yield from self._find_values_for_key(value, key_name)
        elif isinstance(data, list):
            for item in data:
                yield from self._find_values_for_key(item, key_name)

    def test_runtime_only_files_are_ignored_and_untracked(self):
        gitignore_lines = (
            (self.repo_root / ".gitignore").read_text(encoding="utf-8").splitlines()
        )

        self.assertIn("app/config.yaml", gitignore_lines)
        self.assertIn(".env", gitignore_lines)
        self.assertFalse(self._is_tracked("app/config.yaml"))
        self.assertFalse(self._is_tracked(".env"))

    def test_sample_config_keeps_the_nasa_api_key_placeholder(self):
        with self.sample_config_path.open("r", encoding="utf-8") as handle:
            sample_config = yaml.safe_load(handle)

        nasa_api_keys = list(self._find_values_for_key(sample_config, "nasa_api_key"))
        self.assertEqual(
            nasa_api_keys,
            ["YOUR_REAL_KEY_HERE"],
            "config.sample.yaml should only contain the documented NASA API key "
            "placeholder.",
        )


if __name__ == "__main__":
    unittest.main()
