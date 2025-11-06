import json
from .base import Fish, Rarity

class FishService:
    def __init__(self, config_path: str):
        self.config_path = config_path
        self.fishes = []

    def load_fishes(self):
        with open(self.config_path, "r") as file:
            data = json.load(file)
        self.fishes = [
            Fish(
                id=entry["id"],
                image=entry["image"],
                name=entry["name"],
                xp=entry["xp"],
                rarity=Rarity[entry["rarity"]]
            )
            for entry in data["fishes"]
        ]

    def get_all(self):
        return self.fishes

    def get_by_rarity(self, rarity: Rarity):
        return [fish for fish in self.fishes if fish.rarity == rarity]

    def get_xp_by_type(self, fish_type: str) -> int:
        """Return XP value for a given fish name or ID."""
        for fish in self.fishes:
            if fish.name.lower() == fish_type.lower() or fish.id == fish_type:
                return fish.xp
        return 0

    def get_by_name(self, name: str):
        """Return the Fish object with the given name, or None if not found."""
        name_lower = name.lower()
        for fish in self.fishes:
            if fish.name.lower() == name_lower:
                return fish
        return None

    def get_by_id(self, id: str):
        """Return the Fish object with the given name, or None if not found."""
        id_lower = id.lower()
        for fish in self.fishes:
            if fish.id.lower() == id_lower:
                return fish
        return None
