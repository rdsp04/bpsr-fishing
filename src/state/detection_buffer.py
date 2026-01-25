import time

class DetectionBuffer:
    def __init__(self, size=3):
        self.buffer = []
        self.size = size
        
    def add(self, detection_name, found):
        """Track if detection was found (True/False)"""
        self.buffer.append((detection_name, found, time.time()))
        if len(self.buffer) > self.size:
            self.buffer.pop(0)
            
    def is_stable(self, detection_name, required_count=2):
        """Check if detection appeared in at least N recent frames"""
        recent = [found for name, found, _ in self.buffer if name == detection_name]
        return sum(recent) >= required_count
        
    def clear(self):
        self.buffer.clear()