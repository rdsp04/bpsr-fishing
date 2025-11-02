import time
import mss
from PIL import Image


class ScreenService:
    def __init__(self, region=None):
        """
        region: optional tuple (left, top, width, height)
        Works across all monitors using mss.
        """
        self.region = region
        self.sct = mss.mss()

    def safe_screenshot(self, region=None, retries=5, delay=2):
        """Take a screenshot safely. Retries if it fails."""

        print(region)
        for i in range(retries):
            try:
                return self._capture(region or self.region)
            except Exception as e:
                print(f"Screenshot failed: {e}")
                print(f"Retrying ({i + 1}/{retries})...")
                time.sleep(delay)
        return None

    def screenshot(self):
        """Take a screenshot of the entire screen or a region"""
        return self._capture(self.region)

    def _capture(self, region):
        """Internal: capture using mss, thread-safe"""
        import mss

        with mss.mss() as sct:  # create new instance per call
            if region is None:
                monitor = sct.monitors[0]
            else:
                left, top, width, height = region
                monitor = {"left": left, "top": top, "width": width, "height": height}

            img = sct.grab(monitor)
            return Image.frombytes("RGB", img.size, img.rgb)
