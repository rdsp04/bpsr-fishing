import os
import cv2
import numpy as np
from src.screen_reader.base import get_resolution_folder

TARGET_IMAGES_FOLDER = "images"

# List your screenshots here
screenshot_paths = [
    "screenshots/astermackere_test_1920x1080.png"
]

def detect_fish_scores(screenshot_paths):
    fish_folder = os.path.join(TARGET_IMAGES_FOLDER, get_resolution_folder(), "fish")
    if not os.path.exists(fish_folder):
        print(f"Fish folder not found: {fish_folder}")
        return

    fish_templates = []
    for fname in os.listdir(fish_folder):
        if not fname.lower().endswith(".png"):
            continue

        path = os.path.join(fish_folder, fname)
        template_rgba = cv2.imread(path, cv2.IMREAD_UNCHANGED)
        if template_rgba is None:
            continue

        # Handle alpha mask if present
        if template_rgba.shape[2] == 4:
            template = cv2.cvtColor(template_rgba[:, :, :3], cv2.COLOR_BGR2GRAY)
            alpha = template_rgba[:, :, 3]
            mask = cv2.threshold(alpha, 1, 255, cv2.THRESH_BINARY)[1]
        else:
            template = cv2.cvtColor(template_rgba, cv2.COLOR_BGR2GRAY)
            mask = None

        fish_templates.append((os.path.splitext(fname)[0], template, mask))

    for screenshot_path in screenshot_paths:
        if not os.path.exists(screenshot_path):
            print(f"Screenshot not found: {screenshot_path}")
            continue

        screenshot = cv2.imread(screenshot_path, cv2.IMREAD_GRAYSCALE)
        if screenshot is None:
            print(f"Failed to load screenshot: {screenshot_path}")
            continue

        print(f"\nScreenshot: {screenshot_path}")
        for fish_name, template, mask in fish_templates:
            if fish_name != "astermackere":
                continue

            best_score = -1
            best_scale = 1.0
            best_loc = None
            best_shape = None

            # Try scales from 0.4x to 2.0x
            for scale in np.arange(1, 1.4, 0.01):
                resized_template = cv2.resize(template, (0, 0), fx=scale, fy=scale)
                resized_mask = cv2.resize(mask, (resized_template.shape[1], resized_template.shape[0])) if mask is not None else None

                if resized_template.shape[0] > screenshot.shape[0] or resized_template.shape[1] > screenshot.shape[1]:
                    continue

                res = cv2.matchTemplate(screenshot, resized_template, cv2.TM_CCOEFF_NORMED, mask=resized_mask)
                _, max_val, _, max_loc = cv2.minMaxLoc(res)

                if max_val > best_score:
                    best_score = max_val
                    best_scale = scale
                    best_loc = max_loc
                    best_shape = resized_template.shape

            print(f"  Fish: {fish_name}, Best Score: {best_score:.3f} at scale {best_scale:.2f}")

            if best_loc and best_shape:
                h, w = best_shape
                top_left = best_loc
                bottom_right = (top_left[0] + w, top_left[1] + h)
                result_img = cv2.cvtColor(screenshot, cv2.COLOR_GRAY2BGR)
                cv2.rectangle(result_img, top_left, bottom_right, (0, 255, 0), 2)
                cv2.imshow(f"{fish_name} match", result_img)
                cv2.waitKey(0)
                cv2.destroyAllWindows()


if __name__ == "__main__":
    detect_fish_scores(screenshot_paths)
