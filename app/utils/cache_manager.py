import hashlib
import mimetypes
import os

import requests


class CacheManager:
    def __init__(self, cache_dir="static/cache"):
        self.cache_dir = cache_dir
        self._ensure_cache_dir_exists()

    def _ensure_cache_dir_exists(self):
        os.makedirs(self.cache_dir, exist_ok=True)

    def clear_cache(self):
        if os.path.exists(self.cache_dir):
            for filename in os.listdir(self.cache_dir):
                path = os.path.join(self.cache_dir, filename)
                if os.path.isfile(path):
                    os.remove(path)

    def cache_file(self, file_url):
        hash_suffix = hashlib.blake2s(
            file_url.encode("utf-8"),
            digest_size=8,
        ).hexdigest()
        parts = file_url.rstrip("/").split("/")
        base = parts[-2] if parts[-1] == "download" else parts[-1]

        try:
            resp = requests.get(file_url, stream=True, timeout=5)
            resp.raise_for_status()
        except requests.RequestException:
            return None

        content_type = resp.headers.get("Content-Type", "")
        ext = mimetypes.guess_extension(content_type.split(";")[0].strip()) or ".png"
        filename = f"{base}_{hash_suffix}{ext}"
        full_path = os.path.join(self.cache_dir, filename)

        if not os.path.exists(full_path):
            with open(full_path, "wb") as f:
                for chunk in resp.iter_content(1024):
                    f.write(chunk)

        return f"cache/{filename}"
