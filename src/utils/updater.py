import requests
import os
import subprocess
import sys
import tempfile
import json

APP_VERSION = "v1.1.0"
LATEST_URL = "https://github.com/rdsp04/bpsr-fishing/main/latest.json"

def check_for_update():
    try:
        r = requests.get(LATEST_URL, timeout=5)
        if r.status_code != 200:
            return None
        latest = r.json()
        if latest["version"] != APP_VERSION:
            return latest
    except Exception:
        return None
    return None

def download_and_install_update(latest):
    exe_url = latest["url"]
    temp_path = os.path.join(tempfile.gettempdir(), "bpsr_fishing_update.exe")

    print("Downloading update...")
    r = requests.get(exe_url, stream=True)
    with open(temp_path, "wb") as f:
        for chunk in r.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)

    # Relaunch your application
    python_exe = sys.executable  # path to current python exe (if running from script)
    app_path = os.path.abspath(sys.argv[0])
    subprocess.Popen([python_exe, app_path])
    sys.exit(0)
