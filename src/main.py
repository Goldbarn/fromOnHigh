import pygame
from config import SCREEN_WIDTH, SCREEN_HEIGHT
from view import View
from controller import Controller

def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE)
    pygame.display.set_caption("From On High")
    font = pygame.font.SysFont(None, 24)
    
    view = View(screen, font)
    controller = Controller(view)
    
    controller.run()
    pygame.quit()

if __name__ == "__main__":
    main()
