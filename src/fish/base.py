from enum import Enum


class Rarity(Enum):
    COMMON = "Common"
    RARE = "Rare"
    MYTHICAL = "Mythical"


class Fish:
    def __init__(self, image: str, name: str, xp: int, rarity: Rarity):
        self.image = image
        self.name = name
        self.xp = xp
        self.rarity = rarity

    def __repr__(self):
        return f"{self.name} ({self.rarity.value}, XP: {self.xp})"
