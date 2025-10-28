import json
from pynput.keyboard import Key
from src.utils.path import get_data_dir

CONFIG_FILE = get_data_dir() / "config" / "settings.json"

# Collect all special keys from pynput dynamically
VALID_SPECIAL_KEYS = {
    k.lower(): getattr(Key, k) for k in dir(Key) if not k.startswith("_")
}

# Add A–Z and 0–9 characters
VALID_CHAR_KEYS = {chr(i).upper(): chr(i).lower() for i in range(65, 91)}
VALID_CHAR_KEYS.update({str(i): str(i) for i in range(0, 10)})

DEFAULT_START_KEY = "F9"
DEFAULT_STOP_KEY = "F10"

DEFAULT_KEYS = {
    "start_key": "F9",
    "stop_key": "F10",
    "rods_key": "M",
    "bait_key": "N",
    "fish_key": "F",
    "esc_key": "ESC",
}


def load_config():
    """Load JSON config safely."""
    try:
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_config(config):
    """Save config safely to file."""
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)


def key_to_str(key):
    """Convert a pynput Key or character into a string for JSON storage."""
    if isinstance(key, Key):
        return key.name.upper()
    if hasattr(key, "char") and key.char:
        return key.char.upper()
    if isinstance(key, str):
        return key.upper()
    return str(key).upper()


def resolve_key(key_name: str):
    """Convert a string (from JSON or user) into a pynput key object or character."""
    if not key_name:
        return None

    key_name = key_name.strip().lower()

    # Match special keys (like f1, esc, enter)
    if key_name in VALID_SPECIAL_KEYS:
        return VALID_SPECIAL_KEYS[key_name]

    # Match regular letters or digits
    if key_name.upper() in VALID_CHAR_KEYS:
        return VALID_CHAR_KEYS[key_name.upper()]

    return None


def get_keys():
    """Return start and stop keys as pynput key objects."""
    config = load_config()
    start_str = config.get("start_key", DEFAULT_START_KEY)
    stop_str = config.get("stop_key", DEFAULT_STOP_KEY)
    start_key = resolve_key(start_str) or resolve_key(DEFAULT_START_KEY)
    stop_key = resolve_key(stop_str) or resolve_key(DEFAULT_STOP_KEY)
    return start_key, stop_key


def set_keys(start_key_str, stop_key_str):
    """Validate and save key bindings to JSON."""
    config = load_config()

    if not resolve_key(start_key_str):
        raise ValueError(f"Invalid start key: {start_key_str}")
    if not resolve_key(stop_key_str):
        raise ValueError(f"Invalid stop key: {stop_key_str}")

    config["start_key"] = start_key_str.upper()
    config["stop_key"] = stop_key_str.upper()
    save_config(config)


def get_key(name: str):
    """Get any key from config by name (converted to pynput key)."""
    config = load_config()
    key_str = config.get(name)
    return resolve_key(key_str)


def set_key(name: str, key_value):
    """Save any key (pynput or str) to config."""
    config = load_config()
    config[name] = key_to_str(key_value)
    save_config(config)
