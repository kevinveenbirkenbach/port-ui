import os
from flask import Flask, render_template
import yaml
import requests
from utils.configuration_resolver import ConfigurationResolver
from utils.cache_manager import CacheManager
from utils.compute_card_classes import compute_card_classes
import logging
logging.basicConfig(level=logging.DEBUG)
FLASK_ENV = os.getenv("FLASK_ENV", "production")
FLASK_PORT = int(os.getenv("PORT", 5000))
print(f"🔧 Starting app on port {FLASK_PORT}, FLASK_ENV={FLASK_ENV}")

from flask import current_app
from markupsafe import Markup

# Initialize the CacheManager
cache_manager = CacheManager()

# Clear cache on startup
cache_manager.clear_cache()

def load_config(app):
    """Load and resolve the configuration from config.yaml."""
    with open("config.yaml", "r") as f:
        config = yaml.safe_load(f)

    if config.get("nasa_api_key"):
        app.config["NASA_API_KEY"] = config["nasa_api_key"]

    resolver = ConfigurationResolver(config)
    resolver.resolve_links()
    app.config.update(resolver.get_config())

def cache_icons_and_logos(app):
    """Cache all icons and logos to local files, mit Fallback auf source."""
    for card in app.config["cards"]:
        icon = card.get("icon", {})
        if icon.get("source"):
            cached = cache_manager.cache_file(icon["source"])
            # Fallback: wenn cache_file None liefert, nutze weiterhin source
            icon["cache"] = cached or icon["source"]

    # Company-Logo
    company_logo = app.config["company"]["logo"]
    cached = cache_manager.cache_file(company_logo["source"])
    company_logo["cache"] = cached or company_logo["source"]

    # Platform Favicon
    favicon = app.config["platform"]["favicon"]
    cached = cache_manager.cache_file(favicon["source"])
    favicon["cache"] = cached or favicon["source"]

    # Platform Logo
    platform_logo = app.config["platform"]["logo"]
    cached = cache_manager.cache_file(platform_logo["source"])
    platform_logo["cache"] = cached or platform_logo["source"]


# Initialize Flask app
app = Flask(__name__)

# Load configuration and cache assets on startup
load_config(app)
cache_icons_and_logos(app)

@app.context_processor
def utility_processor():
    def include_svg(path):
        full_path = os.path.join(current_app.root_path, 'static', path)
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                svg = f.read()
            return Markup(svg)
        except IOError:
            return Markup(f'<!-- SVG not found: {path} -->')
    return dict(include_svg=include_svg)

@app.before_request
def reload_config_in_dev():
    """Reload config and recache icons before each request in development mode."""
    if FLASK_ENV == "development":
        load_config(app)
        cache_icons_and_logos(app)

@app.route('/')
def index():
    """Render the main index page."""
    cards = app.config["cards"]
    lg_classes, md_classes = compute_card_classes(cards)
    # fetch NASA APOD URL only if key present
    apod_bg = None
    api_key = app.config.get("NASA_API_KEY")
    if api_key:
        resp = requests.get(
            "https://api.nasa.gov/planetary/apod",
            params={"api_key": api_key}
        )
        if resp.ok:
            data = resp.json()
            # only use if it's an image
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
        apod_bg=apod_bg
    )

if __name__ == "__main__":
    app.run(debug=(FLASK_ENV == "development"), host="0.0.0.0", port=FLASK_PORT)
