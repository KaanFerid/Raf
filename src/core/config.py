import os
import json

CONFIG_PATH = os.path.abspath(
    os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        (
            "mock_system"
            if os.environ.get("RAF_DEV") == "1"
            else os.path.expanduser("~/.config/raf")
        ),
        "config.json",
    )
)


def load_config():
    if not os.path.exists(CONFIG_PATH):
        os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
        default_config = {
            "theme_mode": "system",
            "language": "tr",
        }  # "system", "light", "dark"
        save_config(default_config)
        return default_config
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"theme_mode": "system", "language": "tr"}


def save_config(config):
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    try:
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)
    except Exception as e:
        from src.core.translation import tr

        print(tr("log.error_saving_config", error=e))


def get_cached_package_name(book_id):
    """Retrieves the exact package name mapped to a book ID from configuration."""
    config = load_config()
    return config.get("package_names", {}).get(book_id)


def set_cached_package_name(book_id, package_name):
    """Saves the resolved package name for a book ID to avoid guessing in the future."""
    config = load_config()
    if "package_names" not in config:
        config["package_names"] = {}
    config["package_names"][book_id] = package_name
    save_config(config)


def get_last_update_check():
    """Returns the UNIX timestamp of the last update check (0.0 if never checked)."""
    config = load_config()
    return float(config.get("last_update_check", 0.0))


def set_last_update_check(timestamp):
    """Stores the UNIX timestamp of the most recent update check."""
    config = load_config()
    config["last_update_check"] = timestamp
    save_config(config)
