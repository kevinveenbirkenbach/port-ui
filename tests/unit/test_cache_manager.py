import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import Mock, patch

import requests

from app.utils.cache_manager import CacheManager


class TestCacheManager(unittest.TestCase):
    def test_init_creates_cache_directory(self):
        with TemporaryDirectory() as temp_dir:
            cache_dir = Path(temp_dir) / "cache"

            self.assertFalse(cache_dir.exists())

            CacheManager(str(cache_dir))

            self.assertTrue(cache_dir.is_dir())

    def test_clear_cache_removes_files_but_keeps_subdirectories(self):
        with TemporaryDirectory() as temp_dir:
            cache_dir = Path(temp_dir) / "cache"
            nested_dir = cache_dir / "nested"
            nested_dir.mkdir(parents=True)
            file_path = cache_dir / "icon.png"
            file_path.write_bytes(b"icon")

            manager = CacheManager(str(cache_dir))
            manager.clear_cache()

            self.assertFalse(file_path.exists())
            self.assertTrue(nested_dir.is_dir())

    @patch("app.utils.cache_manager.requests.get")
    def test_cache_file_downloads_and_stores_response(self, mock_get):
        with TemporaryDirectory() as temp_dir:
            manager = CacheManager(str(Path(temp_dir) / "cache"))
            response = Mock()
            response.headers = {"Content-Type": "image/svg+xml; charset=utf-8"}
            response.iter_content.return_value = [b"<svg>ok</svg>"]
            response.raise_for_status.return_value = None
            mock_get.return_value = response

            cached_path = manager.cache_file("https://example.com/logo/download")

            self.assertIsNotNone(cached_path)
            self.assertTrue(cached_path.startswith("cache/logo_"))
            self.assertTrue(cached_path.endswith(".svg"))

            stored_file = Path(manager.cache_dir) / Path(cached_path).name
            self.assertEqual(stored_file.read_bytes(), b"<svg>ok</svg>")
            mock_get.assert_called_once_with(
                "https://example.com/logo/download",
                stream=True,
                timeout=5,
            )

    @patch("app.utils.cache_manager.requests.get")
    def test_cache_file_returns_none_when_request_fails(self, mock_get):
        with TemporaryDirectory() as temp_dir:
            manager = CacheManager(str(Path(temp_dir) / "cache"))
            mock_get.side_effect = requests.RequestException("network")

            cached_path = manager.cache_file("https://example.com/icon.png")

            self.assertIsNone(cached_path)


if __name__ == "__main__":
    unittest.main()
