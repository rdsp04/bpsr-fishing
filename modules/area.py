import pyautogui
import cv2
import numpy as np

# ----------------------
# Predefined scroll div
# ----------------------
scroll_div = {"x1": 395, "y1": 175, "x2": 845, "y2": 910}

print(f"Scroll div saved: {scroll_div}")

# ----------------------
# Take screenshot
# ----------------------
screenshot = pyautogui.screenshot()
img = np.array(screenshot)
img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

# Draw scroll div
cv2.rectangle(img, (scroll_div["x1"], scroll_div["y1"]),
              (scroll_div["x2"], scroll_div["y2"]), (0, 255, 0), 2)

# ----------------------
# Function to select new rectangle
# ----------------------
coords = []

def click_event(event, x, y, flags, param):
    global coords
    if event == cv2.EVENT_LBUTTONDOWN:
        coords.append((x, y))
        print(f"Point recorded: {(x, y)}")
        if len(coords) == 2:
            cv2.rectangle(img, coords[0], coords[1], (255, 0, 0), 2)
            cv2.imshow("Screenshot", img)

cv2.imshow("Screenshot", img)
cv2.setMouseCallback("Screenshot", click_event)
cv2.waitKey(0)
cv2.destroyAllWindows()

if len(coords) == 2:
    new_area = {"x1": coords[0][0], "y1": coords[0][1],
                "x2": coords[1][0], "y2": coords[1][1]}
    print(f"New area saved: {new_area}")
