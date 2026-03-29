import random
from hex import Hex

def get_random_passable_hex(grid):
    valid_tiles = [t for t in grid if t.element not in ["stone", "metal"] and not t.has_city]
    if not valid_tiles:
        return Hex(0, 0)
    return random.choice(valid_tiles).position