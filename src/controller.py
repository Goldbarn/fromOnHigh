import pygame
from config import FPS
from hex import Hex
from tile import Tile
from character import Character
from city import City
from utils import get_random_passable_hex
from audio import AudioManager

class Controller:
    def __init__(self, view):
        self.view = view
        self.running = True

        self.grid = []
        radius = 40
        for q in range(-radius, radius + 1):
            r1 = max(-radius, -q - radius)
            r2 = min(radius, -q + radius)
            for r in range(r1, r2 + 1):
                self.grid.append(Tile(Hex(q, r)))

        self.game_state = "SETUP"
        self.cities = []
        self.num_players = 6
        self.player_colors = [
            (255, 50, 50),
            (50, 50, 255),
            (50, 255, 50),
            (255, 255, 50),
            (255, 50, 255),
            (50, 255, 255)
        ]
        self.current_player = 0
        self.founder = Character(get_random_passable_hex(self.grid), self.player_colors[self.current_player])
        self.instructions_text = f"Player {self.current_player + 1}'s turn. Click to move, Enter to found City."
        self.camera_x, self.camera_y = 0.0, 0.0
        self.hovered_tile = None
        self.audio = AudioManager()

    def handle_events(self):
        mouse_pos = pygame.mouse.get_pos()
        hovered_hex = Hex.from_pixel(mouse_pos[0], mouse_pos[1], self.camera_x, self.camera_y)
        
        self.hovered_tile = None
        for t in self.grid:
            if t.position == hovered_hex:
                self.hovered_tile = t
                break

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if self.game_state == "SETUP" and self.founder:
                    if self.hovered_tile and self.hovered_tile.element not in ["stone", "metal"]:
                        if self.founder.jump_to(hovered_hex):
                            self.audio.play('move')
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    if self.game_state == "SETUP" and self.founder:
                        if not any(city.current_hex == self.founder.current_hex for city in self.cities):
                            self.cities.append(City(self.founder.current_hex, self.grid, self.player_colors[self.current_player]))
                            self.audio.play('found_city')
                            self.current_player += 1
                            if self.current_player < self.num_players:
                                self.founder = Character(get_random_passable_hex(self.grid), self.player_colors[self.current_player])
                                self.instructions_text = f"Player {self.current_player + 1}'s turn. Click to move, Enter to found City."
                            else:
                                self.founder = None
                                self.game_state = "PLAY"
                                self.instructions_text = "All cities founded! Main game phase."

    def update(self):
        if self.founder:
            self.founder.update()
            self.camera_x = self.founder.pos[0]
            self.camera_y = self.founder.pos[1]
        for city in self.cities:
            city.update()

    def draw(self):
        self.view.draw_frame(
            self.grid, 
            self.cities, 
            self.founder, 
            self.camera_x, 
            self.camera_y, 
            self.hovered_tile, 
            self.instructions_text
        )

    def run(self):
        clock = pygame.time.Clock()
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            clock.tick(FPS)