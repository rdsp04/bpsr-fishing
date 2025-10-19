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
SPAM_CPS = 20

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

def post_catch_loop(target_window, hwnd):
    global macro_running
    print("Fish took the bait")
    print("Holding left click until continue.png is found")

    counter = 0
    last_print_time = time.time()
    last_check_time = time.time()

    mouse.press(Button.left)

    while macro_running:
        counter += 1
        time.sleep(1 / SPAM_CPS)

        # Print counter every second
        if time.time() - last_print_time >= 1:
            print(f"Held for {counter} ticks")
            last_print_time = time.time()

        # Check for continue.png every 0.3s
        if time.time() - last_check_time >= 0.3:
            continue_found = find_image_in_window(target_window, "continue.png", 0.8)
            last_check_time = time.time()
            if continue_found:
                print("Continue button found, releasing click")
                mouse.release(Button.left)
                click(*continue_found, hwnd)
                time.sleep(1)
                print("Resuming normal loop")
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
                press_key('m', hwnd)
                time.sleep(0.2)

                rod_coords = find_image_in_window(target_window, "use_rod.png", 0.9)
                if rod_coords:
                    print("Clicking use_rod.png")
                    time.sleep(2)
                    click(*rod_coords, hwnd)
                    time.sleep(2)

                continue

            time.sleep(0.2)
            mouse.click(Button.left, 1)
            mouse.click(Button.left, 1)
            print("Started fishing -> waiting for catch_fish.png")
            time.sleep(0.2)

            while macro_running:
                catch_coords = find_image_in_window(target_window, "catch_fish.png", 0.9)
                if catch_coords:
                    print("Fish took the bait")
                    print("Spamming left click until continue.png is found")

                    # === CHANGED SECTION START ===counter =
                    last_check_time = time.time()

                    while macro_running:
                        mouse.position = catch_coords
                        post_catch_loop(target_window, hwnd)

                        mouse.press(Button.left)


                        # Only check for continue.png every 0.3 seconds
                        if time.time() - last_check_time >= 0.3:
                            mouse.release(Button.left)
                            continue_found = find_image_in_window(target_window, "continue.png", 0.8)
                            last_check_time = time.time()
                            if continue_found:
                                print("Continue button found, stopping spam")
                                click(*continue_found, hwnd)
                                time.sleep(1)
                                post_catch_loop(target_window, hwnd)
                                break



                    break

                time.sleep(CHECK_INTERVAL)

        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    main()
