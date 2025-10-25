import webview
from pathlib import Path
from src.utils.path import get_data_dir
from src.ui.stats_api import StatsApi
from src.ui.overview_api import OverviewApi

BASE = get_data_dir()
HTML_PATH = BASE / "html"

class Window:
    STATS = "stats"
    OVERLAY = "overlay"

windows = {}

def start_ui():
    api = StatsApi()
    overview_api = OverviewApi()

    with open(HTML_PATH / "overlay.html", "r", encoding="utf-8") as f:
        overlay_html = f.read()
    with open(HTML_PATH / "main.html", "r", encoding="utf-8") as f:
        main_html = f.read()

    windows[Window.STATS] = webview.create_window(
        "bpsr-fishing Stats",
        html=main_html,
        js_api=api,
        width=800,
        height=600,
        min_size=(400, 300),
        resizable=True,
        frameless=False,
        transparent=True,
        minimized=True,
    )

    windows[Window.OVERLAY] = webview.create_window(
        "bpsr-fishing Overlay",
        html=overlay_html,
        js_api=overview_api,
        width=300,
        height=150,
        resizable=True,
        frameless=True,
        transparent=True,
        on_top=True,
        x=0,
        y=0
    )

    webview.start(debug=True, http_server=False)


def get_window(window_enum: str):
    return windows.get(window_enum)


if __name__ == "__main__":
    start_ui()
