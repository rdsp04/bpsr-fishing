import time
import os
import json
import win32gui
from datetime import datetime
from pynput.mouse import Controller, Button
from pynput.keyboard import Controller as KeyboardController, Listener
import threading
from threading import Event

from src.utils.updater import check_for_update, run_update, UpdateApi

update_api = UpdateApi()

from src.screen_reader.screen_service import ScreenService
from src.screen_reader.image_service import ImageService
from src.ui.ui_service import start_ui, get_window, Window

from log_main import load_sessions, save_sessions
from src.fish.fish_service import FishService

from src.state import FishingStateMachine, BotState, DetectionBuffer, FishingContext, StateHandlers
from src.utils.keybinds import get_keys, key_to_str, get_pykey
from src.utils.path import get_data_dir

# ============ Global Setup ============
macro_start_event = Event()

# Services
screen_service = ScreenService()
image_service = ImageService()

# Paths and configs
BASE = get_data_dir()
CONFIG_PATH = BASE / "config/fish_config.json"
START_KEY, STOP_KEY = get_keys()

# Input devices
mouse = Controller()
keyboard = KeyboardController()

# Fish service
fish_service = FishService(CONFIG_PATH)
fish_service.load_fishes()

# State management
state_machine = FishingStateMachine()
detection_buffer = DetectionBuffer(size=5)
fishing_context = FishingContext()
state_handlers = StateHandlers(
    state_machine, detection_buffer, fishing_context,
    image_service, mouse, keyboard
)

# Session stats
session_stats = {"catches": 0, "misses": 0, "xp": 0, "rate": 0.0}

# Global variables
window_title = None
SPAM_CPS = 20
CHECK_INTERVAL = 0.05

# ============ Logging Functions ============
def log_broken_rod():
    filename = BASE / "logs" / "broken_rods.json"
    filename.parent.mkdir(parents=True, exist_ok=True)
    entry = {"timestamp": datetime.now().isoformat(), "broken": True}
    data = []
    if os.path.exists(filename):
        with open(filename, "r") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                data = []
    data.append(entry)
    with open(filename, "w") as f:
        json.dump(data, f, indent=2)


def log_catch(status, **extra):
    filename = BASE / "logs" / "fishing_log.json"
    filename.parent.mkdir(parents=True, exist_ok=True)
    entry = {"timestamp": datetime.now().isoformat(), "catch": status}
    entry.update(extra)
    data = []
    if os.path.exists(filename):
        with open(filename, "r") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                data = []
    data.append(entry)
    with open(filename, "w") as f:
        json.dump(data, f, indent=2)


def update_ui_stats():
    """Send current stats to overlay UI."""
    overlay = get_window(Window.OVERLAY)
    if overlay:
        overlay.evaluate_js(f"window.updateStats({json.dumps(session_stats)})")


# ============ Window Handling ============
def focus_blue_protocol_window():
    target_title = "Blue Protocol: Star Resonance"
    hwnd = win32gui.FindWindow(None, target_title)
    if hwnd == 0:
        print(f"Window '{target_title}' not found.")
        return None
    try:
        win32gui.ShowWindow(hwnd, 5)
        win32gui.SetForegroundWindow(hwnd)
    except Exception as e:
        print(f"Failed to focus window: {e}")
    return hwnd


def select_window():
    hwnd = focus_blue_protocol_window()
    if hwnd:
        print("Automatically selected Blue Protocol window.")
        return "Blue Protocol: Star Resonance"
    else:
        print("Could not find Blue Protocol window. Waiting...")
        return None


def get_window_rect(title):
    hwnd = win32gui.FindWindow(None, title)
    if not hwnd:
        print(f"Window '{title}' not found.")
        return None
    return win32gui.GetWindowRect(hwnd)


# ============ Keyboard Input Handlers ============
def handle_start_key():
    global macro_start_event, window_title

    overlay = get_window(Window.OVERLAY)
    sessions = load_sessions()

    window_title = select_window()
    if not window_title:
        print("No window found. Cannot start macro.")
        macro_start_event.clear()
        return

    if not sessions or sessions[-1].get("stop") is not None:
        sessions.append({"start": datetime.now().isoformat(), "stop": None})
        save_sessions(sessions)
        if overlay:
            overlay.evaluate_js("window.toggleBotStatus('running');")
        macro_start_event.set()

        # Reset state
        state_machine.transition_to(BotState.IDLE)
        detection_buffer.clear()
        fishing_context.reset()
        
        print(f"Macro started on window: {window_title}")
    else:
        print("Session already started. Press stop first.")


def handle_stop_key():
    global macro_start_event, window_title

    overlay = get_window(Window.OVERLAY)
    sessions = load_sessions()

    if sessions and sessions[-1].get("stop") is None:
        sessions[-1]["stop"] = datetime.now().isoformat()
        save_sessions(sessions)
        macro_start_event.clear()
        window_title = None
        print("Macro stopped")
        if overlay:
            overlay.evaluate_js("window.toggleBotStatus('stopped');")
    else:
        print("No active session to stop.")


def on_press(key):
    pressed_str = key_to_str(key)
    start_key_str, stop_key_str = map(key_to_str, get_keys())

    if pressed_str == start_key_str:
        handle_start_key()
    elif pressed_str == stop_key_str:
        handle_stop_key()


# ============ Main Bot Loop ============
def main():
    global macro_start_event, window_title

    window_title = select_window()
    print(f"Macro waiting for START key ({get_keys()[0]})")

    listener = Listener(on_press=on_press)
    listener.start()

    while True:
        if not macro_start_event.is_set():
            time.sleep(0.1)
            continue

        rect = get_window_rect(window_title)
        if not rect:
            print("Lost window, waiting...")
            time.sleep(1)
            continue
        
        # State-based dispatch
        try:
            if state_machine.state == BotState.IDLE:
                state_handlers.handle_idle_state(rect)
                
            elif state_machine.state == BotState.FISHING:
                state_handlers.handle_fishing_state(rect)
                
            elif state_machine.state == BotState.MINIGAME:
                result = state_handlers.handle_minigame_state(rect, SPAM_CPS)
                if result == False:  # Explicit failure
                    log_catch(False)
                    session_stats["misses"] += 1
                    fishing_context.record_catch(False)
                    total = session_stats["catches"] + session_stats["misses"]
                    session_stats["rate"] = round((session_stats["catches"] / total) * 100, 2) if total > 0 else 0.0
                    update_ui_stats()
                    
            elif state_machine.state == BotState.CATCH_RESULT:
                state_handlers.handle_catch_result_state(
                    rect, fish_service, log_catch, session_stats, update_ui_stats
                )
                
            elif state_machine.state == BotState.BROKEN_ROD:
                log_broken_rod()
                state_handlers.handle_broken_rod_state(rect)
                
            elif state_machine.state == BotState.RECOVERY:
                state_handlers.handle_recovery_state(rect, handle_stop_key, handle_start_key)
                
        except Exception as e:
            print(f"Error in state {state_machine.state.value}: {e}")
            state_machine.transition_to(BotState.RECOVERY)
            
        time.sleep(CHECK_INTERVAL)


def start_macro():
    main()


# ============ Entry Point ============
if __name__ == "__main__":
    from src.utils.refactor.spelling import fix_spelling
    
    try:
        fix_spelling()
        update = check_for_update()
        if update:
            print(f"New version available: {update['version']}")
            run_update(update)
        else:
            print("App is up to date.")

        macro_thread = threading.Thread(target=start_macro, daemon=True)
        macro_thread.start()

        time.sleep(0.5)

        start_ui()
    finally:
        print("App is closing, cleaning up...")
        handle_stop_key()