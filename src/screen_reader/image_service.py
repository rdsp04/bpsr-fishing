import cv2
import numpy as np
import os
from .screen_service import ScreenService
from .base import RESOLUTION_FOLDER
from src.utils.path import get_data_dir

BASE = get_data_dir()
class ImageService:
    def __init__(self):
        self.screen_service = ScreenService()
        # Dynamically set image base folder
        self.target_images_folder = os.path.join(BASE, "images")
        self.resolution_folder = RESOLUTION_FOLDER  # keep existing

    def find_image_in_window(self, window_rect, image_path, threshold=0.7):
        """
        Find a single image on the screen within a given window rectangle.
        Returns center coordinates if found, else None
        """
        if not window_rect:
            return None

        x1, y1, x2, y2 = window_rect
        w, h = x2 - x1, y2 - y1

        screenshot = self.screen_service.safe_screenshot(region=(x1, y1, w, h))
        if screenshot is None:
            return None

        img_rgb = np.array(screenshot)
        img_gray = cv2.cvtColor(img_rgb, cv2.COLOR_BGR2GRAY)

        template = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
        if template is None:
            print(f"Template not found: {image_path}")
            return None

        res = cv2.matchTemplate(img_gray, template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(res)

        if max_val >= threshold:
            click_x = x1 + max_loc[0] + template.shape[1] // 2
            click_y = y1 + max_loc[1] + template.shape[0] // 2
            return click_x, click_y

        return None

    def find_best_matching_fish(self, window_rect):
        """
        Returns the fish name with the highest score and the score itself.
        """
        if not window_rect:
            return None, 0.0

        x1, y1, x2, y2 = window_rect
        w, h = x2 - x1, y2 - y1

        screenshot = self.screen_service.safe_screenshot(region=(x1, y1, w, h))
        if screenshot is None:
            return None, 0.0

        img_rgb = np.array(screenshot)
        img_gray = cv2.cvtColor(img_rgb, cv2.COLOR_BGR2GRAY)

        fish_folder = os.path.join(self.target_images_folder, self.resolution_folder, "fish")
        if not os.path.exists(fish_folder):
            print(f"Fish folder not found: {fish_folder}")
            return None, 0.0

        best_fish = None
        best_score = 0.0

        for fname in os.listdir(fish_folder):
            if not fname.lower().endswith(".png"):
                continue
            fish_name = os.path.splitext(fname)[0]
            template_path = os.path.join(fish_folder, fname)
            template = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)
            if template is None:
                continue

            res = cv2.matchTemplate(img_gray, template, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, _ = cv2.minMaxLoc(res)

            if max_val > best_score:
                best_score = max_val
                best_fish = fish_name

        return best_fish, best_score
