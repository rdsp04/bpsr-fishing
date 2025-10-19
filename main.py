import time
import cv2
import numpy as np
import pyautogui
import pygetwindow as gw
import win32gui
import os
from pynput.mouse import Controller, Button
from pynput.keyboard import Controller as KeyboardController, Listener, KeyCode

# === CONFIG ===
TARGET_IMAGES_FOLDER = "images"
CHECK_INTERVAL = 0.05
THRESHOLD = 0.7
SPAM_CPS = 50

START_KEY = KeyCode(char='s')  # Press 's' to start
STOP_KEY = KeyCode(char='x')   # Press 'x' to stop

mouse = Controller()
keyboard = KeyboardController()
macro_running = False  # Global flag


def on_press(key):
    global macro_running
    if key == START_KEY:
        macro_running = True
        print("Macro started")
    elif key == STOP_KEY:
        macro_running = False
        print("Macro stopped")


def list_windows():
    windows = gw.getAllTitles()
    windows = [w for w in windows if w.strip()]
    for i, title in enumerate(windows):
        print(f"[{i}] {title}")
    return windows


def select_window():
    print("Select a window:")
    windows = list_windows()
    index = int(input("Enter window number: "))
    title = windows[index]
    print(f"Selected window: {title}")
    return title


def get_window_rect(title):
    hwnd = win32gui.FindWindow(None, title)
    if not hwnd:
        return None
    return win32gui.GetWindowRect(hwnd)


def find_image_in_window(window_title, image_name, threshold=THRESHOLD):
    rect = get_window_rect(window_title)
    if not rect:
        return None

    x1, y1, x2, y2 = rect
    w, h = x2 - x1, y2 - y1

    screenshot = pyautogui.screenshot(region=(x1, y1, w, h))
    img_rgb = np.array(screenshot)
    img_gray = cv2.cvtColor(img_rgb, cv2.COLOR_BGR2GRAY)

    path = os.path.join(TARGET_IMAGES_FOLDER, image_name)
    template = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
    if template is None:
        return None

    res = cv2.matchTemplate(img_gray, template, cv2.TM_CCOEFF_NORMED)
    loc = np.where(res >= threshold)
    for pt in zip(*loc[::-1]):
        click_x = x1 + pt[0] + template.shape[1] // 2
        click_y = y1 + pt[1] + template.shape[0] // 2
        return click_x, click_y

    return None


def click(x, y, hwnd):
    time.sleep(0.05)
    mouse.position = (x, y)
    mouse.click(Button.left, 1)


def press_key(key, hwnd):
    time.sleep(0.05)
    keyboard.press(key)
    keyboard.release(key)


def hold_key(key):
    keyboard.press(key)


def release_key(key):
    keyboard.release(key)


def spam_left_click_at_position(x, y, cps, hwnd, duration=1):
    interval = 1 / cps
    start_time = time.time()
    while time.time() - start_time < duration:
        mouse.position = (x, y)
        mouse.click(Button.left, 1)
        time.sleep(interval)


def post_catch_loop(target_window, hwnd):
    global macro_running
    print("Post-catch: handling minigame with timed holds")

    hold_duration = 3       # seconds to hold a key
    release_duration = 0.5  # seconds to release a key
    key_state = {"a": False, "d": False}   # whether key is currently held
    key_timer = {"a": 0, "d": 0}           # last hold/release timestamp

    while macro_running:
        now = time.time()

        # Check arrows
        arrows = {"a": "left.png", "d": "right.png"}
        for key, arrow_file in arrows.items():
            arrow_found = find_image_in_window(target_window, arrow_file)

            if arrow_found:
                # hold/release timing logic
                if not key_state[key]:
                    hold_key(key)
                    key_state[key] = True
                    key_timer[key] = now
                elif key_state[key] and now - key_timer[key] >= hold_duration:
                    release_key(key)
                    key_state[key] = False
                    key_timer[key] = now
            else:
                # release immediately if arrow not found
                if key_state[key]:
                    release_key(key)
                    key_state[key] = False

        # Check continue/default screen
        continue_coords = find_image_in_window(target_window, "continue.png")
        default_coords = find_image_in_window(target_window, "default_screen.png", 0.9)

        if continue_coords:
            time.sleep(1)
            for _ in range(2):
                click(*continue_coords, hwnd)
                time.sleep(0.05)
            for k in key_state:
                if key_state[k]:
                    release_key(k)
                    key_state[k] = False
            print("Continue button clicked, returning to default screen")
            break

        if default_coords:
            for k in key_state:
                if key_state[k]:
                    release_key(k)
                    key_state[k] = False
            print("Minigame failed, returning to default screen")
            break

        time.sleep(CHECK_INTERVAL)


def main():
    global macro_running
    target_window = select_window()
    hwnd = win32gui.FindWindow(None, target_window)
    print(f"Macro waiting for START key ({START_KEY.char})")

    listener = Listener(on_press=on_press)
    listener.start()

    while True:
        if not macro_running:
            time.sleep(0.1)
            continue

        # Step 1: Wait for default screen
        default_coords = find_image_in_window(target_window, "default_screen.png")
        if default_coords:
            print("Default screen detected")
            time.sleep(0.2)

            # Step 2: Check broken pole
            if find_image_in_window(target_window, "broken_pole.png", 0.9):
                print("Broken pole detected -> pressing M")
                press_key('m', hwnd)
                time.sleep(0.2)

                rod_coords = find_image_in_window(target_window, "use_rod.png", 0.9)
                if rod_coords:
                    print("Clicking use_rod.png")
                    time.sleep(2)
                    click(*rod_coords, hwnd)
                    time.sleep(2)

                continue

            # Step 3: Start fishing (no click spam yet)
            time.sleep(0.2)
            mouse.click(Button.left, 1)
            print("Started fishing -> waiting for catch_fish.png")
            time.sleep(0.2)

            # Step 4: Wait until catch_fish.png is visible
            while macro_running:
                catch_coords = find_image_in_window(target_window, "catch_fish.png", 0.9)
                if catch_coords:
                    print("Fish detected -> starting catch")
                    mouse.click(Button.left, 1)
                    time.sleep(0.1)
                    spam_left_click_at_position(catch_coords[0], catch_coords[1], cps=50, hwnd=hwnd, duration=1)
                    print("Finished catching fish, entering post-catch loop")
                    post_catch_loop(target_window, hwnd)
                    break

                time.sleep(CHECK_INTERVAL)

        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    main()
