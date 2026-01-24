import cv2
import os
import numpy as np

# Settings
SOURCE_RES = "1920x1080"
TARGET_RES = "1366x768"
SCALE = 1366 / 1920  # Approx 0.71

def resize_images():
    src_dir = os.path.join("images", SOURCE_RES)
    dst_dir = os.path.join("images", TARGET_RES)

    if not os.path.exists(dst_dir):
        os.makedirs(dst_dir)

    print(f"Resizing from {SOURCE_RES} to {TARGET_RES} (Scale: {SCALE:.3f})...")

    for root, dirs, files in os.walk(src_dir):
        # Maintain subfolder structure (e.g. /fish)
        rel_path = os.path.relpath(root, src_dir)
        target_subdir = os.path.join(dst_dir, rel_path)
        if not os.path.exists(target_subdir):
            os.makedirs(target_subdir)

        for file in files:
            if file.endswith(".png"):
                src_path = os.path.join(root, file)
                dst_path = os.path.join(target_subdir, file)

                # IMREAD_UNCHANGED is vital to load the Alpha Channel (Transparency)
                img = cv2.imread(src_path, cv2.IMREAD_UNCHANGED)
                if img is None:
                    continue

                # Calculate new dimensions
                new_w = int(img.shape[1] * SCALE)
                new_h = int(img.shape[0] * SCALE)

                # INTER_AREA is the best algorithm for shrinking images without jagged edges
                resized_img = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)

                cv2.imwrite(dst_path, resized_img)
                print(f"Saved: {file}")

if __name__ == "__main__":
    resize_images()