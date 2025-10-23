import time
import os
import sys
import json
from datetime import datetime
import win32gui
from pynput.mouse import Controller, Button
from pynput.keyboard import Controller as KeyboardController, Listener, KeyCode
import pyautogui

from src.screen_reader.screen_service import ScreenService
from src.screen_reader.image_service import ImageService
from src.screen_reader.base import RESOLUTION_FOLDER

# Services
screen_service = ScreenService()
image_service = ImageService()

# Globals
TARGET_IMAGES_FOLDER = "images"
saved_continue_pos = None
CHECK_INTERVAL = 0.05
THRESHOLD = 0.7
SPAM_CPS = 20

START_KEY = KeyCode(char="s")
STOP_KEY = KeyCode(char="x")

mouse = Controller()
keyboard = KeyboardController()
macro_running = False


# ---------------- Logging ----------------
def log_broken_rod(filename="broken_rods.json"):
    if getattr(sys, "frozen", False):
        return
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


def log_catch(status, filename="fishing_log.json", **extra):
    if getattr(sys, "frozen", False):
        return
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


# ---------------- Input ----------------
def on_press(key):
    global macro_running
    if key == START_KEY:
        macro_running = True
        print("Macro started")
    elif key == STOP_KEY:
        macro_running = False
        print("Macro stopped")
        if getattr(sys, "frozen", False):
            return
        try:
            import log_main

            log_main.run_summary()
        except Exception as e:
            print(f"Failed to run log_main.py: {e}")


# ---------------- Window Handling ----------------
def focus_blue_protocol_window():
    target_title = "Blue Protocol: Star Resonance"
    hwnd = win32gui.FindWindow(None, target_title)
    if hwnd == 0:
        print(f"Window '{target_title}' not found.")
        return None
    win32gui.ShowWindow(hwnd, 5)
    win32gui.SetForegroundWindow(hwnd)
    return hwnd


def select_window():
    hwnd = focus_blue_protocol_window()
    if hwnd:
        print("Automatically selected Blue Protocol window.")
        return "Blue Protocol: Star Resonance"
    else:
        raise Exception("Could not find Blue Protocol window.")


def get_window_rect(title):
    hwnd = win32gui.FindWindow(None, title)
    if not hwnd:
        return None
    return win32gui.GetWindowRect(hwnd)


# ---------------- Actions ----------------
def click(x, y):
    time.sleep(0.05)
    mouse.position = (x, y)
    mouse.click(Button.left, 1)


def press_key(key):
    time.sleep(0.05)
    keyboard.press(key)
    keyboard.release(key)


def hold_key(key):
    keyboard.press(key)


def release_key(key):
    keyboard.release(key)


