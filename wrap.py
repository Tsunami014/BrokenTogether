# If you are here because you have no clue what's going on with this feel free to contact me through Discord (link in the README of Blaze Sudio)

from BlazeSudio.ldtk import sync
if not sync.is_synced():
    print(sync.explanation())
    print("For this file, it's best to use it with the 'after save', so it will automatically update the file.")
    print(sync.generate_sync_code('wrap.py', '../'))
    exit()

import os
import pygame
from BlazeSudio.Game import world
from BlazeSudio.utils import wrap

if os.getcwd().endswith('/assets'):
    os.chdir(os.path.join(os.getcwd(), '../'))

world = world.World("./assets/planets.ldtk")

imgs = [[], []]
szes = []
for lvl in range(len(world.ldtk.levels)):
    # All the Nones are the default values set by the function
    WRo = None
    WRi = None
    Wsize = 128
    Wquality = None

    Rrotation = 0
    Rsize = None

    settingsExists = False
    wraping = False
    for e in world.ldtk.levels[lvl].entities:
        if e.identifier == 'WrapSettings':
            wraping = True
            settingsExists = True
            for i in e.fieldInstances:
                if i['__identifier'] == 'Ro':
                    WRo = i['__value'] or WRo
                elif i['__identifier'] == 'Ri':
                    WRi = i['__value'] or WRi
                elif i['__identifier'] == 'Size':
                    Wsize = i['__value'] or Wsize
                elif i['__identifier'] == 'Quality':
                    Wquality = i['__value'] or Wquality
        elif e.identifier == 'RotateSettings':
            settingsExists = True
            for i in e.fieldInstances:
                if i['__identifier'] == 'Rotation':
                    Rrotation = i['__value'] or Rrotation
                elif i['__identifier'] == 'Size':
                    Rsize = i['__value']
    if not settingsExists:
        continue
    if wraping:
        szes.append(Wsize)

        i1, i2 = wrap.wrapLevel(world, lvl, WRo, WRi, Wquality)
        imgs[0].append(i1)
        imgs[1].append(i2)
    else: # Rotating
        img = pygame.transform.rotate(world.get_pygame(lvl, transparent_bg=True), Rrotation)
        newimg = pygame.Surface((max(img.get_size()), max(img.get_size())), pygame.SRCALPHA)
        newimg.blit(img, (0, 0))
        imgs[0].append(newimg)
        newsur = pygame.mask.from_surface(newimg).to_surface()
        newsur.set_colorkey((0, 0, 0))
        imgs[1].append(newsur)
        szes.append(Rsize or max(imgs[0][-1].get_size()))

pth = os.path.dirname(__file__) + "/"

wrap.save(imgs[0], pth+"assets/generated/out.png", szes)
wrap.save(imgs[1], pth+"assets/generated/colls.png", szes)
