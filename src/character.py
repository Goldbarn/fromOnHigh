class Character:
    def __init__(self, start_hex, color=(255, 255, 255)):
        self.current_hex = start_hex
        self.target_hex = start_hex
        self.pos = list(start_hex.to_pixel())
        self.start_pos = list(start_hex.to_pixel())
        self.progress = 1.0 # 0.0 to 1.0 during jump
        self.jump_duration = 15 # frames
        self.jump_height = 40
        self.color = color

    def jump_to(self, target_hex):
        if self.current_hex != target_hex and self.progress >= 1.0 and self.is_adjacent(target_hex):
            self.start_pos = list(self.pos)
            self.target_hex = target_hex
            self.progress = 0.0
            return True
        return False

    def is_adjacent(self, target_hex):
        dq = self.current_hex.q - target_hex.q
        dr = self.current_hex.r - target_hex.r
        return (dq, dr) in [(1, 0), (0, 1), (-1, 1), (-1, 0), (0, -1), (1, -1)]

    def update(self):
        if self.progress < 1.0:
            self.progress += 1.0 / self.jump_duration
            if self.progress >= 1.0:
                self.progress = 1.0
                self.current_hex = self.target_hex
            
            target_pos = self.target_hex.to_pixel()
            self.pos[0] = self.start_pos[0] + (target_pos[0] - self.start_pos[0]) * self.progress
            self.pos[1] = self.start_pos[1] + (target_pos[1] - self.start_pos[1]) * self.progress