import pygame
import math
import random

# Constants
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
HEX_SIZE = 40
FPS = 60

# Colors (from docs/elements.md; Lightning/Creature had no color in doc — see comments)
COLOR_BG = (30, 30, 30)
COLOR_PLAYER = (50, 150, 255)
COLOR_SWORD = (200, 200, 200)
COLOR_SWORD_HILT = (139, 69, 19)

class Hex:
    def __init__(self, q, r):
        self.q = q
        self.r = r

    def __eq__(self, other):
        return self.q == other.q and self.r == other.r

    def __hash__(self):
        return hash((self.q, self.r))

    def to_pixel(self):
        x = HEX_SIZE * 3/2 * self.q
        y = HEX_SIZE * math.sqrt(3) * (self.r + self.q/2)
        return (x + SCREEN_WIDTH // 2, y + SCREEN_HEIGHT // 2)

    @staticmethod
    def from_pixel(x, y):
        x_adj = x - SCREEN_WIDTH // 2
        y_adj = y - SCREEN_HEIGHT // 2
        q = (2/3 * x_adj) / HEX_SIZE
        r = (-1/3 * x_adj + math.sqrt(3)/3 * y_adj) / HEX_SIZE
        return Hex.round(q, r)

    @staticmethod
    def round(q, r):
        s = -q - r
        rq = round(q)
        rr = round(r)
        rs = round(s)

        dq = abs(rq - q)
        dr = abs(rr - r)
        ds = abs(rs - s)

        if dq > dr and dq > ds:
            rq = -rr - rs
        elif dr > ds:
            rr = -rq - rs
        
        return Hex(rq, rr)

ELEMENT_COLORS = {
    "light": (255, 255, 255),
    "lightning": (255, 245, 120),  # doc blank — electric yellow
    "fire": (220, 45, 45),
    "wind": (255, 218, 228),  # pale pink
    "creature": (175, 130, 95),  # doc "t" — tan / organic
    "water": (45, 95, 195),
    "plant": (45, 145, 55),
    "earth": (75, 48, 28),
    "stone": (68, 68, 72),
    "metal": (178, 182, 188),
    "ice": (175, 225, 255),
    "dark": (18, 18, 18),
}

ELEMENTS = tuple(ELEMENT_COLORS.keys())

def element_hover_color(element):
    r, g, b = ELEMENT_COLORS[element]
    return (min(255, r + 45), min(255, g + 45), min(255, b + 45))

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

def get_hex_corners(center):
    corners = []
    for i in range(6):
        angle_deg = 60 * i
        angle_rad = math.pi / 180 * angle_deg
        corners.append((center[0] + HEX_SIZE * math.cos(angle_rad),
                        center[1] + HEX_SIZE * math.sin(angle_rad)))
    return corners

def _darker(rgb, factor):
    return tuple(max(0, int(c * factor)) for c in rgb)

def _lighter(rgb, delta):
    return tuple(min(255, int(c + delta)) for c in rgb)

def _blend(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))

