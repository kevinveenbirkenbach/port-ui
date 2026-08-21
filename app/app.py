import logging
import os

import requests
import yaml
from flask import Flask, current_app, make_response, render_template, request, url_for
from markupsafe import Markup
from werkzeug.middleware.proxy_fix import ProxyFix

try:
    from app.utils import i18n
    from app.utils.asset_resolver import asset_src, resolve_asset_cache
    from app.utils.cache_manager import CacheManager
    from app.utils.compute_card_classes import compute_card_classes
    from app.utils.configuration_resolver import ConfigurationResolver
except ImportError:  # pragma: no cover - supports running from the app/ directory.
    from utils.asset_resolver import asset_src, resolve_asset_cache
    from utils.cache_manager import CacheManager
    from utils.compute_card_classes import compute_card_classes
    from utils.configuration_resolver import ConfigurationResolver

    from utils import i18n

TRANSLATED_SECTIONS = ("cards", "company", "navigation", "platform")

logging.basicConfig(level=logging.DEBUG)

FLASK_ENV = os.getenv("FLASK_ENV", "production")
FLASK_HOST = os.getenv("FLASK_HOST", "127.0.0.1")
FLASK_PORT = int(os.getenv("FLASK_PORT", os.getenv("PORT", 5000)))
print(f"Starting app on {FLASK_HOST}:{FLASK_PORT}, FLASK_ENV={FLASK_ENV}")

# Initialize the CacheManager
cache_manager = CacheManager()

# Clear cache on startup
cache_manager.clear_cache()


def load_config(app):
    """Load and resolve the configuration from config.yaml."""
    with open("config.yaml", "r", encoding="utf-8") as handle:
        config = yaml.safe_load(handle)

    if config.get("nasa_api_key"):
        app.config["NASA_API_KEY"] = config["nasa_api_key"]

    resolver = ConfigurationResolver(config)
    resolver.resolve_links()
    app.config.update(resolver.get_config())
    app.config["TRANSLATED_CONFIG"] = {}
    i18n.clear_catalogs()


def cache_icons_and_logos(app):
    """Resolve every icon/logo/favicon to either a local cache path or
    an external URL (see ``resolve_asset_cache``)."""
    for card in app.config["cards"]:
        icon = card.get("icon")
        if icon:
            resolve_asset_cache(icon, cache_manager)

    resolve_asset_cache(app.config["company"]["logo"], cache_manager)
    resolve_asset_cache(app.config["platform"]["favicon"], cache_manager)
    resolve_asset_cache(app.config["platform"]["logo"], cache_manager)


# Initialize Flask app
app = Flask(__name__)

app.jinja_options = {**app.jinja_options, "autoescape": True}

app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1)


def trusted_hosts(raw):
    """Parse a comma-separated host list, or None when nothing is configured.

    Args:
        raw: the ``TRUSTED_HOSTS`` value, possibly empty.
    """
    hosts = [host.strip() for host in raw.split(",") if host.strip()]
    return hosts or None


app.config["TRUSTED_HOSTS"] = trusted_hosts(os.getenv("TRUSTED_HOSTS", ""))

# Load configuration and cache assets on startup
load_config(app)
cache_icons_and_logos(app)


@app.context_processor
def utility_processor():
    def include_svg(path):
        full_path = os.path.join(current_app.root_path, "static", path)
        try:
            with open(full_path, "r", encoding="utf-8") as handle:
                svg = handle.read()
            # Trusted local SVG asset shipped with the application package.
            return Markup(svg)  # nosec B704
        except OSError:
            return ""

    def template_asset_src(asset):
        return asset_src(asset, lambda filename: url_for("static", filename=filename))

    return dict(include_svg=include_svg, asset_src=template_asset_src)


@app.before_request
def reload_config_in_dev():
    """Reload config and recache icons before each request in development mode."""
    if FLASK_ENV == "development":
        load_config(app)
        cache_icons_and_logos(app)


def translated_config(lang):
    """Return the configuration sections translated into ``lang``, memoized.

    The memo is dropped by ``load_config``, so a development reload picks up
    edited content on the next request.
    """
    memo = app.config["TRANSLATED_CONFIG"]
    if lang not in memo:
        source = {section: app.config[section] for section in TRANSLATED_SECTIONS}
        memo[lang] = i18n.translate_tree(source, lang)
    return memo[lang]


def apod_background():
    """Return today's NASA APOD image URL, or None when unavailable."""
    api_key = app.config.get("NASA_API_KEY")
    if not api_key:
        return None

    try:
        resp = requests.get(
            "https://api.nasa.gov/planetary/apod",
            params={"api_key": api_key},
            timeout=10,
        )
    except requests.RequestException:
        logging.warning("APOD lookup failed", exc_info=True)
        return None

    if not resp.ok:
        return None

    data = resp.json()
    return data.get("url") if data.get("media_type") == "image" else None


def render_index(lang):
    """Render the index page in ``lang``."""
    config = translated_config(lang)
    cards = config["cards"]
    lg_classes, md_classes = compute_card_classes(cards)

    return render_template(
        "pages/index.html.j2",
        cards=cards,
        company=config["company"],
        navigation=config["navigation"],
        platform=config["platform"],
        lg_classes=lg_classes,
        md_classes=md_classes,
        apod_bg=apod_background(),
        lang=lang,
        lang_dir=i18n.direction(lang),
        languages=i18n.LANGUAGES,
        ui_strings=i18n.ui_strings(lang),
        t=lambda source: i18n.catalog(lang).get(source, source),
    )


@app.route("/")
def index():
    """Render the index page in the language the browser asks for."""
    response = make_response(render_index(i18n.negotiate(request.accept_languages)))
    response.headers["Vary"] = "Accept-Language"
    return response


@app.route(f"/<any({','.join(i18n.LANGUAGES)}):lang>/")
def localized_index(lang):
    """Render the index page in an explicitly requested language."""
    return render_index(lang)


if __name__ == "__main__":
    app.run(
        debug=(FLASK_ENV == "development"),
        host=FLASK_HOST,
        port=FLASK_PORT,
        use_reloader=False,
    )
