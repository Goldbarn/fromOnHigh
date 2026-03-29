class City:
    def __init__(self, start_hex, grid, color=(255, 255, 255)):
        self.current_hex = start_hex
        self.pos = list(start_hex.to_pixel())
        self.color = color
        
        # Turn the tile it is on into a white color (light element)
        for tile in grid:
            if tile.position == self.current_hex:
                tile.element = "light"
                tile.has_city = True
                tile.owner = color
                break

    def update(self):
        pass