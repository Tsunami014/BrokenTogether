import pygame
import random
import math

class BG:
    def __init__(self, 
                 seed=None, 
                 /, 
                 max_red_diff=30
            ):
        self.cache = {}
        state = random.getstate()
        self.seed = seed
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

        random.setstate(state)
    
    def _genStar(self):
        col = (random.randint(200, 255), random.randint(200, 255), random.randint(200, 255))
        sze = (random.randint(1, 3), random.randint(1, 3))
        sur = pygame.Surface(sze, pygame.SRCALPHA)
        hx, hy = math.floor(sze[0]/2) or 1, math.floor(sze[1]/2) or 1
        for x in range(sze[0]):
            for y in range(sze[1]):
                alpha = 255-((abs(x-hx)/hx*125)+(abs(y-hy)/hy*125))
                alpha += random.randint(-20, 20)
                sur.set_at((x, y), (*col, max(min(alpha, 255), 0)))
        return sur
    
    def _gen(self, sze, x, y, z):
        sur = pygame.Surface(sze)
        sur.fill(self.base)
        if self.seed is not None:
            random.seed(self.seed)
        
        totPxs = sze[0]*sze[1]
        stars = random.sample(range(totPxs), random.randint(totPxs//100, totPxs//50))
        for st in stars:
            x, y = st%sze[0], math.floor(st/sze[0])
            stSur = self._genStar()
            sur.blit(stSur, (x-2, y-2))
        return sur
    
    def __call__(self, sze, x, y, z):
        check = hash((sze, x, y, z))
        if check in self.cache:
            return self.cache[check]
        state = random.getstate()
        sur = self._gen(sze, x, y, z)
        random.setstate(state)
        self.cache[check] = sur
        return sur

if __name__ == '__main__':
    pygame.init()
    win = pygame.display.set_mode((500, 500), pygame.RESIZABLE)
    x, y, z = 0, 0, 0
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
        
        keys = pygame.key.get_pressed()
        if keys[pygame.K_UP]:
            y -= 1
        elif keys[pygame.K_DOWN]:
            y += 1
        if keys[pygame.K_LEFT]:
            x -= 1
        elif keys[pygame.K_RIGHT]:
            x += 1
        if keys[pygame.K_COMMA]:
            z -= 1
        elif keys[pygame.K_PERIOD]:
            z += 1
        
        win.blit(bg(win.get_size(), x, y, z), (0, 0))
        pygame.display.flip()
