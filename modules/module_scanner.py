import pyautogui
import cv2
import numpy as np
import easyocr
import time
import json

# ------------------------
# Coordinates
# ------------------------
scroll_div = (395, 175, 845, 910)
stat1_div = (921, 676, 1381, 752)
stat2_div = (920, 585, 1383, 664)

ROWS, COLS = 6, 5
reader = easyocr.Reader(['en'])

def read_text(crop):
    result = reader.readtext(crop)
    texts = []
    for _, text, conf in result:
        # Try to extract numbers if possible
        try:
            num = int(''.join(filter(str.isdigit, text)))
        except:
            num = 0
        texts.append((text, num, conf))
    return texts

def read_last_row():
    last_row_results = []
    for col in range(COLS):
        click_x = scroll_div[0] + col * cell_w + cell_w // 2
        click_y = scroll_div[1] + (ROWS - 1) * cell_h + cell_h // 2

        pyautogui.click(click_x, click_y)
        time.sleep(0.3)

        screenshot = pyautogui.screenshot()
        img = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

        stat1_crop = img[stat1_div[1]:stat1_div[3], stat1_div[0]:stat1_div[2]]
        stat2_crop = img[stat2_div[1]:stat2_div[3], stat2_div[0]:stat2_div[2]]

        stat1_text = read_text(stat1_crop)
        stat2_text = read_text(stat2_crop)

        last_row_results.append({
            'col': col,
            'stat1': stat1_text,
            'stat2': stat2_text
        })
    return last_row_results

# ------------------------
# Initial setup
# ------------------------
screenshot = pyautogui.screenshot()
img = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
scroll_crop_w = scroll_div[2] - scroll_div[0]
scroll_crop_h = scroll_div[3] - scroll_div[1]
cell_w = 90
cell_h = 115

# ------------------------
# Read all rows except last
# ------------------------
all_results = []
for row in range(ROWS - 1):
    for col in range(COLS):
        click_x = scroll_div[0] + col * cell_w + cell_w // 2
        click_y = scroll_div[1] + row * cell_h + cell_h // 2

        pyautogui.click(click_x, click_y)
        time.sleep(0.3)

        screenshot = pyautogui.screenshot()
        img = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

        stat1_crop = img[stat1_div[1]:stat1_div[3], stat1_div[0]:stat1_div[2]]
        stat2_crop = img[stat2_div[1]:stat2_div[3], stat2_div[0]:stat2_div[2]]

        stat1_text = read_text(stat1_crop)
        stat2_text = read_text(stat2_crop)

        all_results.append({
            'module': row * COLS + col + 1,
            'statA': {'name': stat1_text[0][0], 'value': stat1_text[0][1]},
            'statB': {'name': stat2_text[0][0], 'value': stat2_text[0][1]}
        })

# ------------------------
# Scroll loop
# ------------------------
seen_rows = set()
while True:
    last_row = read_last_row()

    last_row_tuple = tuple(tuple(item['stat1'] + item['stat2']) for item in last_row)
    if last_row_tuple in seen_rows:
        print("Reached repeated row. Stopping scroll.")
        break

    seen_rows.add(last_row_tuple)
    for item in last_row:
        all_results.append({
            'module': 'scrolled',
            'statA': {'name': item['stat1'][0][0], 'value': item['stat1'][0][1]},
            'statB': {'name': item['stat2'][0][0], 'value': item['stat2'][0][1]}
        })

    # Scroll down 130 px
    start_x = scroll_div[0] + scroll_crop_w - 10
    start_y = scroll_div[1] + 10
    end_y = start_y - 113

    pyautogui.moveTo(start_x, start_y)
    pyautogui.mouseDown()
    pyautogui.moveTo(start_x, end_y, duration=0.7)
    pyautogui.mouseUp()
    time.sleep(0.3)

# ------------------------
# Save to JSON
# ------------------------
with open("modules_stats.json", "w") as f:
    json.dump(all_results, f, indent=4)

print("Saved results to modules_stats.json")
