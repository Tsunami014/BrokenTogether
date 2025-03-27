import numpy as np
import pygame
import random
import math
import sys

class Stars:
    def __init__(self, rng):
        self.STARS = []
        self.rng = rng
    
    def __call__(self, typ):
        try:
            return self.STARS[typ]
        except IndexError:
            self.STARS += [self._genStar() for _ in range(typ-len(self.STARS)+1)]
        return self.STARS[typ]
    
    def _genStar(self):
        col = (self.rng.randint(200, 255), self.rng.randint(200, 255), self.rng.randint(200, 255))
        sze = (self.rng.randint(0, 3), self.rng.randint(0, 3))
        sur = pygame.Surface(sze, pygame.SRCALPHA)
        hx, hy = math.floor(sze[0]/2) or 1, math.floor(sze[1]/2) or 1
        for x in range(sze[0]):
            for y in range(sze[1]):
                alpha = 255 - ((abs(x-hx)/hx*125) + (abs(y-hy)/hy*125))
                alpha += self.rng.randint(-50, 50)
                sur.set_at((x, y), (*col, max(min(alpha, 255), 0)))
        return sur

class BG:
    def __init__(self, 
                 seed=None, 
                 /, 
                 max_red_diff=None, 
                 star_chance=None,
                 star_amount=None
        ):
        self.cache = {}
        if seed is None:
            seed = random.randrange(sys.maxsize)
        self.seed = seed
        
        self.rng = random.Random(seed)
        self.startState = self.rng.getstate()

        self.stars = Stars(self.rng)
        if star_chance is None:
            star_chance = random.randint(10, 40)
        self.starChance = star_chance

        if star_amount is None:
            star_amount = self.rng.randint(8, 15)
        self.star_amount = star_amount
        self.stars.STARS = [self.stars._genStar() for _ in range(star_amount)]
        
        type = self.rng.randint(0, 2)
        if type == 0:
            diff = self.rng.randint(20, 120)
            diff2 = self.rng.randint(0, diff)
            self.base = (diff2, diff-diff2, 255-diff)
        else:
            blu = self.rng.randint(0, 100)
            diff = self.rng.randint(0, blu)
            self.base = (diff, blu-diff, blu)
        
        if max_red_diff is None:
            max_red_diff = self.rng.randint(20, 40)
        
        if self.base[0] + max_red_diff >= self.base[2]:
            self.base = (max(self.base[2]-max_red_diff, 0), self.base[1], self.base[2])
    
    def _setState(self):
        self.rng.setstate(self.startState)
    
    def _gen(self, sze, x, y):
        sur = pygame.Surface(sze)
        sur.fill(self.base)
        self._setState()
        
        # Create meshgrid with xy indexing
        xs = np.arange(x, x + sze[0], dtype=np.int64)
        ys = np.arange(y, y + sze[1], dtype=np.int64)
        grid_x, grid_y = np.meshgrid(xs, ys, indexing='xy')
        grid_x = (grid_x + (1 << 15)).astype(np.uint64)
        grid_y = (grid_y + (1 << 15)).astype(np.uint64)

        # Compute the hash using vectorized arithmetic
        n = (grid_x * np.uint64(374761393)) + (grid_y * np.uint64(668265263)) + (np.uint64(self.seed) * np.uint64(982451653))
        n = (n ^ (n >> np.uint64(13))) * np.uint64(1274126177)
        rnds = n & np.uint64(0x7fffffff)

        mask = (rnds % self.starChance == 0)
        ys_idx, xs_idx = np.nonzero(mask)
        
        if ys_idx.size == 0:
            return sur

        # Compute star types and positions for all stars
        star_types = ((rnds[ys_idx, xs_idx] // self.starChance) % self.star_amount).astype(int)
        positions = list(zip(xs_idx - 2, ys_idx - 2))
        
        star_surs = self.stars.STARS
        blit_list = [(star_surs[star_types[idx]], positions[idx]) for idx in range(len(positions))]
        sur.blits(blit_list)

        return sur
    
    def __call__(self, sze, x, y):
        check = hash((sze, x, y))
        if check in self.cache:
            return self.cache[check]
        sur = self._gen(sze, x, y)
        self.cache[check] = sur
        return sur

if __name__ == '__main__':
    pygame.init()
    win = pygame.display.set_mode((500, 500), pygame.RESIZABLE)
    x, y, = 0, 0
    surZoom = 1
    bg = BG()
    clock = pygame.time.Clock()
    run = True
    while run:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                run = False
            elif ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    run = False
                elif ev.key == pygame.K_SPACE or ev.key == pygame.K_RETURN:
                    bg = BG()
        
        keys = pygame.key.get_pressed()
        if keys[pygame.K_UP]:
            y -= 10*surZoom
        elif keys[pygame.K_DOWN]:
            y += 10*surZoom
        if keys[pygame.K_LEFT]:
            x -= 10*surZoom
        elif keys[pygame.K_RIGHT]:
            x += 10*surZoom
        if keys[pygame.K_MINUS]:
            surZoom += 0.02
        elif keys[pygame.K_EQUALS]:
            surZoom -= 0.02
        surZoom = max(min(surZoom, 1), 0.1)
        
        win.blit(pygame.transform.scale(
            bg((int(win.get_width()*surZoom), int(win.get_height()*surZoom)), x, y),
            win.get_size()),
            (0, 0))
        pygame.display.update()
        clock.tick()
        pygame.display.set_caption(f'FPS: {round(clock.get_fps(), 3)}')
