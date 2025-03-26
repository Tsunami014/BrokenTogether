import numpy as np
import pygame
import random
import math
import sys

class Stars:
    def __init__(self, rng):
        self.STARS = {}
        self.rng = rng
    
    def __call__(self, typ):
        if typ not in self.STARS:
            sur = self._genStar()
            self.STARS[typ] = sur
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
    def __init__(self, seed=None, /, max_red_diff=30, star_chance=None):
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
        
        type = self.rng.randint(0, 2)
        if type == 0:
            diff = self.rng.randint(20, 120)
            diff2 = self.rng.randint(0, diff)
            self.base = (diff2, diff-diff2, 255-diff)
        else:
            blu = self.rng.randint(0, 100)
            diff = self.rng.randint(0, blu)
            self.base = (diff, blu-diff, blu)
        
        if self.base[0] + max_red_diff >= self.base[2]:
            self.base = (max(self.base[2]-max_red_diff, 0), self.base[1], self.base[2])
    
    def _setState(self):
        self.rng.setstate(self.startState)
    
    def _gen(self, sze, x, y):
        sur = pygame.Surface(sze)
        sur.fill(self.base)
        self._setState()
        
        # Create a meshgrid of coordinates (note: use 'xy' indexing so xs vary along columns)
        # Use np.uint64 for the coordinate arrays.
        xs = np.arange(x, x + sze[0], dtype=np.int64)
        ys = np.arange(y, y + sze[1], dtype=np.int64)
        grid_x, grid_y = np.meshgrid(xs, ys, indexing='xy')
        # Shift negatives into the positive range before converting to uint64
        grid_x = (grid_x + (1 << 15)).astype(np.uint64)
        grid_y = (grid_y + (1 << 15)).astype(np.uint64)
        
        # Compute the hash using vectorized arithmetic in np.uint64.
        n = (grid_x * np.uint64(374761393)) ^ (grid_y * np.uint64(668265263)) ^ (np.uint64(self.seed) * np.uint64(982451653))
        n = (n ^ (n >> np.uint64(13))) * np.uint64(1274126177)
        n = n ^ (n >> np.uint64(16))
        rnds = n & np.uint64(0x7fffffff)
        
        # Find indices where the condition is met
        mask = (rnds % self.starChance == 0)
        ys_idx, xs_idx = np.nonzero(mask)
        
        # Loop only over the positions that need a star drawn.
        for row, col in zip(ys_idx, xs_idx):
            # Use the computed random value to select a star surface.
            star_index = (rnds[row, col] // self.starChance) % 10
            stSur = self.stars(star_index)
            # Blit the star with appropriate offset.
            sur.blit(stSur, (col - 2, row - 2))

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
        pygame.display.flip()
