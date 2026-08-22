#!/usr/bin/env python3
"""Fill missing content translations from a LibreTranslate instance.

Reads the prose strings out of the live ``app/config.yaml`` and writes one
catalogue per language to ``app/i18n/content/``. Entries that already exist are
never overwritten, so a hand-corrected translation survives every later run.
"""

import argparse
import os
import sys
from pathlib import Path

import requests
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from app.utils import i18n  # noqa: E402

DEFAULT_CONFIG_PATH = REPO_ROOT / "app" / "config.yaml"
REQUEST_TIMEOUT = 30


def collect_sources(node, key=None, found=None):
    """Return every prose string in ``node`` that a backend may translate.

    Args:
        node: the raw configuration tree, or any subtree of it.
        key: the mapping key ``node`` was reached through.
        found: accumulator, for recursion.
    """
    found = set() if found is None else found
    if isinstance(node, dict):
        for name, value in node.items():
            collect_sources(value, name, found)
    elif isinstance(node, list):
        for item in node:
            collect_sources(item, key, found)
    elif isinstance(node, str) and key in i18n.AUTOFILL_KEYS and node.strip():
        found.add(node)
    return found


class BackendError(Exception):
    """The translation backend answered in a way the run cannot continue from."""


def supported_languages(url, session):
    """Return the language codes the LibreTranslate instance at ``url`` offers."""
    try:
        response = session.get(f"{url}/languages", timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        offered = response.json()
    except requests.RequestException as error:
        raise BackendError(f"{url} is not reachable: {error}")
    except ValueError:
        raise BackendError(f"{url}/languages did not answer JSON")

    if not isinstance(offered, list):
        raise BackendError(
            f"{url}/languages answered {type(offered).__name__}, not a list"
        )
    codes = {
        entry["code"]
        for entry in offered
        if isinstance(entry, dict) and isinstance(entry.get("code"), str)
    }
    if not codes:
        raise BackendError(f"{url}/languages listed no usable language codes")
    return codes


def load_existing(path):
    """Return the catalogue at ``path``, or None when it must not be rewritten.

    Distinct from ``i18n.read_catalog``, which degrades an unreadable catalogue
    to English at render time. Here the same file means the hand-written entries
    are unknown, and writing would replace them with a fresh machine pass.
    """
    if not path.exists():
        return {}
    try:
        loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, yaml.YAMLError) as error:
        print(f"  ! {path.name}: {type(error).__name__}, refusing to overwrite it")
        return None
    if loaded is None:
        return {}
    if not isinstance(loaded, dict):
        print(f"  ! {path.name}: not a mapping, refusing to overwrite it")
        return None
    return loaded


def write_catalog(path, catalog):
    """Replace ``path`` with ``catalog`` in one step.

    Writing in place would leave a half-written catalogue behind if the process
    is interrupted or the disk fills, and the truncated remainder can still be
    valid YAML — the next run would then machine-fill the destroyed entries.
    """
    temporary = path.with_name(f"{path.name}.tmp")
    temporary.write_text(
        yaml.safe_dump(catalog, allow_unicode=True, sort_keys=True, width=1000),
        encoding="utf-8",
    )
    os.replace(temporary, path)


def translate(session, url, api_key, text, target):
    """Translate one string into ``target``, or return None on failure."""
    payload = {
        "q": text,
        "source": i18n.SOURCE_LANGUAGE,
        "target": target,
        "format": "text",
    }
    if api_key:
        payload["api_key"] = api_key

    try:
        response = session.post(
            f"{url}/translate", data=payload, timeout=REQUEST_TIMEOUT
        )
    except requests.RequestException as error:
        print(f"  ! {target}: {type(error).__name__}, {error}")
        return None

    if not response.ok:
        print(f"  ! {target}: {response.status_code} {response.text[:120]}")
        return None

    try:
        translated = response.json().get("translatedText")
    except ValueError:
        print(f"  ! {target}: answered 200 but not JSON")
        return None

    if not isinstance(translated, str) or not translated.strip():
        print(f"  ! {target}: unusable translatedText ({translated!r})")
        return None
    return translated


def sync(url, api_key, sources, targets, directory):
    """Fill and write the catalogue of every language in ``targets``.

    Args:
        url: base URL of the LibreTranslate instance.
        api_key: API key, or an empty string.
        sources: English strings to translate.
        targets: language codes to fill.
        directory: catalogue directory to write into.
    """
    directory.mkdir(parents=True, exist_ok=True)
    session = requests.Session()

    available = supported_languages(url, session)
    for target in targets:
        if target not in available:
            print(f"- {target}: not offered by {url}, skipped")
            continue

        path = directory / f"{target}.yaml"
        catalog = load_existing(path)
        if catalog is None:
            continue

        shipped = (
            {}
            if directory == i18n.UI_DIR
            else i18n.read_catalog(i18n.UI_DIR / f"{target}.yaml")
        )
        missing = sorted(
            source
            for source in sources
            if source not in catalog and source not in shipped
        )
        if not missing:
            print(f"- {target}: complete")
            continue

        print(f"- {target}: translating {len(missing)} string(s)")
        added = 0
        for source in missing:
            translated = translate(session, url, api_key, source, target)
            if translated:
                catalog[source] = translated
                added += 1

        if not added:
            print(f"  ! {target}: nothing translated, leaving the file untouched")
            continue

        try:
            write_catalog(path, catalog)
        except OSError as error:
            print(f"  ! {target}: could not write {path.name}: {error}")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--url",
        required=True,
        help="Base URL of a LibreTranslate instance, e.g. http://localhost:5002",
    )
    parser.add_argument(
        "--api-key",
        default="",
        help="API key, if the instance requires one.",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_CONFIG_PATH,
        help=f"Configuration to read the prose from (default: {DEFAULT_CONFIG_PATH}).",
    )
    parser.add_argument(
        "--catalog",
        choices=("content", "ui"),
        default="content",
        help=(
            "content: your configuration's prose, generated per deployment. "
            "ui: the interface strings that ship with the project."
        ),
    )
    parser.add_argument(
        "--languages",
        nargs="+",
        default=[code for code in i18n.LANGUAGES if code != i18n.SOURCE_LANGUAGE],
        help="Language codes to fill (default: every shipped language).",
    )
    args = parser.parse_args(argv)

    if args.catalog == "ui":
        directory = i18n.UI_DIR
        sources = set(i18n.UI_STRINGS)
        print(f"{len(sources)} interface string(s)")
    else:
        directory = i18n.CONTENT_DIR
        config = yaml.safe_load(args.config.read_text(encoding="utf-8"))
        sources = collect_sources(config) | set(i18n.UI_STRINGS)
        print(f"{len(sources)} string(s) in {args.config} and the interface")

    try:
        sync(args.url.rstrip("/"), args.api_key, sources, args.languages, directory)
    except BackendError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
