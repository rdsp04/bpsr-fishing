import pyautogui
import time


class ScreenService:
    def __init__(self, region=None):
        """
        region: optional tuple (left, top, width, height)
        """
        self.region = region

    def safe_screenshot(self, region=None, retries=5, delay=2):
        """
        Take a screenshot safely. Retries if it fails.
        region: tuple (left, top, width, height)
        """
        for i in range(retries):
            try:
                return pyautogui.screenshot(region=region)
            except Exception:
                print(f"Screenshot failed, retrying ({i+1}/{retries})...")
                time.sleep(delay)
        return None

    def screenshot(self):
        """Take a screenshot of the entire screen or a region"""
        return pyautogui.screenshot(region=self.region)
