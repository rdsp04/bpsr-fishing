import cv2
import os
import json
import numpy as np

# --------------------
# Configuration
# --------------------
BG_FOLDER = "assets/1920x1080/"
OUTPUT_JSON = "results.json"
SCALE_RANGE = (1.0, 1.0)
STEPS = 1


# Function to get resolution folder
def get_resolution_folder():
    return "1920x1080"


# --------------------
# Define which images to use
# --------------------
# Background images you want to test
BG_IMAGES = [
    # "abandoned_billboard_test_1920x1080.png",
    # "abandoned_signboard_test_1920x1080.png",
    # "aluminium_billboard_test_1920x1080.png",
    # "aluminium_signboard_test_1920x1080.png",
    # "artisan_tools_test_1920x1080.png",
    # "astercad_test_1920x1080.png",
    # "astermackere_test_1920x1080.png",
    # "azure_damsel_test_1920x1080.png",
    "regnus_bighead_test_1920x1080.png",
    "screenshot_20251026_221424.png"
]

# Fish images you want to target
BASE_FOLDER = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
fish_folder = os.path.join(BASE_FOLDER, "images", get_resolution_folder(), "fish")

FISH_IMAGES = [
    "abandoned_billboard.png",
    "abandoned_signboard.png",
    "aluminium_billboard.png",
    "aluminium_signboard.png",
    "artisan_tools.png",
    "astercad.png",
    "astermackere.png",
    "azure_damsel.png",
    "regnus_bighead.png",
    "starfish.png",
]

# --------------------
# Load fish templates
# --------------------
fish_templates = []
for fname in FISH_IMAGES:
    path = os.path.join(fish_folder, fname)
    if not os.path.exists(path):
        print(f"Warning: fish image not found: {path}")
        continue
    img = cv2.imread(path, cv2.IMREAD_UNCHANGED)
    if img is None:
        continue
    if img.shape[2] == 4:
        bgr = img[:, :, :3]
        alpha = img[:, :, 3]
        mask = (alpha > 0).astype(np.uint8) * 255
    else:
        bgr = img
        mask = None
    fish_templates.append({"name": fname, "image": bgr, "mask": mask})

if not fish_templates:
    print("No valid fish templates found.")
    exit(1)


# --------------------
# Template match function
# --------------------
def best_template_match(bg_cv, target_img, mask=None):
    # Ensure correct data type
    bg_cv = bg_cv.astype(np.uint8)
    target_img = target_img.astype(np.uint8)

    # Sanity check for dimensions
    if bg_cv.shape[0] < target_img.shape[0] or bg_cv.shape[1] < target_img.shape[1]:
        return 0.0, 1.0

    # Check if background or target is uniform (flat color)
    if np.std(bg_cv) < 1e-6 or np.std(target_img) < 1e-6:
        print("Skipped flat image (no variation).")
        return 0.0, 1.0

    try:
        res = cv2.matchTemplate(bg_cv, target_img, cv2.TM_CCOEFF_NORMED, mask=mask)
        if not np.isfinite(res).all():
            return 0.0, 1.0

        _, max_val, _, _ = cv2.minMaxLoc(res)
        if not np.isfinite(max_val):
            max_val = 0.0
        return float(max_val), 1.0

    except cv2.error as e:
        print(f"OpenCV error during matchTemplate: {e}")
        return 0.0, 1.0


# --------------------
# Run test
# --------------------
results = []
for bg_fname in BG_IMAGES:
    bg_path = os.path.join(BG_FOLDER, bg_fname)
    if not os.path.exists(bg_path):
        print(f"Warning: background image not found: {bg_path}")
        continue
    bg_cv = cv2.imread(bg_path)
    if bg_cv is None:
        continue

    for fish in fish_templates:
        accuracy, scale = best_template_match(
            bg_cv, fish["image"], fish["mask"]
        )
        expected_string = "expected_placeholder"

        results.append([bg_fname, expected_string, fish["name"], float(accuracy)])
        print(
            f"Processed BG: {bg_fname}, Target: {fish['name']}, Accuracy: {accuracy:.3f}, Scale: {scale:.2f}"
        )

# --------------------
# Save results
# --------------------
with open(OUTPUT_JSON, "w") as f:
    json.dump(results, f, indent=4)

print(f"Results saved to {OUTPUT_JSON}")
