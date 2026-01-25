import time
from enum import Enum

class BotState(Enum):
    IDLE = "idle"
    FISHING = "fishing"
    MINIGAME = "minigame"
    CATCH_RESULT = "catch_result"
    BROKEN_ROD = "broken_rod"
    RECOVERY = "recovery"

class FishingStateMachine:
    def __init__(self):
        self.state = BotState.IDLE
        self.state_start_time = time.time()
        self.failed_detections = 0
        
    def transition_to(self, new_state):
        print(f"State: {self.state.value} -> {new_state.value}")
        self.state = new_state
        self.state_start_time = time.time()
        self.failed_detections = 0
        
    def time_in_state(self):
        return time.time() - self.state_start_time
        
    def should_timeout(self, max_seconds):
        return self.time_in_state() > max_seconds