# ---------------- Fishing Logic ----------------
def post_catch_loop(window_title):
    global macro_running, saved_continue_pos
    print("Fish took the bait")
    counter = 0
    last_print_time = time.time()
    last_check_time = time.time()
    mouse.press(Button.left)

    lane = 0
    while macro_running:
        counter += 1
        time.sleep(1 / SPAM_CPS)

        rect = get_window_rect(window_title)

        right_found = image_service.find_image_in_window(
            rect,
            os.path.join(TARGET_IMAGES_FOLDER, RESOLUTION_FOLDER, "right.png"),
            0.8,
        )
        left_found = image_service.find_image_in_window(
            rect, os.path.join(TARGET_IMAGES_FOLDER, RESOLUTION_FOLDER, "left.png"), 0.8
        )

        if right_found:
            lane += 1
            if lane > 1:
                lane = 1
            print(f"Right arrow detected, lane = {lane}")
            time.sleep(0.2)
        elif left_found:
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
                os.path.join(TARGET_IMAGES_FOLDER, RESOLUTION_FOLDER, "continue.png"),
                0.8,
            )
            if not continue_found:
                continue_found = image_service.find_image_in_window(
                    rect,
                    os.path.join(
                        TARGET_IMAGES_FOLDER,
                        RESOLUTION_FOLDER,
                        "continue_highlighted.png",
                    ),
                    0.8,
                )
            default_found = image_service.find_image_in_window(
                rect,
                os.path.join(
                    TARGET_IMAGES_FOLDER, RESOLUTION_FOLDER, "default_screen.png"
                ),
                0.9,
            )
            last_check_time = time.time()

            if continue_found:
                if saved_continue_pos is None:
                    saved_continue_pos = continue_found
                print("Continue button found, releasing click")
                mouse.release(Button.left)

                # === Fish Detection + Screenshot ===
                fish_folder = os.path.join(
                    TARGET_IMAGES_FOLDER, RESOLUTION_FOLDER, "fish"
                )
                fish_type = None
                screenshot_folder = "screenshots"
                os.makedirs(screenshot_folder, exist_ok=True)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

                if os.path.exists(fish_folder):
                    found = False
                    for fname in os.listdir(fish_folder):
                        if not fname.lower().endswith(".png"):
                            continue
                        fish_type, score = image_service.find_best_matching_fish(rect)
                        if fish_type:
                            screenshot_path = os.path.join(
                                screenshot_folder, f"screenshot_{fish_type}_{timestamp}.png"
                            )
                            print(f"Detected fish type: {fish_type} (score: {score:.3f}). Screenshot saved: {screenshot_path}")
                            found = True
                            break
                        else:
                            screenshot_path = os.path.join(screenshot_folder, f"screenshot_{timestamp}.png")
                            pyautogui.screenshot(screenshot_path)
                            print(f"No fish detected. Screenshot saved: {screenshot_path}")

                    if not found:
                        screenshot_path = os.path.join(
                            screenshot_folder, f"screenshot_{timestamp}.png"
                        )
                        pyautogui.screenshot(screenshot_path)
                        print(f"No fish detected. Screenshot saved: {screenshot_path}")
                else:
                    print("Fish folder not found, taking default screenshot")
                    screenshot_path = os.path.join(
                        screenshot_folder, f"screenshot_{timestamp}.png"
                    )
                    pyautogui.screenshot(screenshot_path)

                # Logging
                log_args = {"status": True}
                if fish_type:
                    log_args["fish_type"] = fish_type
                log_catch(**log_args)

                # Click saved continue position with retries
                for attempt in range(3):
                    if saved_continue_pos:
                        click(*saved_continue_pos)
                        time.sleep(0.5)
                    still_there = image_service.find_image_in_window(
                        rect,
                        os.path.join(
                            TARGET_IMAGES_FOLDER, RESOLUTION_FOLDER, "continue.png"
                        ),
                        0.75,
                    )
                    if not still_there:
                        still_there = image_service.find_image_in_window(
                            rect,
                            os.path.join(
                                TARGET_IMAGES_FOLDER,
                                RESOLUTION_FOLDER,
                                "continue_highlighted.png",
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
                return


# ---------------- Main Loop ----------------
def main():
    global macro_running
    window_title = select_window()
    print(f"Macro waiting for START key ({START_KEY.char})")

    listener = Listener(on_press=on_press)
    listener.start()

    while True:
        if not macro_running:
            time.sleep(0.1)
            continue

        rect = get_window_rect(window_title)

        default_found = image_service.find_image_in_window(
            rect,
            os.path.join(TARGET_IMAGES_FOLDER, RESOLUTION_FOLDER, "default_screen.png"),
            THRESHOLD,
        )
        if default_found:
            print("Default screen detected")
            time.sleep(0.2)

            # Broken rod handling
            broken_pole = image_service.find_image_in_window(
                rect,
                os.path.join(
                    TARGET_IMAGES_FOLDER, RESOLUTION_FOLDER, "broken_pole.png"
                ),
                0.9,
            )
            if broken_pole:
                print("Broken pole detected -> pressing M")
                log_broken_rod()
                press_key("m")
                time.sleep(0.2)
                use_rod = image_service.find_image_in_window(
                    rect,
                    os.path.join(
                        TARGET_IMAGES_FOLDER, RESOLUTION_FOLDER, "use_rod.png"
                    ),
                    0.9,
                )
                if use_rod:
                    click(*use_rod)
                    time.sleep(1)
                continue

            # Start fishing
            mouse.click(Button.left, 1)
            print("Started fishing -> waiting for catch_fish.png")
            time.sleep(1)

            while macro_running:
                catch_coords = image_service.find_image_in_window(
                    rect,
                    os.path.join(
                        TARGET_IMAGES_FOLDER, RESOLUTION_FOLDER, "catch_fish.png"
                    ),
                    0.9,
                )
                if catch_coords:
                    mouse.position = catch_coords
                    time.sleep(0.05)
                    post_catch_loop(window_title)
                    break

                time.sleep(CHECK_INTERVAL)

        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    main()
