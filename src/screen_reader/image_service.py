import cv2
import numpy as np
import os
from .screen_service import ScreenService
from .base import get_resolution_folder
from src.utils.path import get_data_dir

BASE = get_data_dir()


class ImageService:
    def __init__(self):
        self.screen_service = ScreenService()
        self.target_images_folder = BASE / "images"
        self.resolution_folder = get_resolution_folder()

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

    def find_best_matching_fish(self, window_rect, show_crop=True):
        """
        Returns the fish name with the highest score and the score itself.
        Searches only in a specific bottom-left region:
        - 20% width of window
        - 33% height of window
        - top margin at 66% height
        """
        if not window_rect:
            return None, 0.0, None

        x1, y1, x2, y2 = window_rect
        w, h = x2 - x1, y2 - y1

        screenshot = self.screen_service.safe_screenshot(region=(x1, y1, w, h))
        if screenshot is None:
            return None, 0.0, None

        img_rgb = np.array(screenshot)
        img_gray = cv2.cvtColor(img_rgb, cv2.COLOR_BGR2GRAY)

        # Define the crop region
        crop_width = int(w * 0.30)
        crop_height = int(h * 0.33)
        crop_x1 = int(w * 0.20)
        crop_y1 = int(h * 0.66)
        crop_x2 = crop_x1 + crop_width
        crop_y2 = crop_y1 + crop_height

        img_gray_crop = img_gray[crop_y1:crop_y2, crop_x1:crop_x2]

        if show_crop:
            # Draw the crop rectangle on a copy of the screenshot
            img_show = img_rgb.copy()
            cv2.rectangle(
                img_show, (crop_x1, crop_y1), (crop_x2, crop_y2), (0, 255, 0), 2
            )
            cv2.imshow("Debug Crop Area", img_show)
            print(f"Showing crop: ({crop_x1},{crop_y1}) -> ({crop_x2},{crop_y2})")
            cv2.waitKey(0)  # Wait until you press a key
            cv2.destroyWindow("Debug Crop Area")

        self.resolution_folder = get_resolution_folder()
        fish_folder = self.target_images_folder / self.resolution_folder / "fish"
        if not os.path.exists(fish_folder):
            return None, 0.0

        best_fish = None
        best_score = 0.0
        best_coords = None

        for fname in os.listdir(fish_folder):
            if not fname.lower().endswith(".png"):
                continue
            fish_name = os.path.splitext(fname)[0]
            template_path = fish_folder / fname

            template_img = cv2.imread(str(template_path), cv2.IMREAD_UNCHANGED)
            if template_img is None:
                continue

            if template_img.shape[2] == 4:
                template = cv2.cvtColor(template_img[:, :, :3], cv2.COLOR_BGR2GRAY)
                mask = (template_img[:, :, 3] > 0).astype(np.uint8) * 255
            else:
                template = cv2.cvtColor(template_img, cv2.COLOR_BGR2GRAY)
                mask = None

            template = template.astype(np.uint8)
            img_crop_uint8 = img_gray_crop.astype(np.uint8)

            try:
                res = cv2.matchTemplate(
                    img_crop_uint8, template, cv2.TM_CCOEFF_NORMED, mask=mask
                )
                _, max_val, _, max_loc = cv2.minMaxLoc(res)
            except cv2.error:
                max_val = 0.0
                max_loc = (0, 0)

            print(f"Checked {fish_name}, score: {max_val:.4f}")

            if max_val > best_score:
                best_score = max_val
                best_fish = fish_name
                best_coords = (x1 + crop_x1 + max_loc[0], y1 + crop_y1 + max_loc[1])

        return best_fish, best_score
