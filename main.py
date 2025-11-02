import time
import os
import sys
import json
from datetime import datetime
from pynput.mouse import Controller, Button
from pynput.keyboard import Controller as KeyboardController, Listener, KeyCode, Key

from src.utils.updater import check_for_update, download_update, run_update, UpdateApi

update_api = UpdateApi()

from src.screen_reader.screen_service import ScreenService
from src.screen_reader.image_service import ImageService
from src.screen_reader.base import get_resolution_folder
from src.ui.ui_service import start_ui
import threading
from threading import Event

from log_main import load_sessions, save_sessions
from src.fish.fish_service import FishService

macro_start_event = Event()

# Services
screen_service = ScreenService()
image_service = ImageService()

# Globals
TARGET_IMAGES_FOLDER = "images"
saved_continue_pos = None
CHECK_INTERVAL = 0.05
THRESHOLD = 0.7
SPAM_CPS = 20
session_stats = {"catches": 0, "misses": 0, "xp": 0, "rate": 0.0}
from src.utils.keybinds import get_keys, key_to_str, get_pykey
from src.utils.path import get_data_dir

START_KEY, STOP_KEY = get_keys()
BASE = get_data_dir()
CONFIG_PATH = BASE / "config/fish_config.json"


mouse = Controller()
keyboard = KeyboardController()
fish_service = FishService(CONFIG_PATH)
fish_service.load_fishes()
macro_running = False


# ---------------- Logging ----------------
def log_broken_rod():
    filename = BASE / "logs" / "broken_rods.json"
    filename.parent.mkdir(parents=True, exist_ok=True)
    entry = {"timestamp": datetime.now().isoformat(), "broken": True}
    data = []
    if os.path.exists(filename):
        with open(filename, "r") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                data = []
    data.append(entry)
    with open(filename, "w") as f:
        json.dump(data, f, indent=2)


def log_catch(status, **extra):
    filename = BASE / "logs" / "fishing_log.json"
    filename.parent.mkdir(parents=True, exist_ok=True)
    entry = {"timestamp": datetime.now().isoformat(), "catch": status}
    entry.update(extra)
    data = []
    if os.path.exists(filename):
        with open(filename, "r") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                data = []
    data.append(entry)
    with open(filename, "w") as f:
        json.dump(data, f, indent=2)


def update_ui_stats():
    """Send current stats to overlay UI."""
    overlay = get_window(Window.OVERLAY)
    if overlay:
        overlay.evaluate_js(f"window.updateStats({json.dumps(session_stats)})")


# ---------------- Input ----------------
from src.ui.ui_service import get_window, Window


def handle_start_key():
    global macro_start_event, window_title

    overlay = get_window(Window.OVERLAY)
    sessions = load_sessions()

    window_title = select_window()
    if not window_title:
        print("No window found. Cannot start macro.")
        macro_start_event.clear()
        return

    if not sessions or sessions[-1].get("stop") is not None:
        sessions.append({"start": datetime.now().isoformat(), "stop": None})
        save_sessions(sessions)
        overlay.evaluate_js("window.toggleBotStatus('running');")
        macro_start_event.set()
        print(f"Macro started on window: {window_title}")
    else:
        print("Session already started. Press stop first.")


def handle_stop_key():
    global macro_start_event, saved_continue_pos, window_title

    overlay = get_window(Window.OVERLAY)
    sessions = load_sessions()

    if sessions and sessions[-1].get("stop") is None:
        sessions[-1]["stop"] = datetime.now().isoformat()
        save_sessions(sessions)
        macro_start_event.clear()
        saved_continue_pos = None
        window_title = None
        print("Macro stopped")
        overlay.evaluate_js("window.toggleBotStatus('stopped');")
    else:
        print("No active session to stop.")


def on_press(key):
    pressed_str = key_to_str(key)
    start_key_str, stop_key_str = map(key_to_str, get_keys())

    if pressed_str == start_key_str:
        handle_start_key()
    elif pressed_str == stop_key_str:
        handle_stop_key()


# ---------------- Window Handling ----------------

import win32gui


def focus_blue_protocol_window():
    target_title = "Blue Protocol: Star Resonance"
    hwnd = win32gui.FindWindow(None, target_title)
    if hwnd == 0:
        print(f"Window '{target_title}' not found.")
        return None
    try:
        win32gui.ShowWindow(hwnd, 5)
        win32gui.SetForegroundWindow(hwnd)
    except Exception as e:
        print(f"Failed to focus window: {e}")
    return hwnd


def select_window():
    hwnd = focus_blue_protocol_window()
    if hwnd:
        print("Automatically selected Blue Protocol window.")
        return "Blue Protocol: Star Resonance"
    else:
        print("Could not find Blue Protocol window. Waiting...")
        return None


def get_window_rect(title):
    hwnd = win32gui.FindWindow(None, title)
    if not hwnd:
        print(f"Window '{title}' not found.")
        return None
    return win32gui.GetWindowRect(hwnd)

