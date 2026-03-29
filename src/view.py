import pygame
import math
from config import HEX_SIZE, COLOR_BG, COLOR_SWORD, COLOR_SWORD_HILT, ELEMENT_COLORS
from hex import Hex

class View:
    def __init__(self, screen, font):
        self.screen = screen
        self.font = font

    def get_hex_corners(self, center):
        corners = []
        for i in range(6):
            angle_deg = 60 * i
            angle_rad = math.pi / 180 * angle_deg
            corners.append((center[0] + HEX_SIZE * math.cos(angle_rad),
                            center[1] + HEX_SIZE * math.sin(angle_rad)))
        return corners

    def element_hover_color(self, element):
        r, g, b = ELEMENT_COLORS[element]
        return (min(255, r + 45), min(255, g + 45), min(255, b + 45))

    def draw_tile_hex(self, tile, center, corners, base_color):
        cx, cy = center
        cx, cy = float(cx), float(cy)

        elem = tile.element
        outline_w = 2

        pygame.draw.polygon(self.screen, base_color, corners)

        if elem in ["fire", "lightning"]:
            pygame.draw.circle(self.screen, (255, 140, 0), (int(cx), int(cy)), int(HEX_SIZE * 0.2))

        # Impassable: two small lines only (stone/metal blocked in controller)
        if elem in ("stone", "metal"):
            d = int(HEX_SIZE * 0.18)
            px, py = int(cx), int(cy)
            c = (255, 210, 90) if elem == "stone" else (85, 45, 50)
            pygame.draw.line(self.screen, c, (px - d, py - d), (px + d, py + d), 2)
            pygame.draw.line(self.screen, c, (px + d, py - d), (px - d, py + d), 2)

        if tile.building:
            bx, by = int(cx), int(cy)
            size = int(HEX_SIZE * 0.4)
            rect = pygame.Rect(bx - size//2, by - size//2, size, size)
            if tile.building == "farm":
                pygame.draw.rect(self.screen, (34, 139, 34), rect) # Forest Green
            elif tile.building == "mine":
                pygame.draw.rect(self.screen, (105, 105, 105), rect) # Dim Gray
            elif tile.building == "institute":
                pygame.draw.rect(self.screen, (65, 105, 225), rect) # Royal Blue
            pygame.draw.rect(self.screen, (0, 0, 0), rect, 2)

        pygame.draw.polygon(self.screen, (0, 0, 0), corners, outline_w)

    def draw_character(self, character, camera_x, camera_y):
        screen_width = self.screen.get_width()
        screen_height = self.screen.get_height()
        jump_offset = character.jump_height * 4 * character.progress * (1 - character.progress)
        draw_x = int(character.pos[0] - camera_x + screen_width // 2)
        draw_y = int(character.pos[1] - jump_offset - camera_y + screen_height // 2)

        if character.unit_type == "army":
            points = [(draw_x, draw_y - 15), (draw_x - 12, draw_y + 10), (draw_x + 12, draw_y + 10)]
            pygame.draw.polygon(self.screen, character.color, points)
            pygame.draw.polygon(self.screen, (0, 0, 0), points, 2)
            if character.state == "guarding":
                pygame.draw.circle(self.screen, (200, 200, 200), (draw_x, draw_y), 20, 2)
        elif character.unit_type == "settler":
            points = [(draw_x - 12, draw_y - 10), (draw_x + 12, draw_y - 10), (draw_x, draw_y + 15)]
            pygame.draw.polygon(self.screen, character.color, points)
            pygame.draw.polygon(self.screen, (0, 0, 0), points, 2)
        else:
            pygame.draw.circle(self.screen, character.color, (draw_x, draw_y), int(HEX_SIZE * 0.7), 2)
            pygame.draw.line(self.screen, COLOR_SWORD, (draw_x, draw_y - 15), (draw_x, draw_y + 5), 4)
            pygame.draw.line(self.screen, COLOR_SWORD_HILT, (draw_x - 8, draw_y + 5), (draw_x + 8, draw_y + 5), 3)
            pygame.draw.line(self.screen, COLOR_SWORD_HILT, (draw_x, draw_y + 5), (draw_x, draw_y + 12), 3)

    def draw_city(self, city, camera_x, camera_y):
        screen_width = self.screen.get_width()
        screen_height = self.screen.get_height()
        draw_x = int(city.pos[0] - camera_x + screen_width // 2)
        draw_y = int(city.pos[1] - camera_y + screen_height // 2)

        border_hexes = [
            city.current_hex,
            Hex(city.current_hex.q + 1, city.current_hex.r),
            Hex(city.current_hex.q + 1, city.current_hex.r - 1),
            Hex(city.current_hex.q, city.current_hex.r - 1),
            Hex(city.current_hex.q - 1, city.current_hex.r),
            Hex(city.current_hex.q - 1, city.current_hex.r + 1),
            Hex(city.current_hex.q, city.current_hex.r + 1),
        ]
        
        edges = {}
        for bh in border_hexes:
            world_center = bh.to_pixel()
            screen_center = (world_center[0] - camera_x + screen_width // 2, 
                             world_center[1] - camera_y + screen_height // 2)
            corners = self.get_hex_corners(screen_center)
            for i in range(6):
                p1 = corners[i]
                p2 = corners[(i + 1) % 6]
                rp1 = (int(round(p1[0])), int(round(p1[1])))
                rp2 = (int(round(p2[0])), int(round(p2[1])))
                edge = tuple(sorted((rp1, rp2)))
                edges[edge] = edges.get(edge, 0) + 1
        
        for edge, count in edges.items():
            if count == 1:
                pygame.draw.line(self.screen, city.color, edge[0], edge[1], 4)

        pygame.draw.rect(self.screen, (200, 200, 200), (draw_x - 12, draw_y - 2, 24, 16))
        pygame.draw.rect(self.screen, (139, 69, 19), (draw_x - 4, draw_y + 6, 8, 8))
        pygame.draw.polygon(self.screen, (150, 50, 50), [
            (draw_x - 16, draw_y - 2), 
            (draw_x + 16, draw_y - 2), 
            (draw_x, draw_y - 18)
        ])

    def draw_instructions(self, text):
        instructions = self.font.render(text, True, (200, 200, 200))
        # Set the text position slightly shifted to allow for padding
        text_rect = instructions.get_rect(topleft=(15, 15))
        
        # Create a padded background rectangle
        bg_rect = text_rect.inflate(10, 10) # 5 pixels of padding on all sides
        pygame.draw.rect(self.screen, (20, 20, 20), bg_rect) # Dark gray background
        pygame.draw.rect(self.screen, (100, 100, 100), bg_rect, 2) # Lighter border
        
        self.screen.blit(instructions, text_rect)

    def draw_toolbar(self, powers, selected_power):
        screen_width = self.screen.get_width()
        screen_height = self.screen.get_height()
        rects = []
        spacing = 50
        box_size = 36
        start_x = screen_width // 2 - (len(powers) * spacing) // 2
        start_y = screen_height - 60
        
        # Toolbar background
        bg_rect = pygame.Rect(start_x - 10, start_y - 10, len(powers) * spacing + 10, 60)
        pygame.draw.rect(self.screen, (30, 30, 30), bg_rect, border_radius=8)
        pygame.draw.rect(self.screen, (100, 100, 100), bg_rect, 2, border_radius=8)
        
        for i, power in enumerate(powers):
            rect = pygame.Rect(start_x + i * spacing, start_y, box_size, box_size)
            color = ELEMENT_COLORS.get(power, (255, 255, 255))
            
            if power == selected_power:
                pygame.draw.rect(self.screen, (255, 215, 0), rect.inflate(8, 8), 4, border_radius=5) # Gold highlight
                
            pygame.draw.rect(self.screen, color, rect, border_radius=5)
            pygame.draw.rect(self.screen, (0, 0, 0), rect, 2, border_radius=5)
            
            initial = self.font.render(power[0].upper(), True, (10, 10, 10) if sum(color)>300 else (240, 240, 240))
            self.screen.blit(initial, initial.get_rect(center=rect.center))
            rects.append(rect)
        return rects

    def draw_frame(self, grid, cities, founder, units, camera_x, camera_y, hovered_tile, instructions_text, game_state="SETUP", god_powers=None, selected_power=None):
        screen_width = self.screen.get_width()
        screen_height = self.screen.get_height()
        self.screen.fill(COLOR_BG)
        
        for tile in grid:
            world_center = tile.position.to_pixel()
            
            screen_x = world_center[0] - camera_x + screen_width // 2
            screen_y = world_center[1] - camera_y + screen_height // 2
            if (screen_x + HEX_SIZE < 0 or screen_x - HEX_SIZE > screen_width or
                screen_y + HEX_SIZE < 0 or screen_y - HEX_SIZE > screen_height):
                continue

            corners = self.get_hex_corners((screen_x, screen_y))
            if tile == hovered_tile:
                color = self.element_hover_color(tile.element)
            else:
                color = ELEMENT_COLORS[tile.element]
            self.draw_tile_hex(tile, (screen_x, screen_y), corners, color)

        for city in cities:
            self.draw_city(city, camera_x, camera_y)
        for unit in units:
            self.draw_character(unit, camera_x, camera_y)
        if founder:
            self.draw_character(founder, camera_x, camera_y)
        
        self.draw_instructions(instructions_text)
        
        toolbar_rects = []
        if game_state == "PLAY" and god_powers:
            toolbar_rects = self.draw_toolbar(god_powers, selected_power)
            
        pygame.display.flip()
        return toolbar_rects