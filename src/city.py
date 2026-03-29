class City:
    def __init__(self, start_hex, tile, color=(255, 255, 255), owner_id=None):
        self.current_hex = start_hex
        self.pos = list(start_hex.to_pixel())
        self.color = color
        self.owner_id = owner_id
        
        if tile:
            tile.element = "light"
            tile.has_city = True
            tile.owner = color

    def update(self):
        pass