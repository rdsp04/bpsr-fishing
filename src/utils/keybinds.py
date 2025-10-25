import json
from pynput.keyboard import Key
from src.utils.path import get_data_dir
CONFIG_FILE = get_data_dir() / "config" / "settings.json"

KEY_MAP = {
    "F1": Key.f1,
    "F2": Key.f2,
    "F3": Key.f3,
    "F4": Key.f4,
    "F5": Key.f5,
    "F6": Key.f6,
    "F7": Key.f7,
    "F8": Key.f8,
    "F9": Key.f9,
    "F10": Key.f10,
    "F11": Key.f11,
    "F12": Key.f12,
}

DEFAULT_START_KEY = "F9"
DEFAULT_STOP_KEY = "F10"

def load_config():
    try:
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_config(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)

def get_keys():
    config = load_config()
    start_str = config.get("start_key", DEFAULT_START_KEY)
    stop_str = config.get("stop_key", DEFAULT_STOP_KEY)
    return KEY_MAP.get(start_str, Key.f9), KEY_MAP.get(stop_str, Key.f10)

def set_keys(start_key_str, stop_key_str):
    config = load_config()
    config["start_key"] = start_key_str
    config["stop_key"] = stop_key_str
    save_config(config)
