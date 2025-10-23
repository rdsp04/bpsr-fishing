import subprocess
import yaml
import os
import sys

# Load YAML
with open("builder.yaml", "r") as f:
    config = yaml.safe_load(f)

# ---------------- PyInstaller ----------------
pyinstaller_cmd = ["pyinstaller"]

if config["pyinstaller"].get("onefile"):
    pyinstaller_cmd.append("--onefile")
if config["pyinstaller"].get("windowed"):
    pyinstaller_cmd.append("--windowed")
if icon := config["pyinstaller"].get("icon"):
    pyinstaller_cmd += ["--icon", icon]

for add in config["pyinstaller"].get("add_data", []):
    pyinstaller_cmd += ["--add-data", add]

entry = config["pyinstaller"]["entry_script"]
pyinstaller_cmd.append(entry)

print("Running PyInstaller:", " ".join(pyinstaller_cmd))
subprocess.run(pyinstaller_cmd, check=True)

# ---------------- NSIS ----------------
nsis_cfg = config.get("nsis")
if nsis_cfg:
    print("Running NSIS...")
    nsis_cmd = ["makensis", nsis_cfg["script"]]
    subprocess.run(nsis_cmd, check=True)
    print("Installer generated:", nsis_cfg.get("output", "dist_installer.exe"))
