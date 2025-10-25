import webview
from src.utils.keybinds import get_keys, set_keys, DEFAULT_START_KEY, DEFAULT_STOP_KEY, KEY_MAP

def get_window(title):
    for w in webview.windows:
        if w.title == title:
            return w

def get_all_windows():
    return webview.windows

class OverviewApi:
    def __init__(self):
        self.start_key, self.stop_key = get_keys()

    def start_bot(self):
        print("Bot started")
        return "running"

    def stop_bot(self):
        print("Bot stopped")
        return "stopped"

    def minimize_window(self):
        w = get_window("bpsr-fishing Overlay")
        if w:
            w.minimize()
        return "minimized"

    def close_window(self):
        for window in get_all_windows()[:]:
            window.destroy()
        return "closed"

    # Key methods
    def get_start_key(self):
        var = self.start_key.name if hasattr(self.start_key, "name") else str(self.start_key)
        return var

    def get_stop_key(self):
        return self.stop_key.name if hasattr(self.stop_key, "name") else str(self.stop_key)

    def set_start_key(self, key_str):
        self.start_key = KEY_MAP.get(key_str, self.start_key)
        set_keys(key_str, self.get_stop_key())
        return key_str

    def set_stop_key(self, key_str):
        self.stop_key = KEY_MAP.get(key_str, self.stop_key)
        set_keys(self.get_start_key(), key_str)
        return key_str
