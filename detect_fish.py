import os
import cv2
from src.screen_reader.base import RESOLUTION_FOLDER

TARGET_IMAGES_FOLDER = "images"

# List your screenshots here
screenshot_paths = [
    "screenshots/screenshot_20251023_210520.png",
    "screenshots/screenshot_20251023_210659.png",
    "screenshots/screenshot_astercad_20251023_210232.png"
]
def detect_fish_scores(screenshot_paths):
    fish_folder = os.path.join(TARGET_IMAGES_FOLDER, RESOLUTION_FOLDER, "fish")
    if not os.path.exists(fish_folder):
        print(f"Fish folder not found: {fish_folder}")
        return

    # Preload all fish templates
    fish_templates = []
    for fname in os.listdir(fish_folder):
        if not fname.lower().endswith(".png"):
            continue
        path = os.path.join(fish_folder, fname)
        template = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
        if template is not None:
            fish_templates.append((os.path.splitext(fname)[0], template))

    for screenshot_path in screenshot_paths:
        if not os.path.exists(screenshot_path):
            print(f"Screenshot not found: {screenshot_path}")
            continue

        screenshot = cv2.imread(screenshot_path, cv2.IMREAD_GRAYSCALE)
        if screenshot is None:
            print(f"Failed to load screenshot: {screenshot_path}")
            continue

        print(f"\nScreenshot: {screenshot_path}")
        for fish_name, template in fish_templates:
            res = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, _ = cv2.minMaxLoc(res)
            print(f"  Fish: {fish_name}, Score: {max_val:.3f}")

if __name__ == "__main__":
    detect_fish_scores(screenshot_paths)
