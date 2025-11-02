from src.utils.path import get_data_dir
import json

TARGET_IMAGES_FOLDER = "images"

BASE = get_data_dir()
SETTINGS_FILE = BASE / "config/settings.json"

DEFAULT_SETTINGS = {
    "resolution": "1920x1080",
    "auto_bait_purchase": "T1",
    "auto_rods_purchase": "T1",
    "start_key": "F9",
    "stop_key": "F10",
    "rods_key": "M",
    "bait_key": "N",
    "fish_key": "F",
    "esc_key": "ESC",
}


def get_resolution_folder():
    return get_settings()["resolution"]


def get_settings():
    if SETTINGS_FILE.exists():
        try:
            with open(SETTINGS_FILE, "r") as f:
                user_settings = json.load(f)
                return {**DEFAULT_SETTINGS, **user_settings}
        except json.JSONDecodeError:
            return DEFAULT_SETTINGS.copy()
    # Return default if file missing or corrupted
    return DEFAULT_SETTINGS.copy()
