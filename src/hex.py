import math
from config import HEX_SIZE, SCREEN_WIDTH, SCREEN_HEIGHT

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
        return (x, y)

    @staticmethod
    def from_pixel(x, y, camera_x=0, camera_y=0):
        x_adj = x - SCREEN_WIDTH // 2 + camera_x
        y_adj = y - SCREEN_HEIGHT // 2 + camera_y
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