def draw_tile_hex(surface, tile, center, corners, base_color):
    """Fill hex, draw element-specific interior style, then black outline."""
    cx, cy = center
    cx, cy = float(cx), float(cy)
    rnd = random.Random(tile.deco_seed)
    # Safe radius so radial motifs stay inside the hex (flat-edge limited)
    inner_r = HEX_SIZE * 0.82

    elem = tile.element
    outline_w = 2

    def outline():
        pygame.draw.polygon(surface, (0, 0, 0), corners, outline_w)

    if elem == "water":
        fill = _darker(base_color, 0.52)
        pygame.draw.polygon(surface, fill, corners)
        wave_col = _lighter(_blend(fill, (200, 230, 255), 0.55), 12)
        amp = 4.0
        for row in range(5):
            t_off = rnd.uniform(0, 6.28)
            y_base = cy - inner_r * 0.85 + row * (inner_r * 0.42)
            pts = []
            steps = 24
            for s in range(steps + 1):
                t = s / steps
                x = cx - inner_r * 0.92 + t * (inner_r * 1.84)
                y = y_base + amp * math.sin(t * 4.2 * math.pi + t_off + row * 0.7)
                pts.append((x, y))
            for i in range(len(pts) - 1):
                pygame.draw.line(surface, wave_col, pts[i], pts[i + 1], 2)

    elif elem == "plant":
        pygame.draw.polygon(surface, base_color, corners)
        blade_hi = _lighter(base_color, 55)
        blade_lo = _darker(base_color, 0.75)
        for _ in range(22):
            ang = rnd.uniform(0, 2 * math.pi)
            dist = rnd.uniform(0.15, 0.88) * inner_r
            bx = cx + math.cos(ang) * dist
            by = cy + math.sin(ang) * dist
            h = rnd.uniform(5, 11)
            w = rnd.uniform(2.5, 5.0)
            col = blade_hi if rnd.random() > 0.4 else blade_lo
            top = (bx, by - h)
            pygame.draw.line(surface, col, (bx - w * 0.5, by), top, 2)
            pygame.draw.line(surface, col, (bx + w * 0.5, by), top, 2)

    elif elem == "earth":
        pygame.draw.polygon(surface, base_color, corners)
        for _ in range(38):
            ang = rnd.uniform(0, 2 * math.pi)
            dist = rnd.uniform(0.1, 0.92) * inner_r
            px = cx + math.cos(ang) * dist
            py = cy + math.sin(ang) * dist
            r = rnd.randint(1, 3)
            c = _lighter(base_color, rnd.randint(8, 35)) if rnd.random() > 0.5 else _darker(base_color, rnd.uniform(0.55, 0.85))
            pygame.draw.circle(surface, c, (int(px), int(py)), r)

    elif elem == "stone":
        pygame.draw.polygon(surface, base_color, corners)
        crack = _darker(base_color, 0.45)
        for _ in range(4):
            sx = cx + rnd.uniform(-0.75, 0.75) * inner_r
            sy = cy + rnd.uniform(-0.75, 0.75) * inner_r
            n = rnd.randint(4, 7)
            poly = []
            px, py = sx, sy
            for _i in range(n):
                poly.append((int(px), int(py)))
                px += rnd.uniform(-10, 10)
                py += rnd.uniform(-10, 10)
                px = cx + max(-inner_r, min(inner_r, px - cx))
                py = cy + max(-inner_r, min(inner_r, py - cy))
            if len(poly) >= 2:
                pygame.draw.lines(surface, crack, False, poly, 1)

    elif elem == "fire":
        pygame.draw.polygon(surface, base_color, corners)
        orange = (255, 140, 40)
        yellow = (255, 230, 80)
        for _ in range(7):
            ang = rnd.uniform(-0.5, 0.5) - math.pi / 2
            fx = cx + rnd.uniform(-14, 14)
            fy = cy + rnd.uniform(4, 18)
            h = rnd.uniform(14, 26)
            w = rnd.uniform(6, 12)
            tip = (fx + math.cos(ang) * h * 0.2, fy + math.sin(ang) * h)
            left = (fx - w / 2, fy + rnd.uniform(2, 6))
            right = (fx + w / 2, fy + rnd.uniform(2, 6))
            col = yellow if rnd.random() > 0.55 else orange
            pygame.draw.polygon(surface, col, [tip, left, right])

    elif elem == "ice":
        pygame.draw.polygon(surface, base_color, corners)
        frost = _blend(base_color, (255, 255, 255), 0.45)
        frost2 = _lighter(base_color, 70)
        for angle_deg in (-35, 35, 0):
            rad = math.radians(angle_deg)
            dx, dy = math.cos(rad), math.sin(rad)
            for off in (-10, 0, 10):
                x1 = cx - dx * inner_r * 0.9 + dy * off * 0.3
                y1 = cy - dy * inner_r * 0.9 - dx * off * 0.3
                x2 = cx + dx * inner_r * 0.9 + dy * off * 0.3
                y2 = cy + dy * inner_r * 0.9 - dx * off * 0.3
                pygame.draw.line(surface, frost, (x1, y1), (x2, y2), 2)
        for _ in range(6):
            rad = math.radians(rnd.uniform(-50, 50))
            dx, dy = math.cos(rad), math.sin(rad)
            ln = rnd.uniform(0.25, 0.55) * inner_r
            ox, oy = rnd.uniform(-15, 15), rnd.uniform(-15, 15)
            pygame.draw.line(
                surface, frost2,
                (cx + ox - dx * ln, cy + oy - dy * ln),
                (cx + ox + dx * ln, cy + oy + dy * ln),
                1,
            )

    elif elem == "metal":
        pygame.draw.polygon(surface, base_color, corners)
        shine = _lighter(base_color, 85)
        shine2 = (255, 255, 255)
        for angle_deg in (-40, -15, 25):
            rad = math.radians(angle_deg)
            dx, dy = math.cos(rad), math.sin(rad)
            x1, y1 = cx - dx * inner_r * 0.95, cy - dy * inner_r * 0.95
            x2, y2 = cx + dx * inner_r * 0.95, cy + dy * inner_r * 0.95
            wcol = shine2 if angle_deg == -15 else shine
            pygame.draw.line(surface, wcol, (x1, y1), (x2, y2), 2)
        pygame.draw.line(
            surface, shine2,
            (cx - inner_r * 0.35, cy - inner_r * 0.55),
            (cx + inner_r * 0.15, cy - inner_r * 0.2),
            1,
        )

    elif elem == "dark":
        pygame.draw.polygon(surface, base_color, corners)
        star_c = [(80, 60, 140), (100, 100, 180), (60, 80, 120)]
        for _ in range(14):
            ang = rnd.uniform(0, 2 * math.pi)
            dist = rnd.uniform(0.12, 0.9) * inner_r
            sx = cx + math.cos(ang) * dist
            sy = cy + math.sin(ang) * dist
            col = rnd.choice(star_c)
            arm = rnd.randint(2, 4)
            pygame.draw.line(surface, col, (sx - arm, sy), (sx + arm, sy), 1)
            pygame.draw.line(surface, col, (sx, sy - arm), (sx, sy + arm), 1)

    elif elem == "light":
        pygame.draw.polygon(surface, base_color, corners)
        ray = _darker(base_color, 0.82)
        n_rays = 14
        for i in range(n_rays):
            ang = 2 * math.pi * i / n_rays + rnd.uniform(-0.04, 0.04)
            r0 = inner_r * 0.12
            r1 = inner_r * 0.92
            pygame.draw.line(
                surface, ray,
                (cx + math.cos(ang) * r0, cy + math.sin(ang) * r0),
                (cx + math.cos(ang) * r1, cy + math.sin(ang) * r1),
                2,
            )

    elif elem == "wind":
        pygame.draw.polygon(surface, base_color, corners)
        arc_col = _darker(_blend(base_color, (255, 150, 200), 0.35), 0.75)
        for _ in range(5):
            w = rnd.randint(22, 40)
            h = rnd.randint(14, 28)
            ex = int(cx + rnd.uniform(-inner_r * 0.5, inner_r * 0.5))
            ey = int(cy + rnd.uniform(-inner_r * 0.55, inner_r * 0.55))
            rect = pygame.Rect(ex - w // 2, ey - h // 2, w, h)
            start = rnd.uniform(0.2, 0.8) * 2 * math.pi
            stop = start + rnd.uniform(0.8, 1.6)
            pygame.draw.arc(surface, arc_col, rect, start, stop, 2)

    elif elem == "lightning":
        pygame.draw.polygon(surface, base_color, corners)
        bolt = (200, 160, 40)
        outline_bolt = (80, 60, 20)
        pts = []
        x, y = cx + rnd.uniform(-4, 4), cy - inner_r * 0.75
        pts.append((x, y))
        for _ in range(12):
            if y >= cy + inner_r * 0.65:
                break
            x += rnd.uniform(-12, 12)
            y += rnd.uniform(10, 16)
            pts.append((x, y))
        if len(pts) >= 2:
            pygame.draw.lines(surface, outline_bolt, False, pts, 4)
            pygame.draw.lines(surface, bolt, False, pts, 2)

    elif elem == "creature":
        pygame.draw.polygon(surface, base_color, corners)
        eye = (35, 28, 22)
        eye_y = int(cy - inner_r * 0.08)
        pygame.draw.circle(surface, eye, (int(cx - inner_r * 0.22), eye_y), 4)
        pygame.draw.circle(surface, eye, (int(cx + inner_r * 0.22), eye_y), 4)
        pygame.draw.circle(surface, (255, 255, 255), (int(cx - inner_r * 0.22) + 1, eye_y - 1), 1)
        pygame.draw.circle(surface, (255, 255, 255), (int(cx + inner_r * 0.22) + 1, eye_y - 1), 1)

    else:
        pygame.draw.polygon(surface, base_color, corners)

    outline()

class Character:
    def __init__(self, start_hex):
        self.current_hex = start_hex
        self.target_hex = start_hex
        self.pos = list(start_hex.to_pixel())
        self.start_pos = list(start_hex.to_pixel())
        self.progress = 1.0 # 0.0 to 1.0 during jump
        self.jump_duration = 15 # frames
        self.jump_height = 40

    def jump_to(self, target_hex):
        if self.current_hex != target_hex and self.progress >= 1.0 and self.is_adjacent(target_hex):
            self.start_pos = list(self.pos)
            self.target_hex = target_hex
            self.progress = 0.0


    def is_adjacent(self, target_hex):
        dq = self.current_hex.q - target_hex.q
        dr = self.current_hex.r - target_hex.r
        return (dq, dr) in [(1, 0), (0, 1), (-1, 1), (-1, 0), (0, -1), (1, -1)]
        self.start_pos = list(self.pos)
        self.target_hex = target_hex
        self.progress = 0.0

    def update(self):
        if self.progress < 1.0:
            self.progress += 1.0 / self.jump_duration
            if self.progress >= 1.0:
                self.progress = 1.0
                self.current_hex = self.target_hex
            
            target_pos = self.target_hex.to_pixel()
            # Linear horizontal/vertical interpolation
            self.pos[0] = self.start_pos[0] + (target_pos[0] - self.start_pos[0]) * self.progress
            self.pos[1] = self.start_pos[1] + (target_pos[1] - self.start_pos[1]) * self.progress

    def draw(self, surface):
        # Calculate jump offset (parabola: h * 4 * x * (1-x))
        jump_offset = self.jump_height * 4 * self.progress * (1 - self.progress)
        draw_x = int(self.pos[0])
        draw_y = int(self.pos[1] - jump_offset)

        pygame.draw.circle(surface, (255, 255, 255), (draw_x, draw_y), int(HEX_SIZE * 0.7), 2)

        # Draw sword icon (centered on the character)
        # Blade (top part)
        pygame.draw.line(surface, COLOR_SWORD, (draw_x, draw_y - 15), (draw_x, draw_y + 5), 4)
        # Hilt/Guard
        pygame.draw.line(surface, COLOR_SWORD_HILT, (draw_x - 8, draw_y + 5), (draw_x + 8, draw_y + 5), 3)
        # Handle
        pygame.draw.line(surface, COLOR_SWORD_HILT, (draw_x, draw_y + 5), (draw_x, draw_y + 12), 3)

def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Hex Jump Prototype")
    clock = pygame.time.Clock()

    # Create a grid of tiles (radius-based)
    grid = []
    radius = 4
    for q in range(-radius, radius + 1):
        r1 = max(-radius, -q - radius)
        r2 = min(radius, -q + radius)
        for r in range(r1, r2 + 1):
            grid.append(Tile(Hex(q, r)))

    player = Character(Hex(0, 0))
    font = pygame.font.SysFont(None, 24)
    instructions = font.render("Click on a tile to jump!", True, (200, 200, 200))
    
    running = True
    while running:
        mouse_pos = pygame.mouse.get_pos()
        hovered_hex = Hex.from_pixel(mouse_pos[0], mouse_pos[1])

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if any(t.position == hovered_hex for t in grid):
                    player.jump_to(hovered_hex)

        # Update
        player.update()

        # Draw
        screen.fill(COLOR_BG)
        
        # Draw grid
        for tile in grid:
            center = tile.position.to_pixel()
            corners = get_hex_corners(center)
            if tile.position == hovered_hex:
                color = element_hover_color(tile.element)
            else:
                color = ELEMENT_COLORS[tile.element]
            draw_tile_hex(screen, tile, center, corners, color)

        # Draw player
        player.draw(screen)
        
        # Draw instructions
        screen.blit(instructions, (10, 10))

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()

if __name__ == "__main__":
    main()
