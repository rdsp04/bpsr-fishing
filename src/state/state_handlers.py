import time
from pynput.mouse import Button
from .state_machine import BotState
from src.utils.path import get_data_dir
from src.screen_reader.base import get_resolution_folder
from src.utils.keybinds import get_pykey

TARGET_IMAGES_FOLDER = "images"

class StateHandlers:
    # Add resolution-aware thresholds
    THRESHOLDS = {
        "default_screen": 0.75,      # Was 0.7 - slightly stricter
        "broken_pole": 0.80,         # Was 0.85 - too strict for scaled images
        "catch_fish": 0.80,          # Was 0.85 - too strict
        "continue": 0.70,            # Was 0.75 - more lenient for highlights
        "default_fail": 0.80,        # Was 0.85 - more lenient
        "arrow": 0.70,               # Was 0.75 - more lenient for fast detection
        "use_rod": 0.75,             # Was 0.80 - more lenient
        "fish_type": 0.65            # Was 0.70 - more lenient for variety
    }
    
    def __init__(self, state_machine, detection_buffer, fishing_context, 
                 image_service, mouse, keyboard):
        self.state_machine = state_machine
        self.detection_buffer = detection_buffer
        self.fishing_context = fishing_context
        self.image_service = image_service
        self.mouse = mouse
        self.keyboard = keyboard
        self.last_progress_time = time.time()
        self.saved_continue_pos = None
        self.current_lane = 0
        
    def handle_idle_state(self, rect):
        """Looking for default screen to start fishing"""
        default_found = self.image_service.find_image_in_window(
            rect,
            get_data_dir() / TARGET_IMAGES_FOLDER / get_resolution_folder() / "default_screen.png",
            self.THRESHOLDS["default_screen"]
        )
        
        self.detection_buffer.add("default_screen", default_found is not None)
        
        if self.detection_buffer.is_stable("default_screen", required_count=2):
            # Check for broken rod first
            broken_pole = self.image_service.find_image_in_window(
                rect,
                get_data_dir() / TARGET_IMAGES_FOLDER / get_resolution_folder() / "broken_pole.png",
                self.THRESHOLDS["broken_pole"]
            )
            
            if broken_pole:
                print("[IDLE] Broken rod detected")
                self.state_machine.transition_to(BotState.BROKEN_ROD)
                self.detection_buffer.clear()
            else:
                self.mouse.click(Button.left, 1)
                print("[IDLE] Started fishing")
                self.state_machine.transition_to(BotState.FISHING)
                self.detection_buffer.clear()
                self.last_progress_time = time.time()
        
        if self.state_machine.should_timeout(15):
            print("[IDLE] Timeout - entering recovery")
            self.state_machine.transition_to(BotState.RECOVERY)
    
    def handle_fishing_state(self, rect):
        """Waiting for catch_fish.png to appear"""
        catch_coords = self.image_service.find_image_in_window(
            rect,
            get_data_dir() / TARGET_IMAGES_FOLDER / get_resolution_folder() / "catch_fish.png",
            self.THRESHOLDS["catch_fish"]
        )
        
        if catch_coords:
            self.mouse.position = catch_coords
            time.sleep(0.05)
            self.mouse.press(Button.left)
            print("[FISHING] Catch detected, starting minigame")
            self.state_machine.transition_to(BotState.MINIGAME)
            self.detection_buffer.clear()
            self.last_progress_time = time.time()
            return
        
        if self.state_machine.should_timeout(30):
            print("[FISHING] Timeout - no catch detected")
            self.state_machine.transition_to(BotState.RECOVERY)
    
    def handle_minigame_state(self, rect, spam_cps=20):
        """Handle the minigame"""
        # Check for failure (default screen)
        default_found = self.image_service.find_image_in_window(
            rect,
            get_data_dir() / TARGET_IMAGES_FOLDER / get_resolution_folder() / "default_screen.png",
            self.THRESHOLDS["default_fail"]
        )
        
        self.detection_buffer.add("default_screen_fail", default_found is not None)
        
        if self.detection_buffer.is_stable("default_screen_fail", required_count=2):
            self.mouse.release(Button.left)
            self._release_arrow_keys()
            self.fishing_context.record_catch(False)
            self.state_machine.transition_to(BotState.IDLE)
            self.last_progress_time = time.time()
            return False

        # Check for continue button
        continue_found = self.image_service.find_image_in_window(
            rect,
            get_data_dir() / TARGET_IMAGES_FOLDER / get_resolution_folder() / "continue.png",
            self.THRESHOLDS["continue"]
        )
        if not continue_found:
            continue_found = self.image_service.find_image_in_window(
                rect,
                get_data_dir() / TARGET_IMAGES_FOLDER / get_resolution_folder() / "continue_highlighted.png",
                self.THRESHOLDS["continue"]
            )
        
        self.detection_buffer.add("continue", continue_found is not None)
        
        if self.detection_buffer.is_stable("continue", required_count=2):
            self.mouse.release(Button.left)
            self._release_arrow_keys()
            if continue_found:
                self.saved_continue_pos = continue_found
            self.state_machine.transition_to(BotState.CATCH_RESULT)
            self.last_progress_time = time.time()
            return
        
        # Arrow detection logic
        arrow, score = self.image_service.find_minigame_arrow(rect)
        
        if arrow is not None and "right" in arrow and score > self.THRESHOLDS["arrow"]:
            self.last_progress_time = time.time()
            self.current_lane = min(1, self.current_lane + 1)
            print(f"Right arrow detected, lane = {self.current_lane}")
            time.sleep(0.2)
        elif arrow is not None and "left" in arrow and score > self.THRESHOLDS["arrow"]:
            self.last_progress_time = time.time()
            self.current_lane = max(-1, self.current_lane - 1)
            print(f"Left arrow detected, lane = {self.current_lane}")
            time.sleep(0.2)
        
        # Apply lane movement
        if self.current_lane == -1:
            self._hold_key(get_pykey("left_key"))
            self._release_key(get_pykey("right_key"))
        elif self.current_lane == 0:
            self._release_key(get_pykey("left_key"))
            self._release_key(get_pykey("right_key"))
        elif self.current_lane == 1:
            self._hold_key(get_pykey("right_key"))
            self._release_key(get_pykey("left_key"))
        
        time.sleep(1 / spam_cps)
        
        return None
    
    def handle_catch_result_state(self, rect, fish_service, log_catch_func, session_stats, update_stats_func):
        """Process catch result and click continue"""
        # Detect fish type
        fish_type, score = self.image_service.find_best_matching_fish(rect)
        
        if fish_type and score >= self.THRESHOLDS["fish_type"]:
            print(f"Detected fish type: {fish_type} (score: {score:.3f})")
            log_catch_func(status=True, fish_type=fish_type)
            session_stats["xp"] += fish_service.get_xp_by_type(fish_type=fish_type)
        else:
            print("No fish type detected")
            log_catch_func(status=True)
            session_stats["xp"] += 1
        
        session_stats["catches"] += 1
        self.fishing_context.record_catch(True)
        
        total = session_stats["catches"] + session_stats["misses"]
        session_stats["rate"] = round((session_stats["catches"] / total) * 100, 2) if total > 0 else 0.0
        update_stats_func()
        
        # Click continue
        if self.saved_continue_pos:
            for attempt in range(3):
                self.mouse.position = self.saved_continue_pos
                time.sleep(0.05)
                self.mouse.click(Button.left, 1)
                time.sleep(0.5)
                
                still_there = self.image_service.find_image_in_window(
                    rect,
                    get_data_dir() / TARGET_IMAGES_FOLDER / get_resolution_folder() / "continue.png",
                    self.THRESHOLDS["continue"]
                )
                if not still_there:
                    break
        
        self.state_machine.transition_to(BotState.IDLE)
        self.last_progress_time = time.time()
    
    def handle_broken_rod_state(self, rect):
        """Handle broken fishing rod"""
        print("Broken pole detected -> opening rod menu")
        self._press_key(get_pykey("rods_key"))
        time.sleep(0.5)
        
        use_rod = self.image_service.find_image_in_window(
            rect,
            get_data_dir() / TARGET_IMAGES_FOLDER / get_resolution_folder() / "use_rod.png",
            self.THRESHOLDS["use_rod"]
        )
        
        if use_rod:
            self.mouse.position = use_rod
            time.sleep(0.05)
            self.mouse.click(Button.left, 1)
            time.sleep(1)
            self.state_machine.transition_to(BotState.IDLE)
            self.last_progress_time = time.time()
        else:
            print("Use rod button not found")
            self.state_machine.transition_to(BotState.RECOVERY)
    
    def handle_recovery_state(self, rect, handle_stop_func, handle_start_func):
        """Smart recovery based on context"""
        print(f"Recovery attempt (failures: {self.fishing_context.consecutive_failures})")
        
        default_found = self.image_service.find_image_in_window(
            rect,
            get_data_dir() / TARGET_IMAGES_FOLDER / get_resolution_folder() / "default_screen.png",
            self.THRESHOLDS["default_fail"]
        )
        
        if default_found:
            print("Recovery successful - back to default screen")
            self.detection_buffer.clear()
            self.state_machine.transition_to(BotState.IDLE)
            self.last_progress_time = time.time()
            return
        
        recovery_time = self.state_machine.time_in_state()
        
        if recovery_time < 2:
            self._press_key(get_pykey("esc_key"))
        elif recovery_time < 5:
            self._press_key(get_pykey("esc_key"))
            time.sleep(0.5)
            self._press_key(get_pykey("fish_key"))
        else:
            print("Heavy recovery - full restart sequence")
            if self.fishing_context.should_force_recovery():
                handle_stop_func()
                time.sleep(1)
                handle_start_func()
            self.state_machine.transition_to(BotState.IDLE)
        
        time.sleep(1)
    
    def _press_key(self, key):
        time.sleep(0.05)
        self.keyboard.press(key)
        self.keyboard.release(key)
    
    def _hold_key(self, key):
        self.keyboard.press(key)
    
    def _release_key(self, key):
        self.keyboard.release(key)
    
    def _release_arrow_keys(self):
        self._release_key(get_pykey("left_key"))
        self._release_key(get_pykey("right_key"))
        self.current_lane = 0