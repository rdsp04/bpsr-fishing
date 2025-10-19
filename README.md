# Running the Python Macro Project

## 1. Clone the repository
git clone https://github.com/rdsp04/bpsr-fishing.git

## 2. Create a virtual environment
python -m venv venv

## 3. Activate the virtual environment

- **Windows (cmd):**
venv\Scripts\activate

- **Windows (PowerShell):**
venv\Scripts\Activate.ps1

- **macOS / Linux:**
source venv/bin/activate

## 4. Install dependencies
If there is a `requirements.txt` file:
pip install -r requirements.txt

Otherwise, install manually:
pip install pyautogui pynput opencv-python numpy pygetwindow win32gui

## 5. Prepare the game
- Set the game window to **1600x900 resolution**
- Run the game in **windowed mode**
- Ensure the player character is in a **fishing position** before starting

## 6. Run the project
python main.py

- Press **s** to start the macro
- Press **x** to pause/stop the macro
- Press **Ctrl + C** to fully exit the program

## 7. Deactivate the virtual environment (optional)
deactivate
