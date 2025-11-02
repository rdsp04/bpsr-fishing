import webview
from enum import Enum

windows = {}

class Window(Enum):
    MAIN = "main"
    OVERLAY = "overlay"


def get_window(window_type: Window):
    return windows.get(window_type.value)


def start_ui():
    from src.ui.stats_api import StatsApi
    from src.ui.overview_api import OverviewApi
    from src.utils.path import get_data_dir

    BASE = get_data_dir()
    HTML_PATH = BASE / "html"

    api = StatsApi()
    overview_api = OverviewApi()

    with open(HTML_PATH / "overlay.html", "r", encoding="utf-8") as f:
        overlay_html = f.read()
    with open(HTML_PATH / "main.html", "r", encoding="utf-8") as f:
        main_html = f.read()

    main_window = webview.create_window(
        "bpsr-fishing Stats",
        html=main_html,
        js_api=api,
        width=940,
        height=600,
        min_size=(900, 600),
        resizable=True,
        frameless=False,
        transparent=False,
        minimized=False,
    )
    windows[Window.MAIN.value] = main_window

    overlay_window = webview.create_window(
        "bpsr-fishing Overlay",
        html=overlay_html,
        js_api=overview_api,
        frameless=True,
        transparent=False,
        easy_drag=True,
        width=310,
        height=170,
        resizable=False,
        on_top=True
    )
    windows[Window.OVERLAY.value] = overlay_window



    webview.start(debug=False)
