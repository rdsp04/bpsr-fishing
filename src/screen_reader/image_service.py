import cv2
import numpy as np
import os
from .screen_service import ScreenService
from .base import get_resolution_folder
from src.utils.path import get_data_dir
import easyocr
from src.fish.fish_service import FishService

BASE = get_data_dir()
CONFIG_PATH = BASE / "config/fish_config.json"



class ImageService:
    def __init__(self):
        self.screen_service = ScreenService()
        self.target_images_folder = BASE / "images"
        self.resolution_folder = get_resolution_folder()
        self.reader = easyocr.Reader(['en'])
        self.fish_service = FishService(CONFIG_PATH)

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

    def capture_window(self, window_rect, region=None):
        """
        Take a screenshot of a window or a sub-region.
        window_rect: full window coordinates (x1, y1, x2, y2)
        region: optional tuple (left, top, width, height) relative to window
        Returns a grayscale numpy array
        """
        if not window_rect:
            return None

        x1, y1, x2, y2 = window_rect
        w, h = x2 - x1, y2 - y1

        if region:
            rx, ry, rw, rh = region
            screenshot = self.screen_service.safe_screenshot(
                region=(x1 + rx, y1 + ry, rw, rh)
            )
        else:
            screenshot = self.screen_service.safe_screenshot(region=(x1, y1, w, h))

        if screenshot is None:
            return None

        img_rgb = np.array(screenshot)
        img_gray = cv2.cvtColor(img_rgb, cv2.COLOR_BGR2GRAY)
        return img_gray

    def find_best_matching_fish(self, window_rect, img=None):
        """
        Use OCR to detect the fish name from a cropped region of the window.
        Returns fish_name (str) and confidence (float)
        """
        if img is None:
            img = self.capture_window(window_rect)
        if img is None:
            return None, 0.0

        # Crop area for fish name, adjust as needed
        h, w = img.shape[:2]
        crop_x1 = int(w * 0.56)
        crop_y1 = int(h * 0.66)
        crop_x2 = crop_x1 + int(w * 0.30)
        crop_y2 = crop_y1 + int(h * 0.08)
        crop = img[crop_y1:crop_y2, crop_x1:crop_x2]

        # Run OCR
        result = self.reader.readtext(crop)
        if not result:
            return None, 0.0

        # Take the highest-confidence detection
        best_text, best_conf = "", 0.0
        for _, text, conf in result:
            if conf > best_conf:
                best_text, best_conf = text, conf

        # Normalize the text
        fish_name = best_text.replace(" ", "_").replace("#", "").lower()

        return fish_name, float(best_conf)

    def find_minigame_arrow(self, window_rect, img=None):
        """
        Detect arrows in minigame.
        Uses optional pre-captured img, otherwise captures screenshot.
        Returns best_match and score
        """
        if img is None:
            img = self.capture_window(window_rect)

        if img is None:
            return None, 0.0

        h, w = img.shape
        crop_width = int(w * 0.40)
        crop_height = int(h * 0.20)
        crop_x1 = int(w * 0.30)
        crop_y1 = int(h * 0.40)
        crop_x2 = crop_x1 + crop_width
        crop_y2 = crop_y1 + crop_height
        img_crop = img[crop_y1:crop_y2, crop_x1:crop_x2]

        self.resolution_folder = get_resolution_folder()
        arrow_folder = self.target_images_folder / self.resolution_folder

        templates = ["left-high.png", "right-high.png"]
        best_match = None
        best_score = 0.0

        for template_name in templates:
            template_path = arrow_folder / template_name
            if not template_path.exists():
                continue

            template_img = cv2.imread(str(template_path), cv2.IMREAD_UNCHANGED)
            if template_img is None:
                continue

            if template_img.shape[2] == 4:
                template = cv2.cvtColor(template_img[:, :, :3], cv2.COLOR_BGR2GRAY)
                mask = (template_img[:, :, 3] > 0).astype(np.uint8) * 255
            else:
                template = cv2.cvtColor(template_img, cv2.COLOR_BGR2GRAY)
                mask = None

            try:
                res = cv2.matchTemplate(
                    img_crop.astype(np.uint8),
                    template.astype(np.uint8),
                    cv2.TM_CCOEFF_NORMED,
                    mask=mask,
                )
                _, max_val, _, _ = cv2.minMaxLoc(res)
            except cv2.error:
                max_val = 0.0

            if max_val > best_score:
                best_score = max_val
                best_match = template_name.replace(".png", "")

        return best_match, best_score
