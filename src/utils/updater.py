import os
import sys
import tempfile
import subprocess
import threading
import requests
import webview
import ctypes

APP_VERSION = "v1.0.0"
LATEST_URL = "https://raw.githubusercontent.com/rdsp04/bpsr-fishing/main/latest.json"

class UpdateApi:
    def __init__(self):
        self.window = None

    def set_progress(self, percent, downloaded_mb=None, total_mb=None):
        """Update progress bar and optional text"""
        js = f"setProgress({percent}"
        if downloaded_mb is not None and total_mb is not None:
            js += f", '{downloaded_mb:.1f}MB / {total_mb:.1f}MB'"
        js += ");"
        if self.window:
            self.window.evaluate_js(js)

def check_for_update():
    """Check latest.json for a newer version"""
    try:
        r = requests.get(LATEST_URL, timeout=5)
        r.raise_for_status()
        latest = r.json()
        if latest["version"] != APP_VERSION:
            return latest
    except Exception:
        return None
    return None

def download_update(latest, api):
    """Download the update with GUI progress"""
    temp_path = os.path.join(tempfile.gettempdir(), "bpsr_fishing_update.exe")
    if os.path.exists(temp_path):
        os.remove(temp_path)

    response = requests.get(latest["url"], stream=True)
    total = int(response.headers.get("content-length", 0))
    downloaded = 0

    total_mb = total / (1024*1024)

    with open(temp_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)
                downloaded += len(chunk)
                percent = int(downloaded / total * 100)
                downloaded_mb = downloaded / (1024*1024)
                api.set_progress(percent, downloaded_mb, total_mb)

    # Run installer silently
    subprocess.Popen([temp_path, "/UPDATER /S "], shell=True)
    if api.window:
        api.window.destroy()
    sys.exit(0)
def run_update(latest):
    """Show update window and start download"""
    api = UpdateApi()
    html = """
    <!DOCTYPE html>
    <html>
      <head>
        <meta charset="utf-8">
        <title>Updating</title>
        <style>
          body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            text-align: center;
            background-color: #f0f0f0;
            margin: 0;
            padding: 20px;
          }
          h3 {
            margin-bottom: 20px;
            color: #333;
          }
          #progress-container {
            width: 80%;
            height: 30px;
            margin: auto;
            background-color: #ddd;
            border-radius: 15px;
            box-shadow: inset 0 2px 5px rgba(0,0,0,0.2);
          }
          #bar {
            height: 100%;
            width: 0%;
            background: linear-gradient(90deg, #4caf50, #81c784);
            border-radius: 15px;
            transition: width 0.2s;
          }
          #percent {
            margin-top: 10px;
            font-weight: bold;
            color: #555;
          }
        </style>
      </head>
      <body>
        <h3>Updating...</h3>
        <div id="progress-container">
          <div id="bar"></div>
        </div>
        <p id="percent">0%</p>
      </body>
      <script>
        function setProgress(percent, text){
          document.getElementById('bar').style.width = percent + '%';
          document.getElementById('percent').innerText = text ? text : percent + '%';
        }
      </script>
    </html>
    """
    # Center window on screen
    user32 = ctypes.windll.user32
    screen_width = user32.GetSystemMetrics(0)
    screen_height = user32.GetSystemMetrics(1)

    window_width = 400
    window_height = 250
    x = int((screen_width - window_width) / 2)
    y = int((screen_height - window_height) / 2)

    api.window = webview.create_window(
        "Updating...",
        html=html,
        width=window_width,
        height=window_height,
        resizable=False,
        x=x,
        y=y
    )

    threading.Thread(target=download_update, args=(latest, api), daemon=True).start()
    webview.start(debug=False)


if __name__ == "__main__":
    latest = check_for_update()
    if latest:
        print(f"New version available: {latest['version']}")
        run_update(latest)
    else:
        print("No updates found. App is up to date.")
