import cv2
import glob
import os
from src.screen_reader.image_service import ImageService
from src.fish.fish_service import FishService
from src.utils.path import get_data_dir

# Folder with images
image_folder = "tests/assets/1920x1080"

# Initialize services with config path
BASE = get_data_dir()
CONFIG_PATH = BASE / "config/fish_config.json"
image_service = ImageService()
fish_service = FishService(CONFIG_PATH)
fish_service.load_fishes()  # Load the fish list

for image_path in glob.glob(os.path.join(image_folder, "*")):
    img_name = os.path.basename(image_path)

    img = cv2.imread(image_path)
    if img is None:
        print(f"Failed to load image: {img_name}")
        continue

    # Let the service handle cropping internally
    fish_name, confidence = image_service.find_best_matching_fish(None, img)

    if not fish_name:
        print(f"Image: {img_name} -> No OCR text detected!")
        continue

    print(f"Image: {img_name}")
    print(f"OCR: {{'text': '{fish_name}', 'confidence': {confidence}}}")

    # Compare against loaded fish list
    fish_obj = fish_service.get_by_id(fish_name)
    if fish_obj:
        print(f"Detected fish exists in FishService ✅\n")
    else:
        print(f"WARNING: Detected fish '{fish_name}' not found in FishService!\n")