# ---------------- Actions ----------------
def click(x, y):
    time.sleep(0.05)
    mouse.position = (x, y)
    mouse.click(Button.left, 1)


def press_key(key):
    select_window()
    time.sleep(0.05)
    keyboard.press(key)
    keyboard.release(key)


def hold_key(key):
    keyboard.press(key)


def release_key(key):
    keyboard.release(key)


# ---------------- Fishing Logic ----------------
last_progress_time = time.time()


def post_catch_loop(window_title):
    global macro_start_event, saved_continue_pos, last_progress_time
    print("Fish took the bait")
    last_progress_time = time.time()

    counter = 0
    last_print_time = time.time()
    last_check_time = time.time()
    mouse.press(Button.left)

    lane = 0
    while macro_start_event.is_set():
        if time.time() - last_progress_time > NO_PROGRESS_LIMIT:
            handle_no_progress_loop(window_title)

        counter += 1
        time.sleep(1 / SPAM_CPS)

        rect = get_window_rect(window_title)

        arrow, score = image_service.find_minigame_arrow(rect)

        if arrow is not None and "right" in arrow and score > 0.8:
            last_progress_time = time.time()

            lane += 1
            if lane > 1:
                lane = 1
            print(f"Right arrow detected, lane = {lane}")
            time.sleep(0.2)
        elif arrow is not None and "left" in arrow and score > 0.8:
            last_progress_time = time.time()

            lane -= 1
            if lane < -1:
                lane = -1
            print(f"Left arrow detected, lane = {lane}")
            time.sleep(0.2)

        if lane == -1:
            hold_key("a")
            release_key("d")
        elif lane == 0:
            release_key("a")
            release_key("d")
        elif lane == 1:
            hold_key("d")
            release_key("a")

        if time.time() - last_print_time >= 1:
            print(f"Held for {counter} ticks")
            last_print_time = time.time()

        if time.time() - last_check_time >= 0.3:
            continue_found = image_service.find_image_in_window(
                rect,
                (
                    get_data_dir()
                    / TARGET_IMAGES_FOLDER
                    / get_resolution_folder()
                    / "continue.png"
                ),
                0.8,
            )
            if not continue_found:
                continue_found = image_service.find_image_in_window(
                    rect,
                    (
                        get_data_dir()
                        / TARGET_IMAGES_FOLDER
                        / get_resolution_folder()
                        / "continue_highlighted.png"
                    ),
                    0.8,
                )
            default_found = image_service.find_image_in_window(
                rect,
                (
                    get_data_dir()
                    / TARGET_IMAGES_FOLDER
                    / get_resolution_folder()
                    / "default_screen.png"
                ),
                0.9,
            )
            last_check_time = time.time()

            if continue_found:
                last_progress_time = time.time()

                if saved_continue_pos is None:
                    saved_continue_pos = continue_found
                print("Continue button found, releasing click")
                mouse.release(Button.left)

                # === Fish Detection + Screenshot ===
                fish_folder = (
                    get_data_dir()
                    / TARGET_IMAGES_FOLDER
                    / get_resolution_folder()
                    / "fish"
                )
                fish_type = None

                if os.path.exists(fish_folder):
                    attempts = 3
                    fish_type = None
                    for i in range(attempts):
                        fish_type, score = image_service.find_best_matching_fish(rect)
                        if fish_type and score >= 0.7:
                            print(f"Detected fish type: {fish_type} (score: {score:.3f}).")
                            break
                        else:
                            print(f"Attempt {i + 1}: No fish type detected.")
                            if i < attempts - 1:
                                time.sleep(0.2)
                else:
                    print("Fish folder not found.")

                # Logging
                log_args = {"status": True}
                if fish_type:
                    log_args["fish_type"] = fish_type
                    session_stats["xp"] += fish_service.get_xp_by_type(
                        fish_type=fish_type
                    )
                else:
                    session_stats["xp"] += 1
                log_catch(**log_args)
                session_stats["catches"] += 1
                total = session_stats["catches"] + session_stats["misses"]
                session_stats["rate"] = (
                    round((session_stats["catches"] / total) * 100, 2)
                    if total > 0
                    else 0.0
                )
                update_ui_stats()

                # Click saved continue position with retries
                for attempt in range(3):
                    if saved_continue_pos:
                        click(*saved_continue_pos)
                        time.sleep(0.5)
                    still_there = image_service.find_image_in_window(
                        rect,
                        (
                            get_data_dir()
                            / TARGET_IMAGES_FOLDER
                            / get_resolution_folder()
                            / "continue.png"
                        ),
                        0.75,
                    )
                    if not still_there:
                        still_there = image_service.find_image_in_window(
                            rect,
                            (
                                get_data_dir()
                                / TARGET_IMAGES_FOLDER
                                / get_resolution_folder()
                                / "continue_highlighted.png"
                            ),
                            0.75,
                        )
                    if not still_there:
                        break

                return

            elif default_found:
                print("Default screen detected, minigame failed. Releasing click.")
                mouse.release(Button.left)
                log_catch(False)
                session_stats["misses"] += 1
                total = session_stats["catches"] + session_stats["misses"]
                session_stats["rate"] = (
                    round((session_stats["catches"] / total) * 100, 2)
                    if total > 0
                    else 0.0
                )
                update_ui_stats()
                return


