import logging
import os

import requests
import yaml
from flask import Flask, current_app, render_template, url_for
from markupsafe import Markup

try:
    from app.utils.asset_resolver import asset_src, resolve_asset_cache
    from app.utils.cache_manager import CacheManager
    from app.utils.compute_card_classes import compute_card_classes
    from app.utils.configuration_resolver import ConfigurationResolver
except ImportError:  # pragma: no cover - supports running from the app/ directory.
    from utils.asset_resolver import asset_src, resolve_asset_cache
    from utils.cache_manager import CacheManager
    from utils.compute_card_classes import compute_card_classes
    from utils.configuration_resolver import ConfigurationResolver

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


@app.route("/")
def index():
    """Render the main index page."""
    cards = app.config["cards"]
    lg_classes, md_classes = compute_card_classes(cards)
    apod_bg = None
    api_key = app.config.get("NASA_API_KEY")
    if api_key:
        resp = requests.get(
            "https://api.nasa.gov/planetary/apod",
            params={"api_key": api_key},
            timeout=10,
        )
        if resp.ok:
            data = resp.json()
            if data.get("media_type") == "image":
                apod_bg = data.get("url")

    return render_template(
        "pages/index.html.j2",
        cards=cards,
        company=app.config["company"],
        navigation=app.config["navigation"],
        platform=app.config["platform"],
        lg_classes=lg_classes,
        md_classes=md_classes,
        apod_bg=apod_bg,
    )


if __name__ == "__main__":
    app.run(
        debug=(FLASK_ENV == "development"),
        host=FLASK_HOST,
        port=FLASK_PORT,
        use_reloader=False,
    )
