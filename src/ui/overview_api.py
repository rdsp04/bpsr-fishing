import webview
from src.utils.keybinds import (
    get_keys,
    set_keys,
    resolve_key,
    key_to_str,
)
from main import handle_start_key, handle_stop_key

def get_window(title):
    for w in webview.windows:
        if w.title == title:
            return w

def get_all_windows():
    return webview.windows

class OverviewApi:
    def __init__(self):
        self.start_key, self.stop_key = get_keys()

    def start_script(self):
        handle_start_key()

    def stop_script(self):
        handle_stop_key()

    def minimize_window(self):
        w = get_window("bpsr-fishing Overlay")
        if w:
            w.minimize()
        return "minimized"

    def close_window(self):
        for window in get_all_windows()[:]:
            window.destroy()
        return "closed"

   # --- Generic key conversion helpers ---
    def _key_to_str(self, key_obj):
        return key_to_str(key_obj)

    def _str_to_key(self, key_str, fallback=None):
        resolved = resolve_key(key_str)
        return resolved or fallback

    # --- Start/Stop keys ---
    def get_start_key(self):
        return self._key_to_str(self.start_key)

    def get_stop_key(self):
        return self._key_to_str(self.stop_key)

    def set_start_key(self, key_str):
        new_key = self._str_to_key(key_str, self.start_key)
        self.start_key = new_key
        set_keys(key_str, self.get_stop_key())
        return key_str

    def set_stop_key(self, key_str):
        new_key = self._str_to_key(key_str, self.stop_key)
        self.stop_key = new_key
        set_keys(self.get_start_key(), key_str)
        return key_str