# ---------------- Main Loop ----------------
restart_flag = False


def main():
    global macro_start_event, last_progress_time, restart_flag
    window_title = select_window()
    print(f"Macro waiting for START key ({get_keys()[0]})")
    last_progress_time = time.time()

    listener = Listener(on_press=on_press)
    listener.start()

    while True:

        if not macro_start_event.is_set():
            time.sleep(0.1)
            continue

        if time.time() - last_progress_time > NO_PROGRESS_LIMIT:
            handle_no_progress_loop(window_title)

        rect = get_window_rect(window_title)

        default_found = image_service.find_image_in_window(
            rect,
            (
                get_data_dir()
                / TARGET_IMAGES_FOLDER
                / get_resolution_folder()
                / "default_screen.png"
            ),
            THRESHOLD,
        )
        if default_found:
            last_progress_time = time.time()

            print(time.time() - last_progress_time)
            print("Default screen detected")
            time.sleep(0.2)

            # Broken rod handling
            broken_pole = image_service.find_image_in_window(
                rect,
                (
                    get_data_dir()
                    / TARGET_IMAGES_FOLDER
                    / get_resolution_folder()
                    / "broken_pole.png"
                ),
                0.9,
            )
            if broken_pole:
                print("Broken pole detected -> pressing M")
                last_progress_time = time.time()

                log_broken_rod()
                press_key(get_pykey("rods_key"))
                time.sleep(0.2)
                use_rod = image_service.find_image_in_window(
                    rect,
                    (
                        get_data_dir()
                        / TARGET_IMAGES_FOLDER
                        / get_resolution_folder()
                        / "use_rod.png"
                    ),
                    0.9,
                )
                if use_rod:
                    last_progress_time = time.time()

                    click(*use_rod)
                    time.sleep(1)
                continue

            # Start fishing
            mouse.click(Button.left, 1)
            print("Started fishing -> waiting for catch_fish.png")
            last_progress_time = time.time()

            time.sleep(1)

            while macro_start_event.is_set():
                if time.time() - last_progress_time > NO_PROGRESS_LIMIT:
                    handle_no_progress_loop(window_title)

                catch_coords = image_service.find_image_in_window(
                    rect,
                    (
                        get_data_dir()
                        / TARGET_IMAGES_FOLDER
                        / get_resolution_folder()
                        / "catch_fish.png"
                    ),
                    0.9,
                )
                if catch_coords:
                    last_progress_time = time.time()

                    mouse.position = catch_coords
                    time.sleep(0.05)
                    post_catch_loop(window_title)
                    break

                time.sleep(CHECK_INTERVAL)

        time.sleep(CHECK_INTERVAL)


NO_PROGRESS_LIMIT = 45

from src.utils.keybinds import get_key


def restart_macro():
    global restart_flag
    print("Triggering macro restart...")

    def _restart():
        handle_stop_key()
        time.sleep(0.5)  # let loops exit
        handle_start_key()

    threading.Thread(target=_restart, daemon=True).start()


def handle_no_progress_loop(window_title):
    global last_progress_time, macro_start_event
    print("restart")

    esc_key = get_key("esc_key")
    fish_key = get_key("fish_key")

    while macro_start_event.is_set():
        rect = get_window_rect(window_title)
        if not rect:
            time.sleep(1)
            continue

        # Check if default screen is detected
        default_found = image_service.find_image_in_window(
            rect,
            get_data_dir()
            / TARGET_IMAGES_FOLDER
            / get_resolution_folder()
            / "default_screen.png",
            0.9,
        )
        if default_found:
            print("Default screen detected, stopping recovery loop.")
            last_progress_time = time.time()
            restart_macro()
            break

        # Perform recovery actions
        print("No progress detected, performing recovery actions...")
        if esc_key:
            press_key(get_pykey("esc_key"))
            time.sleep(1)
        if fish_key:
            press_key(get_pykey("fish_key"))
            time.sleep(1)

        last_progress_time = time.time()
        time.sleep(1)


def start_macro():
    main()


if __name__ == "__main__":
    try:
        update = check_for_update()
        if update:
            print(f"New version available: {update['version']}")
            run_update(update)
        else:
            print("App is up to date.")

        macro_thread = threading.Thread(target=start_macro, daemon=True)
        macro_thread.start()

        time.sleep(0.5)

        start_ui()
    finally:
        print("App is closing, cleaning up...")
        handle_stop_key()
