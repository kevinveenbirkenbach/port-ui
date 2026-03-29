import unittest
from pathlib import Path

import yaml

ALLOWED_URL_PREFIXES = ("https://", "mailto:", "tel:")
URL_KEYS = {"url", "imprint", "imprint_url"}


class TestSampleConfigUrls(unittest.TestCase):
    def setUp(self) -> None:
        repo_root = Path(__file__).resolve().parents[2]
        sample_config_path = repo_root / "app" / "config.sample.yaml"
        with sample_config_path.open("r", encoding="utf-8") as handle:
            self.sample_config = yaml.safe_load(handle)

    def _iter_urls(self, data, path="root"):
        if isinstance(data, dict):
            for key, value in data.items():
                next_path = f"{path}.{key}"
                if key in URL_KEYS and isinstance(value, str):
                    yield next_path, value
                yield from self._iter_urls(value, next_path)
        elif isinstance(data, list):
            for index, item in enumerate(data):
                yield from self._iter_urls(item, f"{path}[{index}]")

    def test_sample_config_urls_use_safe_schemes(self):
        invalid_urls = [
            f"{path} -> {url}"
            for path, url in self._iter_urls(self.sample_config)
            if not url.startswith(ALLOWED_URL_PREFIXES)
        ]

        self.assertFalse(
            invalid_urls,
            "The sample config contains URLs with unsupported schemes:\n"
            + "\n".join(f"- {entry}" for entry in invalid_urls),
        )


if __name__ == "__main__":
    unittest.main()
