import pygame
import threading
import random
from config import FPS, ELEMENTS
from hex import Hex
from tile import Tile
from character import Character
from city import City
from utils import get_random_passable_hex
from audio import AudioManager
from ai import AIPlayer

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

        self.selected_city = False
        self.current_player = 0
        self.founder = Character(get_random_passable_hex(self.grid), self.player_colors[self.current_player], unit_type="founder", owner_id=self.current_player)
        
        self.units = []
        self.turn_queue = []
        self.current_action_entity = "CITY"
        self.instructions_text = f"Player {self.current_player + 1}'s turn. Click to move, Enter to found City."
        self.camera_x, self.camera_y = 0.0, 0.0
        self.hovered_tile = None
        self.audio = AudioManager()
        
        self.ai = AIPlayer()
        self.ai_thinking = False
        self.ai_decision = None
        
        self.turn_start_time = 0
        self.god_powers = list(ELEMENTS)
        self.selected_power = None
        self.toolbar_rects = []
        
        # Set up distinct AI personalities and starting resources
        personalities = [
            "Devoutly Religious, worships the Gods",
            "Rebellious, hates the Gods",
            "Cautious and Paranoid",
            "Aggressive Warlord",
            "Peaceful Scholar",
            "Opportunistic Scavenger"
        ]
        self.player_stats = [{'resources': {e: 0 for e in ELEMENTS}, 'food': 5, 'wind': 1, 'research': 1, 'personality': personalities[i]} for i in range(self.num_players)]

    def handle_events(self):
        screen_width = self.view.screen.get_width()
        screen_height = self.view.screen.get_height()
        mouse_pos = pygame.mouse.get_pos()
        hovered_hex = Hex.from_pixel(mouse_pos[0], mouse_pos[1], self.camera_x, self.camera_y, screen_width, screen_height)
        
        self.hovered_tile = None
        for t in self.grid:
            if t.position == hovered_hex:
                self.hovered_tile = t
                break

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif self.game_state == "SETUP" and self.founder:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if self.hovered_tile and self.hovered_tile.element not in ["stone", "metal"]:
                        if self.founder.jump_to(hovered_hex):
                            self.audio.play('move')
                        else:
                            self.audio.play('error') # Clicked a valid tile, but it's too far away
                    else:
                        self.audio.play('error') # Clicked impassable tile or off-grid
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        if not any(city.current_hex == self.founder.current_hex for city in self.cities):
                            self.cities.append(City(
                                self.founder.current_hex,
                                self.grid,
                                self.player_colors[self.current_player],
                                self.current_player
                            ))
                            self.audio.play('found_city')
                            self.current_player += 1
                            if self.current_player < self.num_players:
                                self.founder = Character(get_random_passable_hex(self.grid), self.player_colors[self.current_player], unit_type="founder", owner_id=self.current_player)
                                self.instructions_text = f"Player {self.current_player + 1}'s turn. Click to move, Enter to found City."
                            else:
                                self.founder = None
                                self.game_state = "PLAY"
                                self.current_player = 0
                                self.turn_start_time = pygame.time.get_ticks()
                                self.turn_queue = ["CITY"] + [u for u in self.units if u.owner_id == self.current_player]
                                self.current_action_entity = self.turn_queue.pop(0) if self.turn_queue else "CITY"
                                self.instructions_text = f"Player {self.current_player + 1}'s turn. Main game phase."
                                self.center_camera_on_current_player_city()
            elif self.game_state == "PLAY":
                if event.type == pygame.MOUSEMOTION:
                    if self.hovered_tile:
                        self.instructions_text = f"Hovering {self.hovered_tile.element} tile at ({hovered_hex.q}, {hovered_hex.r})"
                if event.type == pygame.MOUSEBUTTONDOWN:
                    clicked_toolbar = False
                    for i, rect in enumerate(self.toolbar_rects):
                        if rect.collidepoint(event.pos):
                            if self.selected_power == self.god_powers[i]:
                                self.selected_power = None
                            else:
                                self.selected_power = self.god_powers[i]
                            clicked_toolbar = True
                            break
                    
                    if not clicked_toolbar:
                        if self.selected_power and self.hovered_tile:
                            # Prevent trapping units in impassable terrain
                            units_on_tile = [u for u in self.units if u.current_hex == hovered_hex]
                            if self.founder and self.founder.current_hex == hovered_hex:
                                units_on_tile.append(self.founder)
                            
                            if self.selected_power in ["stone", "metal"] and units_on_tile:
                                self.audio.play('error')
                            else:
                                self.hovered_tile.element = self.selected_power
                                if self.selected_power in ["lightning", "fire", "dark"]: self.audio.play('error')
                                elif self.selected_power in ["light", "plant", "water"]: self.audio.play('found_city')
                                else: self.audio.play('move')
                        else:
                            clicked_city = self.get_city_at_hex(hovered_hex)
                            if clicked_city:
                                if clicked_city.owner_id == self.current_player:
                                    self.selected_city = True
                                    self.instructions_text = f"Player {self.current_player + 1}: A to train army, S to train settler, F to build farm, M to build mine, I to build institute."
                if event.type == pygame.KEYDOWN:
                    if self.selected_city:
                        if event.key == pygame.K_a:
                            self.selected_city = False
                            self._execute_city_decision({"action": "train_army"})
                        elif event.key == pygame.K_s:
                            self.selected_city = False
                            self._execute_city_decision({"action": "train_settler"})
                        elif event.key == pygame.K_f:
                            self.selected_city = False
                            self._execute_city_decision({"action": "build_farm"})
                        elif event.key == pygame.K_i:
                            self.selected_city = False
                            self._execute_city_decision({"action": "build_institute"})
                        elif event.key == pygame.K_m:
                            self.selected_city = False
                            self._execute_city_decision({"action": "build_mine"})


    def _fetch_ai_decision(self):
        print(f"Asking AI for Player {self.current_player + 1}...")
        decision = self.ai.get_decision(self.founder.current_hex, self.grid)
        print(f"AI decided: {decision}")
        self.ai_decision = decision
        self.ai_thinking = False

    def _fetch_play_ai_decision(self):
        city = self.get_current_player_city()
        if city:
            # Look at adjacent tiles to tell the AI what is around them
            adj_elements = []
            dq_dr = [(1, 0), (0, 1), (-1, 1), (-1, 0), (0, -1), (1, -1)]
            for dq, dr in dq_dr:
                hx = Hex(city.current_hex.q + dq, city.current_hex.r + dr)
                for t in self.grid:
                    if t.position == hx:
                        adj_elements.append(t.element)
                        break
                        
            stats = self.player_stats[self.current_player]
            state = {
                'q': city.current_hex.q,
                'r': city.current_hex.r,
                'food': stats['food'],
                'wind': stats['wind'],
                'research': stats['research'],
                'personality': stats['personality'],
                'surroundings': ", ".join(adj_elements) if adj_elements else "Empty void"
            }
            
            print(f"Asking AI for Player {self.current_player + 1}...")
            decision = self.ai.get_city_decision(state)
            print(f"AI decided: {decision}")
            self.ai_decision = decision
        self.ai_thinking = False

    def _fetch_unit_ai_decision(self, unit):
        print(f"Asking AI for Unit Player {self.current_player + 1}...")
        decision = self.ai.get_unit_decision(unit, self.grid)
        print(f"AI Unit decided: {decision}")
        self.ai_decision = decision
        self.ai_thinking = False

    def _advance_turn_queue(self, last_action_msg=""):
        if last_action_msg:
            self.instructions_text = last_action_msg
            
        if self.turn_queue:
            self.current_action_entity = self.turn_queue.pop(0)
            self.turn_start_time = pygame.time.get_ticks()
        else:
            self.next_player(last_action_msg)

    def _execute_city_decision(self, decision):
        action = decision.get("action", "do_nothing")
        stats = self.player_stats[self.current_player]
        city = self.get_current_player_city()
        msg = f"P{self.current_player + 1} city is idle."
        
        if not city:
            self._advance_turn_queue(msg)
            return
            
        if action == "train_army":
            self.units.append(Character(city.current_hex, self.player_colors[self.current_player], unit_type="army", owner_id=self.current_player))
            self.audio.play('train')
            msg = f"P{self.current_player + 1} trained an army."
        elif action == "train_settler":
            self.units.append(Character(city.current_hex, self.player_colors[self.current_player], unit_type="settler", owner_id=self.current_player))
            self.audio.play('train')
            msg = f"P{self.current_player + 1} trained a settler."
        elif action in ["build_farm", "build_institute", "build_mine"]:
            dq_dr = [(1, 0), (0, 1), (-1, 1), (-1, 0), (0, -1), (1, -1)]
            adj = [Hex(city.current_hex.q + dq, city.current_hex.r + dr) for dq, dr in dq_dr]
            valid_tiles = [t for t in self.grid if t.position in adj + [city.current_hex] and not t.building]
            
            if action == "build_farm":
                valid_tiles = [t for t in valid_tiles if t.element in ["plant", "creature", "water"]]
            elif action == "build_mine":
                valid_tiles = [t for t in valid_tiles if t.element != "ice"]
            
            if valid_tiles:
                chosen = random.choice(valid_tiles)
                chosen.building = action.split('_')[1]
                chosen.building_owner = self.current_player
                self.audio.play('build')
                msg = f"P{self.current_player + 1} built a {chosen.building}."
            else:
                self.audio.play('error')
                msg = f"P{self.current_player + 1} failed to build {action.split('_')[1]}."
        elif action == "pray":
            self.audio.play('found_city')
            msg = f"P{self.current_player + 1} prays to the Ascended!"
        elif action == "send_message":
            m = decision.get("message", "We send our regards.")
            if stats['wind'] > 0:
                stats['wind'] -= 1
                self.audio.play('move')
                msg = f"P{self.current_player + 1}: '{m}'"
        
        self._advance_turn_queue(msg)

    def _execute_unit_decision(self, unit, decision):
        action = decision.get("action", "do_nothing")
        msg = f"P{self.current_player + 1} unit is idle."
        
        if action == "move":
            target = Hex(decision.get("q", unit.current_hex.q), decision.get("r", unit.current_hex.r))
            tile = next((t for t in self.grid if t.position == target), None)
            if tile and tile.element not in ["stone", "metal"]:
                if unit.jump_to(target):
                    self.audio.play('move')
                    msg = f"P{self.current_player + 1} unit moved."
                    unit.state = "idle"
        elif action == "guard" and unit.unit_type == "army":
            unit.state = "guarding"
            self.audio.play('build')
            msg = f"P{self.current_player + 1} army is guarding."
        elif action == "settle" and unit.unit_type == "settler":
            if not any(c.current_hex == unit.current_hex for c in self.cities):
                self.cities.append(City(unit.current_hex, self.grid, unit.color, unit.owner_id))
                if unit in self.units:
                    self.units.remove(unit)
                self.audio.play('found_city')
                msg = f"P{self.current_player + 1} founded a new city."
        
        self._advance_turn_queue(msg)

    def update(self):
        if self.founder:
            self.founder.update()
            self.camera_x = self.founder.pos[0]
            self.camera_y = self.founder.pos[1]
            
        for city in self.cities:
            city.update()
            
        for unit in self.units:
            unit.update()
            
        # AI Auto-Play for the main game loop
        if self.game_state == "PLAY":
            if not self.ai_thinking and self.ai_decision is None:
                time_since_turn = pygame.time.get_ticks() - self.turn_start_time
                if time_since_turn < 1500:
                    pass # Keep current text
                elif time_since_turn < 3000:
                    if self.current_action_entity == "CITY":
                        self.instructions_text = f"Player {self.current_player + 1} is deciding what to produce..."
                    else:
                        self.instructions_text = f"Player {self.current_player + 1} unit is awaiting orders..."
                else:
                    self.ai_thinking = True
                    if self.current_action_entity == "CITY":
                        threading.Thread(target=self._fetch_play_ai_decision, daemon=True).start()
                    else:
                        threading.Thread(target=self._fetch_unit_ai_decision, args=(self.current_action_entity,), daemon=True).start()
                
            if self.ai_decision is not None:
                decision = self.ai_decision
                self.ai_decision = None # Reset
                
                if self.current_action_entity == "CITY":
                    self._execute_city_decision(decision)
                else:
                    self._execute_unit_decision(self.current_action_entity, decision)

    def draw(self):
        self.toolbar_rects = self.view.draw_frame(
            self.grid, 
            self.cities, 
            self.founder, 
            self.units,
            self.camera_x, 
            self.camera_y, 
            self.hovered_tile, 
            self.instructions_text,
            self.game_state,
            self.god_powers,
            self.selected_power
        )

    def get_player_cities(self, player_index):
        return [city for city in self.cities if city.owner_id == player_index]

    def get_current_player_cities(self):
        return self.get_player_cities(self.current_player)

    def get_city_at_hex(self, hex_coord):
        return next((city for city in self.cities if city.current_hex == hex_coord), None)

    def get_current_player_city(self):
        cities = self.get_current_player_cities()
        return cities[0] if cities else None

    def center_camera_on_current_player_city(self):
        city = self.get_current_player_city()
        if city:
            self.camera_x, self.camera_y = city.pos

    def next_player(self, last_action_msg=""):
        self.current_player = (self.current_player + 1) % self.num_players
        
        # Resource collection
        stats = self.player_stats[self.current_player]
        for t in self.grid:
            if t.building_owner == self.current_player:
                if t.building == "farm" and t.element in ["plant", "creature", "water"]:
                    stats['resources'][t.element] += 2
                elif t.building == "mine" and t.element != "ice":
                    stats['resources'][t.element] += 1
        
        self.turn_start_time = pygame.time.get_ticks()
        self.turn_queue = ["CITY"] + [u for u in self.units if u.owner_id == self.current_player]
        self.current_action_entity = self.turn_queue.pop(0) if self.turn_queue else "CITY"
        
        base_msg = f"Player {self.current_player + 1}'s turn."
        if last_action_msg:
            self.instructions_text = f"{last_action_msg} {base_msg}"
        else:
            self.instructions_text = base_msg
        self.center_camera_on_current_player_city()

    def run(self):
        clock = pygame.time.Clock()
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            clock.tick(FPS)