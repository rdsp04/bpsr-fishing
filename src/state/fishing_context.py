import time

class FishingContext:
    def __init__(self):
        self.last_catch_time = None
        self.last_minigame_time = None
        self.consecutive_failures = 0
        self.consecutive_successes = 0
        
    def record_catch(self, success):
        if success:
            self.consecutive_successes += 1
            self.consecutive_failures = 0
            self.last_catch_time = time.time()
        else:
            self.consecutive_failures += 1
            self.consecutive_successes = 0
            
    def time_since_last_catch(self):
        if not self.last_catch_time:
            return float('inf')
        return time.time() - self.last_catch_time
        
    def should_force_recovery(self):
        """Determine if pattern suggests we're stuck"""
        return (self.consecutive_failures > 3 or 
                self.time_since_last_catch() > 60)
    
    def reset(self):
        """Reset context when macro stops/starts"""
        self.last_catch_time = None
        self.last_minigame_time = None
        self.consecutive_failures = 0
        self.consecutive_successes = 0