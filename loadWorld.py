from functools import lru_cache
from BlazeSudio.Game import world
from BlazeSudio.ldtk import Tileset
from BlazeSudio import collisions
import BlazeSudio.utils.genCollisions as gen
import pygame

MAINWORLD = world.World('./assets/main.ldtk')
TILESETS = list(MAINWORLD.ldtk.tilesets.values())

@lru_cache
def collisionFuncColl(tset: Tileset, x, y):
    thisPth = tset.tilesetPath.replace('\\', '/')
    thisPth = thisPth[thisPth.rfind('/')+1:]
    
    for otherTset in TILESETS:
        if otherTset.tilesetPath.endswith(thisPth):
            break
    else:
        return collisions.NoShape()

    collTyp = otherTset.getTileData(x, y)
    if collTyp == []:
        return collisions.NoShape()
    collTyp = collTyp[0]

    img = tset.subsurface(x, y, tset.tileGridSize, tset.tileGridSize)

    poly = None
    if collTyp == 'FullCollision':
        poly = collisions.Rect(0, 0, tset.tileGridSize, tset.tileGridSize)
    elif collTyp == 'BoundingBox':
        poly = gen.bounding_box(img)
    elif collTyp == 'Trace':
        poly = gen.approximate_polygon(img, 1)
    elif collTyp == 'Corners':
        poly = gen.corners(img)
    
    if poly is None:
        return collisions.NoShape()
    return poly

def collisionFunc(tset: Tileset, x, y):
    sur = pygame.Surface((tset.tileGridSize, tset.tileGridSize), pygame.SRCALPHA)
    sur.fill(0)

    poly = collisionFuncColl(tset, x, y)

    if collisions.checkShpType(poly, collisions.ShpTyps.NoShape):
        return sur
    pygame.draw.polygon(sur, (255, 255, 255), poly.toPoints())
    return sur
