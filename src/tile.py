import random
from config import ELEMENTS

class Tile:
    def __init__(self, position):
        self.position = position
        self.element = random.choice(ELEMENTS)
        self.food = random.randint(0, 5)
        self.gold = random.randint(0, 3)
        self.has_city = False
        self.owner = None
        self.deco_seed = random.randint(0, 2**31 - 1)

    def __str__(self):
        return (
            f"Tile(hex=({self.position.q}, {self.position.r}), "
            f"element={self.element!r}, food={self.food}, gold={self.gold}, "
            f"has_city={self.has_city}, owner={self.owner!r})"
        )