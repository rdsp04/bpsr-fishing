import json
from pynput.keyboard import Key
from pynput import keyboard
from src.utils.path import get_data_dir
import string

CONFIG_FILE = get_data_dir() / "config" / "settings.json"

# Collect all special keys from pynput dynamically
VALID_SPECIAL_KEYS = {
    k.lower(): getattr(Key, k) for k in dir(Key) if not k.startswith("_")
}

SPECIAL_KEYS = {k.upper(): getattr(Key, k) for k in dir(Key) if not k.startswith("_")}
PRINTABLE_KEYS = {
    c: c for c in string.printable if c not in string.whitespace or c == " "
}
DIGIT_KEYS = {str(i): str(i) for i in range(10)}

# Combine all into one dictionary
ALL_KEYS = {**SPECIAL_KEYS, **PRINTABLE_KEYS, **DIGIT_KEYS}
mapper_list = [{"key": str(ALL_KEYS[k]), "name": k} for k in ALL_KEYS]

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
    if key_name in ALL_KEYS:
        return ALL_KEYS[key_name]

    # Match regular letters or digits
    if key_name.upper() in ALL_KEYS:
        return ALL_KEYS[key_name.upper()]

    return None


def get_keys():
    """Return start and stop keys as pynput key objects."""
    config = load_config()
    start_str = config.get("start_key", DEFAULT_START_KEY)
    stop_str = config.get("stop_key", DEFAULT_STOP_KEY)

    return resolve_key(start_str), resolve_key(stop_str)


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
    """Get any key from config by name as a string."""
    config = load_config()
    return config.get(name, DEFAULT_KEYS.get(name))



def set_key(name: str, key_value):
    """Save any key (pynput or str) to config."""
    if name not in DEFAULT_KEYS:
        raise ValueError(f"Invalid setting name: {name}")

    key_str = key_to_str(key_value)
    config = load_config()
    config[name] = key_str
    save_config(config)


def capture_and_set_key(setting_name: str) -> str:
    """
    Listen for the next key press, save it to config under the given setting name,
    and return the string representation of the key.
    """
    if setting_name not in DEFAULT_KEYS:
        raise ValueError(f"Invalid setting name: {setting_name}")

    key_pressed = {}

    def on_press(key):
        # Convert key to string
        key_str = key_to_str(key)
        # Save to config
        set_key(setting_name, key)
        # Store it to return
        key_pressed["key_str"] = key_str
        # Stop listener
        return False

    with keyboard.Listener(on_press=on_press) as listener:
        listener.join()

    return key_pressed.get("key_str")
