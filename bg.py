import pygame
import random

class BG:
    def __init__(self, 
                 seed=None, 
                 /, 
                 max_red_diff=30
            ):
        if seed is not None:
            random.seed(seed)
        type = random.randint(0, 2)
        if type == 0:
            diff = random.randint(20, 120)
            diff2 = random.randint(0, diff)
            self.base = (diff2, diff-diff2, 255-diff)
        elif type >= 1:
            blu = random.randint(0, 100)
            diff = random.randint(0, blu)
            self.base = (diff, blu-diff, blu)
        
        if self.base[0] + max_red_diff >= self.base[2]:
            self.base = (max(self.base[2]-max_red_diff, 0), self.base[1], self.base[2])
    
    def __call__(self, WIN):
        WIN.fill(self.base)

if __name__ == '__main__':
    pygame.init()
    win = pygame.display.set_mode((500, 500))
    bg = BG()
    run = True
    while run:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                run = False
            elif ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    run = False
                elif ev.key == pygame.K_SPACE:
                    bg = BG()
        
        bg(win)
        pygame.display.flip()
