SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
HEX_SIZE = 40
FPS = 60

COLOR_BG = (30, 30, 30)
COLOR_PLAYER = (50, 150, 255)
COLOR_SWORD = (200, 200, 200)
COLOR_SWORD_HILT = (139, 69, 19)

ELEMENT_COLORS = {
    "light": (255, 255, 255),
    "lightning": (255, 245, 120),
    "fire": (220, 45, 45),
    "wind": (255, 218, 228),
    "creature": (175, 130, 95),
    "water": (45, 95, 195),
    "plant": (45, 145, 55),
    "earth": (75, 48, 28),
    "stone": (68, 68, 72),
    "metal": (178, 182, 188),
    "ice": (175, 225, 255),
    "dark": (18, 18, 18),
}

ELEMENTS = tuple(ELEMENT_COLORS.keys())