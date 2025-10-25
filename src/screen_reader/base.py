from src.utils.path import get_data_dir
import json
TARGET_IMAGES_FOLDER = "images"

BASE = get_data_dir()
SETTINGS_FILE = BASE / "config/settings.json"

DEFAULT_SETTINGS = {
    "resolution": "1600x900",
    "auto_bait_purchase": "T1",
    "auto_rods_purchase": "T1",
    "start_key": "T9",
    "stop_key": "F10",
}

def get_resolution_folder():
    return get_settings()["resolution"]

def get_settings():
    if SETTINGS_FILE.exists():
        try:
            with open(SETTINGS_FILE, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            pass
    # Return default if file missing or corrupted
    return DEFAULT_SETTINGS.copy()
