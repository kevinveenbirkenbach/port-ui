"""View model of the optional ``dashboard`` configuration section."""

import datetime
import re

SLUG = re.compile(r"^[a-z0-9-]+$")


def walk(folders, parent):
    """Yield ``(path, parent, folder)`` for every folder of a tree, depth first.

    Args:
        folders: list of folder mappings with a ``slug`` and optional ``children``.
        parent: path of the folder holding ``folders``, ``""`` at the top level.
    """
    if not isinstance(folders, list):
        raise ValueError(
            f"dashboard folders below {parent or 'the top'} must be a list"
        )
    for folder in folders:
        slug = folder.get("slug") if isinstance(folder, dict) else None
        if not isinstance(slug, str) or not SLUG.match(slug):
            raise ValueError(f"dashboard folder slug {slug!r} must match [a-z0-9-]+")
        if not isinstance(folder.get("name"), str):
            raise ValueError(f"dashboard folder {slug!r} needs a name")
        if "icon" in folder and not (
            isinstance(folder["icon"], dict)
            and isinstance(folder["icon"].get("class"), str)
        ):
            raise ValueError(f"dashboard folder {slug!r} icon must be {{class: ...}}")
        path = f"{parent}/{slug}" if parent else slug
        yield path, parent, folder
        if "children" in folder:
            yield from walk(folder["children"], path)


def _string_list(value, what):
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ValueError(f"{what} must be a list of strings")
    return value


def _iso_date(value, what):
    if isinstance(value, datetime.datetime):
        return value.date().isoformat()
    if isinstance(value, datetime.date):
        return value.isoformat()
    if isinstance(value, str):
        try:
            return datetime.date.fromisoformat(value).isoformat()
        except ValueError:
            pass
    raise ValueError(f"{what} must be an ISO date, got {value!r}")


def _positive_number(section, key, what):
    value = section.get(key)
    if isinstance(value, bool) or not isinstance(value, (int, float)) or value <= 0:
        raise ValueError(f"{what}.{key} must be a positive number")


def validate(config):
    """Raise ``ValueError`` when the ``dashboard`` section or its card fields are bad.

    Args:
        config: the resolved, untranslated configuration.
    """
    section = config.get("dashboard")
    if section is None:
        return
    if not isinstance(section, dict):
        raise ValueError("dashboard must be a mapping")

    paths = set()
    if "folders" in section:
        for path, _, _ in walk(section["folders"], ""):
            if path in paths:
                raise ValueError(f"dashboard folder path {path!r} is defined twice")
            paths.add(path)

    if "new_days" in section:
        _positive_number(section, "new_days", "dashboard")

    ids = set()
    for index, card in enumerate(config["cards"]):
        what = f"cards[{index}]"
        if "id" in card:
            if not isinstance(card["id"], str):
                raise ValueError(f"{what}.id must be a string")
            if card["id"] in ids:
                raise ValueError(f"{what}.id {card['id']!r} is used twice")
            ids.add(card["id"])
        if "tags" in card:
            _string_list(card["tags"], f"{what}.tags")
        if "added" in card:
            _iso_date(card["added"], f"{what}.added")
        if "folders" in card and "folders" in section:
            for path in _string_list(card["folders"], f"{what}.folders"):
                if path not in paths:
                    raise ValueError(f"{what}.folders names unknown folder {path!r}")


def _prefixes(path):
    parts = path.split("/")
    return ["/".join(parts[: depth + 1]) for depth in range(len(parts))]


def _unique(values):
    return list(dict.fromkeys(value for value in values if value))


def locate(model, requested):
    """Return the open folder path and its breadcrumb trail as ``(path, name)`` pairs.

    Args:
        model: the view model returned by ``build``.
        requested: the ``folder`` query value; None or an unknown path opens the top.
    """
    names = {folder["path"]: folder["name"] for folder in model["folders"]}
    if requested not in names:
        return "", []
    return requested, [(prefix, names[prefix]) for prefix in _prefixes(requested)]


def build(translated, source):
    """Return the dashboard view model, or None when there is no ``dashboard`` section.

    Args:
        translated: configuration sections translated into the page language.
        source: the same sections untranslated, so search also matches English.
    """
    section = translated.get("dashboard")
    if section is None:
        return None
    english = source["dashboard"]
    folder_view = "folders" in section

    folders = {}
    if folder_view:
        pairs = zip(walk(section["folders"], ""), walk(english["folders"], ""))
        for (path, parent, folder), (_, _, folder_en) in pairs:
            folders[path] = {
                "path": path,
                "parent": parent,
                "name": folder["name"],
                "name_en": folder_en["name"],
                "description": folder.get("description"),
                "icon": (folder.get("icon") or {}).get("class"),
                "members": set(),
            }

    cards = []
    for index, (card, card_en) in enumerate(zip(translated["cards"], source["cards"])):
        paths = card.get("folders", []) if folder_view else []
        ancestry = _unique(prefix for path in paths for prefix in _prefixes(path))
        for prefix in ancestry:
            folders[prefix]["members"].add(index)
        cards.append(
            {
                "key": card.get("id"),
                "title": card.get("title"),
                "folders": paths,
                "added": _iso_date(card["added"], "added") if "added" in card else None,
                "search": _unique(
                    [
                        card.get("title"),
                        card_en.get("title"),
                        card.get("text"),
                        card_en.get("text"),
                        *card.get("tags", []),
                        *(folders[prefix]["name"] for prefix in ancestry),
                        *(folders[prefix]["name_en"] for prefix in ancestry),
                    ]
                ),
                "title_en": card_en.get("title"),
            }
        )

    visible = []
    for folder in folders.values():
        folder["count"] = len(folder.pop("members"))
        if folder["count"]:
            visible.append(folder)

    return {
        "folder_view": folder_view,
        "folders": visible,
        "cards": cards,
        "client": {
            "folder_view": folder_view,
            "folders": {
                folder["path"]: {
                    "name": folder["name"],
                    "name_en": folder["name_en"],
                    "parent": folder["parent"],
                }
                for folder in visible
            },
            "cards": cards,
            "new_days": section.get("new_days"),
        },
    }
