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
        self.grid_dict = {}
        radius = 40
        for q in range(-radius, radius + 1):
            r1 = max(-radius, -q - radius)
            r2 = min(radius, -q + radius)
            for r in range(r1, r2 + 1):
                tile = Tile(Hex(q, r))
                self.grid.append(tile)
                self.grid_dict[tile.position] = tile

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

        self.selected_city = None
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
        self.ui_rects = {}
        
        self.toolbar_collapsed = False
        self.text_expanded = False
        self.current_text = ""
        self.god_whisper = ""
        self.whisper_target_player = None
        self.last_ai_failure = None
        self.ai_retry_count = 0
        
        # Set up distinct AI personalities and starting resources
        personalities = [
            "Devoutly Religious, worships the Gods",
            "Rebellious, hates the Gods",
            "Cautious and Paranoid",
            "Aggressive Warlord",
            "Peaceful Scholar",
            "Opportunistic Scavenger"
        ]
        self.player_stats = [{'resources': {e: 0 for e in ELEMENTS}, 'research': 1, 'research_points': 0, 'personality': personalities[i]} for i in range(self.num_players)]

    def handle_events(self):
        screen_width = self.view.screen.get_width()
        screen_height = self.view.screen.get_height()
        mouse_pos = pygame.mouse.get_pos()
        hovered_hex = Hex.from_pixel(mouse_pos[0], mouse_pos[1], self.camera_x, self.camera_y, screen_width, screen_height)
        
        self.hovered_tile = self.grid_dict.get(hovered_hex)

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
                            tile = self.grid_dict.get(self.founder.current_hex)
                            new_city = City(
                                self.founder.current_hex,
                                tile,
                                self.player_colors[self.current_player],
                                self.current_player
                            )
                            self.cities.append(new_city)
                            self._give_founding_resources(self.current_player, new_city)
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
                    if self.ui_rects.get('left_btn') and self.ui_rects['left_btn'].collidepoint(event.pos):
                        self.toolbar_collapsed = not self.toolbar_collapsed
                        continue
                        
                    if self.ui_rects.get('right_btn') and self.ui_rects['right_btn'].collidepoint(event.pos):
                        self.text_expanded = not self.text_expanded
                        continue

                    clicked_toolbar = False
                    if not self.toolbar_collapsed:
                        for i, rect in enumerate(self.ui_rects.get('toolbar', [])):
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
                                self.selected_city = clicked_city
                                if clicked_city.owner_id == self.current_player:
                                    self.instructions_text = f"Player {self.current_player + 1}: A to train army, S to train settler, F to build farm, M to build mine, I to build institute."
                            else:
                                self.selected_city = None
                if event.type == pygame.KEYDOWN:
                    if self.text_expanded:
                        if event.key == pygame.K_RETURN:
                            self.god_whisper = self.current_text
                            self.whisper_target_player = None
                            self.current_text = ""
                            self.text_expanded = False
                        elif event.key == pygame.K_BACKSPACE:
                            self.current_text = self.current_text[:-1]
                        else:
                            self.current_text += event.unicode
                    elif self.selected_city and self.selected_city.owner_id == self.current_player:
                        if event.key == pygame.K_a:
                            self.selected_city = None
                            self._execute_city_decision({"action": "train_army"})
                        elif event.key == pygame.K_s:
                            self.selected_city = None
                            self._execute_city_decision({"action": "train_settler"})
                        elif event.key == pygame.K_f:
                            self.selected_city = None
                            self._execute_city_decision({"action": "build_farm"})
                        elif event.key == pygame.K_i:
                            self.selected_city = None
                            self._execute_city_decision({"action": "build_institute"})
                        elif event.key == pygame.K_m:
                            self.selected_city = None
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
                t = self.grid_dict.get(hx)
                if t: adj_elements.append(t.element)
                        
            stats = self.player_stats[self.current_player]
            wealth = sum(stats['resources'].values())
            
            res_str = ", ".join([f"{v} {k}" for k, v in stats['resources'].items() if v > 0])
            if not res_str:
                res_str = "0 resources"
                
            state = {
                'q': city.current_hex.q,
                'r': city.current_hex.r,
                'resources': res_str,
                'wealth': wealth,
                'research': stats['research'],
                'personality': stats['personality'],
                'surroundings': ", ".join(adj_elements) if adj_elements else "Empty void",
                'last_failure': self.last_ai_failure
            }
            
            if self.god_whisper:
                if self.whisper_target_player is None:
                    self.whisper_target_player = self.current_player
                if self.whisper_target_player == self.current_player:
                    state['god_whisper'] = self.god_whisper
            
            print(f"Asking AI for Player {self.current_player + 1}...")
            decision = self.ai.get_city_decision(state)
            print(f"AI decided: {decision}")
            self.ai_decision = decision
        self.ai_thinking = False

    def _fetch_unit_ai_decision(self, unit):
        print(f"Asking AI for Unit Player {self.current_player + 1}...")
        
        adj_info = []
        dq_dr = [(1, 0), (0, 1), (-1, 1), (-1, 0), (0, -1), (1, -1)]
        occupants = {c.current_hex: f"Player {c.owner_id + 1} city" for c in self.cities}
        occupants.update({u.current_hex: f"Player {u.owner_id + 1} {u.unit_type}" for u in self.units})
        
        for dq, dr in dq_dr:
            hx = Hex(unit.current_hex.q + dq, unit.current_hex.r + dr)
            t = self.grid_dict.get(hx)
            tile_element = t.element if t else "void"
            occupant = occupants.get(hx, "none")
            adj_info.append(f"dir({dq},{dr}): {tile_element}, {occupant}")
            
        other_cities_info = []
        for c in self.cities:
            if c.owner_id != unit.owner_id:
                dq = c.current_hex.q - unit.current_hex.q
                dr = c.current_hex.r - unit.current_hex.r
                other_cities_info.append(f"Player {c.owner_id + 1} city at relative q:{dq}, r:{dr}")
                
        state = {
            'q': unit.current_hex.q,
            'r': unit.current_hex.r,
            'unit_type': unit.unit_type,
            'surroundings': "\n        ".join(adj_info),
            'other_cities': "\n        ".join(other_cities_info) if other_cities_info else "None known",
            'last_failure': self.last_ai_failure
        }
        
        if self.god_whisper:
            if self.whisper_target_player is None:
                self.whisper_target_player = self.current_player
            if self.whisper_target_player == self.current_player:
                state['god_whisper'] = self.god_whisper
        
        decision = self.ai.get_unit_decision(state)
        print(f"AI Unit decided: {decision}")
        self.ai_decision = decision
        self.ai_thinking = False

    def _advance_turn_queue(self, last_action_msg=""):
        self.ai_retry_count = 0
        
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
        success = True
        
        if not city:
            self._advance_turn_queue(msg)
            return
            
        if action == "train_army":
            if stats['resources']['creature'] >= 1 and stats['resources']['stone'] >= 1:
                stats['resources']['creature'] -= 1
                stats['resources']['stone'] -= 1
                creation_level = stats['research']
                self.units.append(Character(city.current_hex, self.player_colors[self.current_player], unit_type="army", owner_id=self.current_player, creation_research_level=creation_level))
                self.audio.play('train')
                msg = f"P{self.current_player + 1} trained an army."
            else:
                self.audio.play('error')
                msg = f"P{self.current_player + 1} failed to train army (insufficient resources)."
                success = False
        elif action == "train_settler":
            if stats['resources']['water'] >= 2 and stats['resources']['earth'] >= 2:
                stats['resources']['water'] -= 2
                stats['resources']['earth'] -= 2
                self.units.append(Character(city.current_hex, self.player_colors[self.current_player], unit_type="settler", owner_id=self.current_player))
                self.audio.play('train')
                msg = f"P{self.current_player + 1} trained a settler."
            else:
                self.audio.play('error')
                msg = f"P{self.current_player + 1} failed to train settler (insufficient resources)."
                success = False
        elif action in ["build_farm", "build_institute", "build_mine"]:
            can_afford = False
            fail_reason = "insufficient resources"
            if action == "build_farm" and stats['resources']['earth'] >= 2:
                can_afford = True
            elif action == "build_mine" and stats['resources']['plant'] >= 2:
                can_afford = True
            elif action == "build_institute":
                num_institutes = sum(1 for t in self.grid if t.building == 'institute' and t.building_owner == self.current_player)
                if num_institutes >= 9:
                    fail_reason = "max 9 reached"
                elif stats['resources']['metal'] >= 2 and stats['resources']['fire'] >= 1:
                    can_afford = True
                
            if can_afford:
                dq_dr = [(1, 0), (0, 1), (-1, 1), (-1, 0), (0, -1), (1, -1)]
                adj = [Hex(city.current_hex.q + dq, city.current_hex.r + dr) for dq, dr in dq_dr]
                valid_tiles = [self.grid_dict[hx] for hx in adj + [city.current_hex] if hx in self.grid_dict and not self.grid_dict[hx].building]
                
                if action == "build_farm":
                    valid_tiles = [t for t in valid_tiles if t.element in ["plant", "creature", "water"]]
                elif action == "build_mine":
                    valid_tiles = [t for t in valid_tiles if t.element != "ice"]
                
                if valid_tiles:
                    if action == "build_farm":
                        stats['resources']['earth'] -= 2
                    elif action == "build_mine":
                        stats['resources']['plant'] -= 2
                    elif action == "build_institute":
                        stats['resources']['metal'] -= 2
                        stats['resources']['fire'] -= 1
                        
                    chosen = random.choice(valid_tiles)
                    chosen.building = action.split('_')[1]
                    chosen.building_owner = self.current_player
                    self.audio.play('build')
                    msg = f"P{self.current_player + 1} built a {chosen.building}."
                else:
                    self.audio.play('error')
                    msg = f"P{self.current_player + 1} failed to build {action.split('_')[1]} (no valid tiles)."
                    success = False
            else:
                self.audio.play('error')
                msg = f"P{self.current_player + 1} failed to build {action.split('_')[1]} ({fail_reason})."
                success = False
        elif action == "trade":
            give_res = decision.get("give")
            if give_res in ELEMENTS:
                if stats['resources'].get(give_res, 0) >= 3:
                    stats['resources'][give_res] -= 3
                    available_res = [e for e in ELEMENTS if e != give_res]
                    get_res = random.choice(available_res)
                    stats['resources'][get_res] += 1
                    self.audio.play('trade')
                    msg = f"P{self.current_player + 1} traded 3 {give_res} for 1 {get_res}."
                else:
                    self.audio.play('error')
                    msg = f"P{self.current_player + 1} failed to trade (insufficient {give_res})."
                    success = False
            else:
                self.audio.play('error')
                msg = f"P{self.current_player + 1} failed to trade (invalid resource)."
                success = False
        elif action == "condense":
            give_res = decision.get("give")
            get_res = decision.get("get")
            if give_res in ["light", "dark"] and get_res in ELEMENTS:
                if stats['resources'].get(give_res, 0) >= 2:
                    stats['resources'][give_res] -= 2
                    stats['resources'][get_res] += 1
                    self.audio.play('trade')
                    msg = f"P{self.current_player + 1} condensed 2 {give_res} for 1 {get_res}."
                else:
                    self.audio.play('error')
                    msg = f"P{self.current_player + 1} failed to condense (insufficient {give_res})."
                    success = False
            else:
                self.audio.play('error')
                msg = f"P{self.current_player + 1} failed to condense (invalid resource)."
                success = False
        elif action == "pray":
            self.audio.play('found_city')
            msg = f"P{self.current_player + 1} prays to the Ascended!"
        elif action == "send_message":
            m = decision.get("message", "We send our regards.")
            if stats['resources']['wind'] > 0:
                stats['resources']['wind'] -= 1
                self.audio.play('move')
                msg = f"P{self.current_player + 1}: '{m}'"
            else:
                self.audio.play('error')
                msg = f"P{self.current_player + 1} lacks wind to send message."
                success = False
        elif action == "do_nothing":
            pass
        else:
            success = False
            msg = f"Invalid action: {action}"
        
        if success:
            self.last_ai_failure = None
            self._advance_turn_queue(msg)
        else:
            self.ai_retry_count += 1
            if self.ai_retry_count >= 3:
                self.last_ai_failure = None
                self._advance_turn_queue(f"{msg} (Turn forfeited)")
            else:
                self.last_ai_failure = f"Attempted '{action}', but failed: {msg}"
                self.instructions_text = f"{msg} (Retry {self.ai_retry_count}/3)"
                self.turn_start_time = pygame.time.get_ticks()

    def _execute_unit_decision(self, unit, decision):
        action = decision.get("action", "do_nothing")
        msg = f"P{self.current_player + 1} unit is idle."
        success = True
        
        if action == "move":
            target = Hex(decision.get("q", unit.current_hex.q), decision.get("r", unit.current_hex.r))
            tile = self.grid_dict.get(target)
            if tile and tile.element not in ["stone", "metal"]:
                if unit.jump_to(target):
                    self.audio.play('move')
                    unit.state = "idle"
                    
                    combat_msg = None
                    if unit.unit_type == 'army':
                        combat_msg = self._check_for_combat(unit)
                    
                    if combat_msg:
                        msg = combat_msg
                    else:
                        msg = f"P{self.current_player + 1} unit moved."
                else:
                    success = False
                    msg = "Move failed: Invalid target distance or already moving."
            else:
                success = False
                msg = "Move failed: Tile is impassable or out of bounds."
        elif action == "guard" and unit.unit_type == "army":
            unit.state = "guarding"
            self.audio.play('build')
            msg = f"P{self.current_player + 1} army is guarding."
        elif action == "settle" and unit.unit_type == "settler":
            if not any(c.current_hex == unit.current_hex for c in self.cities):
                tile = self.grid_dict.get(unit.current_hex)
                new_city = City(unit.current_hex, tile, unit.color, unit.owner_id)
                self.cities.append(new_city)
                self._give_founding_resources(unit.owner_id, new_city)
                if unit in self.units:
                    self.units.remove(unit)
                self.audio.play('found_city')
                msg = f"P{self.current_player + 1} founded a new city."
            else:
                success = False
                msg = "Settle failed: City already exists here."
        elif action == "do_nothing":
            pass
        else:
            success = False
            msg = f"Invalid action: {action}"
        
        if success:
            self.last_ai_failure = None
            self._advance_turn_queue(msg)
        else:
            self.ai_retry_count += 1
            if self.ai_retry_count >= 3:
                self.last_ai_failure = None
                self._advance_turn_queue(f"{msg} (Turn forfeited)")
            else:
                self.last_ai_failure = f"Attempted '{action}', but failed: {msg}"
                self.instructions_text = f"{msg} (Retry {self.ai_retry_count}/3)"
                self.turn_start_time = pygame.time.get_ticks()

    def _check_for_combat(self, moving_army):
        hex_coord = moving_army.current_hex
        # Find other armies on the same tile from different players
        defenders = [u for u in self.units if u.current_hex == hex_coord and u.owner_id != moving_army.owner_id and u is not moving_army and u.unit_type == 'army']
        if defenders:
            defender = defenders[0]
            return self._resolve_combat(moving_army, defender)
        return None

    def _resolve_combat(self, army1, army2):
        level1 = army1.creation_research_level
        level2 = army2.creation_research_level
        delta_L = level1 - level2

        win_prob_army1 = 0.5
        if delta_L == 1:
            win_prob_army1 = 0.7
        elif delta_L >= 2: # Covers 3v1
            win_prob_army1 = 0.95
        elif delta_L == -1:
            win_prob_army1 = 0.3
        elif delta_L <= -2: # Covers 1v3
            win_prob_army1 = 0.05

        roll = random.random()

        if roll < win_prob_army1:
            winner, loser = army1, army2
        else:
            winner, loser = army2, army1
        
        if loser in self.units:
            self.units.remove(loser)
        
        self.audio.play('error')  # A battle sound

        return f"Battle! P{winner.owner_id + 1}'s army (Lvl {winner.creation_research_level}) defeated P{loser.owner_id + 1}'s army (Lvl {loser.creation_research_level})!"

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
        self.ui_rects = self.view.draw_frame(
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
            self.selected_power,
            self.selected_city,
            self.player_stats,
            self.toolbar_collapsed,
            self.text_expanded,
            self.current_text
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

    def get_city_hexes(self, city):
        return [
            city.current_hex,
            Hex(city.current_hex.q + 1, city.current_hex.r),
            Hex(city.current_hex.q + 1, city.current_hex.r - 1),
            Hex(city.current_hex.q, city.current_hex.r - 1),
            Hex(city.current_hex.q - 1, city.current_hex.r),
            Hex(city.current_hex.q - 1, city.current_hex.r + 1),
            Hex(city.current_hex.q, city.current_hex.r + 1),
        ]

    def _give_founding_resources(self, player_id, city):
        stats = self.player_stats[player_id]
        for hx in self.get_city_hexes(city):
            tile = self.grid_dict.get(hx)
            if tile:
                stats['resources'][tile.element] += 2

    def next_player(self, last_action_msg=""):
        if self.whisper_target_player is not None and self.whisper_target_player == self.current_player:
            self.god_whisper = ""
            self.whisper_target_player = None
            
        self.current_player = (self.current_player + 1) % self.num_players
        
        # CITY CAPTURE LOGIC for the NEW current player
        captured_cities_msgs = []
        armies_of_new_player = [u for u in self.units if u.owner_id == self.current_player and u.unit_type == 'army']
        for unit in armies_of_new_player:
            city_on_tile = self.get_city_at_hex(unit.current_hex)
            if city_on_tile and city_on_tile.owner_id != self.current_player:
                original_owner = city_on_tile.owner_id
                city_on_tile.owner_id = self.current_player
                city_on_tile.color = self.player_colors[self.current_player]
                # Update the city center tile's owner color
                tile = self.grid_dict.get(city_on_tile.current_hex)
                if tile:
                    tile.owner = city_on_tile.color
                captured_cities_msgs.append(f"P{self.current_player + 1} captured a city from P{original_owner + 1}!")
                self.audio.play('found_city')  # Capture sound
        
        
        # Research point accumulation
        stats = self.player_stats[self.current_player]
        num_institutes = sum(1 for t in self.grid if t.building == 'institute' and t.building_owner == self.current_player)
        stats['research_points'] += num_institutes
        if stats['research_points'] >= 3 and stats['research'] < 3:
            stats['research'] += 1
            stats['research_points'] -= 3
            captured_cities_msgs.append(f"P{self.current_player + 1} reached Research Level {stats['research']}!")
            self.audio.play('found_city') # Level up sound
        
        # Resource collection
        stats = self.player_stats[self.current_player]
        
        # 1. City bounds resources (plant, creature, water)
        for city in self.get_player_cities(self.current_player):
            for hx in self.get_city_hexes(city):
                tile = self.grid_dict.get(hx)
                if tile and tile.element in ["plant", "creature", "water"]:
                    stats['resources'][tile.element] += 1

        # 2. Mine and farm resources
        for t in self.grid:
            if t.building_owner == self.current_player:
                if t.building in ["farm", "mine"]:
                    stats['resources'][t.element] += 1
                    
        # 3. Upkeep
        units_to_remove = []
        for u in self.units:
            if u.owner_id == self.current_player:
                if stats['resources']['water'] > 0:
                    stats['resources']['water'] -= 1
                elif stats['resources']['plant'] > 0:
                    stats['resources']['plant'] -= 1
                elif stats['resources']['creature'] > 0:
                    stats['resources']['creature'] -= 1
                else:
                    units_to_remove.append(u)
                    
        for u in units_to_remove:
            self.units.remove(u)

        self.turn_start_time = pygame.time.get_ticks()
        self.turn_queue = ["CITY"] + [u for u in self.units if u.owner_id == self.current_player]
        self.current_action_entity = self.turn_queue.pop(0) if self.turn_queue else "CITY"
        self.ai_retry_count = 0
        
        base_msg = f"Player {self.current_player + 1}'s turn."
        
        if captured_cities_msgs:
            capture_summary = " ".join(captured_cities_msgs)
            if last_action_msg:
                last_action_msg = f"{last_action_msg} {capture_summary}"
            else:
                last_action_msg = capture_summary

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