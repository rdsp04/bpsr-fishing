import webview
from src.utils.path import get_data_dir

def get_window(title):
    for w in webview.windows:
        if w.title == title:
            return w

def get_all_windows():
    return webview.windows

class OverviewApi:
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
