"""Language negotiation and translation of the resolved configuration tree.

Translation is catalogue-driven: a string is replaced only when the target
language's catalogue holds an entry for the exact English source string.
Anything unknown falls through to English, so a partially filled catalogue
degrades instead of breaking.
"""

import logging
from pathlib import Path

import yaml

I18N_DIR = Path(__file__).resolve().parent.parent / "i18n"
UI_DIR = I18N_DIR / "ui"
CONTENT_DIR = I18N_DIR / "content"

SOURCE_LANGUAGE = "en"

LANGUAGES = {
    "en": "English",
    "zh": "中文",
    "hi": "हिन्दी",
    "es": "Español",
    "fr": "Français",
    "ar": "العربية",
    "bn": "বাংলা",
    "pt": "Português",
    "ru": "Русский",
    "ur": "اردو",
    "id": "Bahasa Indonesia",
    "de": "Deutsch",
    "ja": "日本語",
    "tr": "Türkçe",
    "ko": "한국어",
    "vi": "Tiếng Việt",
    "it": "Italiano",
    "th": "ไทย",
    "pl": "Polski",
    "nl": "Nederlands",
    "uk": "Українська",
    "fa": "فارسی",
    "ro": "Română",
    "el": "Ελληνικά",
    "cs": "Čeština",
    "sv": "Svenska",
    "hu": "Magyar",
    "he": "עברית",
    "da": "Dansk",
    "fi": "Suomi",
}

RTL_LANGUAGES = frozenset({"ar", "fa", "he", "ur"})

AUTOFILL_KEYS = frozenset({"description", "text", "warning", "info", "subtitel"})

TRANSLATABLE_KEYS = AUTOFILL_KEYS | frozenset({"name", "title"})

UI_STRINGS = (
    "Alternatives",
    "Close",
    "Copy",
    "Identifier copied to clipboard!",
    "Imprint",
    "Information",
    "Language",
    "Open",
    "Open Link",
    "Options",
    "Warning",
)

_catalogs: dict[str, dict[str, str]] = {}


def direction(code):
    """Return the writing direction of ``code`` as an HTML ``dir`` value."""
    return "rtl" if code in RTL_LANGUAGES else "ltr"


def read_catalog(path):
    """Return the catalogue at ``path``, or an empty one if it is unusable.

    Catalogues are hand-edited and machine-written, so a stray character must
    degrade that language to English rather than take every page down with a
    parse error. Non-string entries are dropped for the same reason: they would
    otherwise reach the templates and render as ``42`` or ``null``.
    """
    if not path.exists():
        return {}
    try:
        loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, yaml.YAMLError):
        logging.warning("Ignoring unreadable translation catalogue: %s", path)
        return {}
    if not isinstance(loaded, dict):
        logging.warning(
            "Ignoring translation catalogue that is not a mapping: %s", path
        )
        return {}
    return {
        key: value
        for key, value in loaded.items()
        if isinstance(key, str) and isinstance(value, str)
    }


def clear_catalogs():
    """Drop the memoized catalogues so edited files are picked up."""
    _catalogs.clear()


def catalog(code):
    """Return the merged UI and content catalogue for ``code``."""
    if code not in _catalogs:
        _catalogs[code] = {
            **read_catalog(UI_DIR / f"{code}.yaml"),
            **read_catalog(CONTENT_DIR / f"{code}.yaml"),
        }
    return _catalogs[code]


def negotiate(accepted, default=SOURCE_LANGUAGE):
    """Pick the best supported language from ``Accept-Language`` pairs.

    Args:
        accepted: iterable of ``(tag, quality)`` as produced by
            ``flask.request.accept_languages``.
        default: language returned when no tag is supported.

    Werkzeug's own ``best_match`` returns an exact match before it considers
    primary-tag fallbacks, so ``de-DE,en;q=0.8`` resolves to English. Matching
    on the primary subtag up front avoids that.
    """
    best, best_quality = default, 0.0
    for tag, quality in accepted:
        code = tag.replace("_", "-").split("-")[0].lower()
        if code in LANGUAGES and quality > best_quality:
            best, best_quality = code, quality
    return best


def translate_tree(node, code, key=None):
    """Return a copy of ``node`` with translatable leaves swapped for ``code``.

    Args:
        node: the resolved configuration tree, or any subtree of it.
        code: target language code.
        key: the mapping key ``node`` was reached through.
    """
    if isinstance(node, dict):
        return {name: translate_tree(value, code, name) for name, value in node.items()}
    if isinstance(node, list):
        return [translate_tree(item, code, key) for item in node]
    if isinstance(node, str) and key in TRANSLATABLE_KEYS:
        return catalog(code).get(node, node)
    return node


def ui_strings(code):
    """Return the interface strings for ``code``, keyed by their English source."""
    entries = catalog(code)
    return {source: entries.get(source, source) for source in UI_STRINGS}
