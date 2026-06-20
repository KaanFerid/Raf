import os
import json

CONFIG_PATH = os.path.abspath(os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
    "mock_system" if os.environ.get("KITAPMARKT_DEV") == "1" else os.path.expanduser("~/.config/kitapmarkt"),
    "config.json"
))

def load_config():
    if not os.path.exists(CONFIG_PATH):
        os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
        default_config = {"theme_mode": "system"} # "system", "light", "dark"
        save_config(default_config)
        return default_config
    try:
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {"theme_mode": "system"}

def save_config(config):
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    try:
        with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2)
    except Exception as e:
        print(f"Error saving config: {e}")
