from BlazeSudio.Game import world
from BlazeSudio.ldtk import Tileset
import BlazeSudio.utils.genCollisions as gen
import pygame

MAINWORLD = world.World('./assets/main.ldtk')
TILESETS = list(MAINWORLD.ldtk.tilesets.values())

def collisionFunc(tset: Tileset, x, y):
    sur = pygame.Surface((tset.tileGridSize, tset.tileGridSize), pygame.SRCALPHA)
    sur.fill(0)

    thisPth = tset.tilesetPath.replace('\\', '/')
    thisPth = thisPth[thisPth.rfind('/')+1:]
    
    for otherTset in TILESETS:
        if otherTset.tilesetPath.endswith(thisPth):
            break
    else:
        return sur

    collTyp = otherTset.getTileData(x, y)
    if collTyp == []:
        return sur
    collTyp = collTyp[0]

    img = tset.subsurface(x, y, tset.tileGridSize, tset.tileGridSize)

    poly = None
    if collTyp == 'FullCollision':
        poly = [(0, 0), 
                (tset.tileGridSize, 0), 
                (tset.tileGridSize, tset.tileGridSize), 
                (0, tset.tileGridSize)]
    elif collTyp == 'BoundingBox':
        poly = gen.bounding_box(img).toPoints()
    elif collTyp == 'Trace':
        poly = gen.approximate_polygon(img, 1).toPoints()
    
    if poly is None:
        return sur
    pygame.draw.polygon(sur, (255, 255, 255), poly)
    return sur
