import time
import cv2
import numpy as np
import pyautogui
import pygetwindow as gw
import win32gui
import os
from pynput.mouse import Controller, Button
from pynput.keyboard import Controller as KeyboardController, Listener, KeyCode
saved_continue_pos = None  # global continue button position

# === CONFIG ===
TARGET_IMAGES_FOLDER = "images"
CHECK_INTERVAL = 0.05
THRESHOLD = 0.7
SPAM_CPS = 20

START_KEY = KeyCode(char="s")  # Press 's' to start
STOP_KEY = KeyCode(char="x")  # Press 'x' to stop

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

def focus_blue_protocol_window():
    target_title = "Blue Protocol: Star Resonance"
    hwnd = win32gui.FindWindow(None, target_title)
    if hwnd == 0:
        print(f"Window '{target_title}' not found.")
        return None
    win32gui.ShowWindow(hwnd, 5)  # Restore if minimized
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
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)

    # only accept strong matches
    if max_val >= threshold:
        click_x = x1 + max_loc[0] + template.shape[1] // 2
        click_y = y1 + max_loc[1] + template.shape[0] // 2
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

def post_catch_loop(target_window, hwnd):
    global macro_running, saved_continue_pos
    print("Fish took the bait")
    print("Holding left click until continue.png, continue_highlighted.png, or default_screen.png is found")

    counter = 0
    last_print_time = time.time()
    last_check_time = time.time()

    mouse.press(Button.left)
    saved_continue_pos = None  # store first found continue location

    while macro_running:
        counter += 1
        time.sleep(1 / SPAM_CPS)

        # Print counter every second
        if time.time() - last_print_time >= 1:
            print(f"Held for {counter} ticks")
            last_print_time = time.time()

        # Check every 0.3s
        if time.time() - last_check_time >= 0.3:
            win_rect = get_window_rect(target_window)
            if win_rect:
                x1, y1, x2, y2 = win_rect
                mouse.position = (x1 + 50, y1 + 50)
            time.sleep(0.3)

            continue_found = None
            if saved_continue_pos is None:
                # Find continue on screen if we don’t have a saved position
                continue_found = find_image_in_window(target_window, "continue.png", 0.8)
                if continue_found:
                    print(f"[LOG] Found continue.png at {continue_found}")
                    saved_continue_pos = continue_found
                else:
                    continue_found = find_image_in_window(target_window, "continue_highlighted.png", 0.8)
                    if continue_found:
                        print(f"[LOG] Found continue_highlighted.png at {continue_found}")
                        saved_continue_pos = continue_found
            else:
                # Use saved position
                continue_found = saved_continue_pos

            default_found = find_image_in_window(target_window, "default_screen.png", 0.9)
            last_check_time = time.time()

            if continue_found:
                print("Continue button found, releasing click")
                mouse.release(Button.left)

                for attempt in range(3):
                    if saved_continue_pos:
                        click(*saved_continue_pos, hwnd)
                        print(f"[LOG] Clicked saved continue position {saved_continue_pos}")
                        time.sleep(0.5)

                    if win_rect:
                        mouse.position = (x1 + 50, y1 + 50)

                    still_there = find_image_in_window(target_window, "continue.png", 0.75)
                    if not still_there:
                        still_there = find_image_in_window(target_window, "continue_highlighted.png", 0.75)

                    if not still_there:
                        print("Continue button gone, proceeding")
                        time.sleep(1)
                        return
                    else:
                        print(f"Click {attempt + 1} didn't register, retrying...")

                        # # Optional: recheck if the continue button moved
                        # new_pos = find_image_in_window(target_window, "continue.png", 0.8)
                        # if not new_pos:
                        #     new_pos = find_image_in_window(target_window, "continue_highlighted.png", 0.8)
                        # if new_pos:
                        #     print(f"[LOG] Updated continue position {new_pos}")
                        #     saved_continue_pos = new_pos

                print("Continue button still visible after retries, returning anyway")
                return

            elif default_found:
                print("Default screen detected, minigame failed. Releasing click.")
                mouse.release(Button.left)
                time.sleep(0.5)
                return

    mouse.release(Button.left)



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

        default_coords = find_image_in_window(target_window, "default_screen.png")
        if default_coords:
            print("Default screen detected")
            time.sleep(0.2)

            if find_image_in_window(target_window, "broken_pole.png", 0.9):
                print("Broken pole detected -> pressing M")
                press_key("m", hwnd)
                time.sleep(0.2)

                rod_coords = find_image_in_window(target_window, "use_rod.png", 0.9)
                if rod_coords:
                    print("Clicking use_rod.png")
                    time.sleep(2)
                    click(*rod_coords, hwnd)
                    time.sleep(2)

                continue

            time.sleep(0.2)
            # start fishing once. do not start post-catch until catch_fish appears
            mouse.click(Button.left, 1)
            print("Started fishing -> waiting for catch_fish.png")
            time.sleep(1)

            while macro_running:
                catch_coords = find_image_in_window(
                    target_window, "catch_fish.png", 0.9
                )
                if catch_coords:
                    # move mouse to the detected fish position
                    mouse.position = catch_coords
                    time.sleep(0.05)

                    # enter post-catch handling which presses and holds,
                    # checks for continue.png and clicks it reliably
                    post_catch_loop(target_window, hwnd)

                    # after post_catch_loop returns, break to outer loop
                    break

                time.sleep(CHECK_INTERVAL)

        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    main()
