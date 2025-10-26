import cv2
import numpy as np
from skimage.feature import match_template
from skimage import io, img_as_float

def find_best_match(bg_path, target_path, scale_range=(0.5, 1.5), steps=21):
    # Load background
    bg_cv = cv2.imread(bg_path)
    bg_gray = cv2.cvtColor(bg_cv, cv2.COLOR_BGR2GRAY)
    bg_sk = img_as_float(io.imread(bg_path))
    bg_sk_gray = np.dot(bg_sk[..., :3], [0.2989, 0.5870, 0.1140])

    # Load target
    target_cv = cv2.imread(target_path, cv2.IMREAD_UNCHANGED)
    if target_cv.shape[2] == 4:
        bgr_target = target_cv[:, :, :3]
        alpha = target_cv[:, :, 3]
        mask_template = (alpha > 0).astype(np.uint8) * 255
    else:
        bgr_target = target_cv
        mask_template = None

    target_sk = img_as_float(io.imread(target_path))
    target_sk_gray = np.dot(target_sk[..., :3], [0.2989, 0.5870, 0.1140])
    gray_target = cv2.cvtColor(bgr_target, cv2.COLOR_BGR2GRAY)

    scales = np.linspace(scale_range[0], scale_range[1], steps)

    # --------------------
    # OpenCV template matching
    # --------------------
    best_val_cv, best_scale_cv = -1, 1.0
    for scale in scales:
        h, w = int(bgr_target.shape[0]*scale), int(bgr_target.shape[1]*scale)
        scaled_target = cv2.resize(bgr_target, (w, h))
        scaled_mask = cv2.resize(mask_template, (w, h)) if mask_template is not None else None
        res = cv2.matchTemplate(bg_cv, scaled_target, cv2.TM_CCOEFF_NORMED, mask=scaled_mask)
        _, max_val, _, _ = cv2.minMaxLoc(res)
        if max_val > best_val_cv:
            best_val_cv = max_val
            best_scale_cv = scale

    # --------------------
    # scikit-image template matching
    # --------------------
    best_val_sk, best_scale_sk = -1, 1.0
    for scale in scales:
        h, w = int(target_sk_gray.shape[0]*scale), int(target_sk_gray.shape[1]*scale)
        scaled_target_sk = cv2.resize(target_sk_gray, (w, h))
        res_sk = match_template(bg_sk_gray, scaled_target_sk)
        max_val_sk = np.max(res_sk)
        if max_val_sk > best_val_sk:
            best_val_sk = max_val_sk
            best_scale_sk = scale

    # --------------------
    # SIFT feature matching
    # --------------------
    sift = cv2.SIFT_create()
    kp_bg, des_bg = sift.detectAndCompute(bg_gray, None)
    best_accuracy_sift, best_scale_sift = 0, 1.0
    for scale in scales:
        h, w = int(gray_target.shape[0]*scale), int(gray_target.shape[1]*scale)
        scaled_gray_target = cv2.resize(gray_target, (w, h))
        kp_t, des_t = sift.detectAndCompute(scaled_gray_target, None)
        if des_t is None or des_bg is None:
            continue
        bf = cv2.BFMatcher()
        matches = bf.knnMatch(des_t, des_bg, k=2)
        good = [m for m, n in matches if m.distance < 0.75 * n.distance]
        accuracy = len(good) / max(1, len(kp_t))
        if accuracy > best_accuracy_sift:
            best_accuracy_sift = accuracy
            best_scale_sift = scale

    return {
        "OpenCV": {"score": best_val_cv, "scale": best_scale_cv},
        "scikit-image": {"score": best_val_sk, "scale": best_scale_sk},
        "SIFT": {"score": best_accuracy_sift, "scale": best_scale_sift}
    }

# --------------------
# Example usage
# --------------------

results = find_best_match("screenshots/astermackere_test_1920x1080.png", "images/1920x1080/fish/astermackere.png")
print(results)
