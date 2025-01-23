# If you are here because you have no clue what's going on with this feel free to contact me through Discord (link in the README of Blaze Sudio)

from BlazeSudio.ldtk import sync
if not sync.is_synced():
    print(sync.explanation())
    print(sync.generate_sync_code('wrap.py', '../'))
    exit()

import os
from BlazeSudio.graphics import Screen, GUI, options as GO, Progressbar
from BlazeSudio.graphics.loading import DEFAULT_FORMAT_FUNC
from BlazeSudio.Game import world
from BlazeSudio.utils import wrap
# Because we load the world *before* we use the GUI
import pygame
pygame.init()
pygame.display.set_mode()
pygame.display.toggle_fullscreen()

worldCwd = os.getcwd()

world = world.World(worldCwd+'/main.ldtk')

if '/brokenTogether' not in os.getcwd():
    raise FileNotFoundError('I HAVE NO IDEA WHERE I AM PANIK PANIK PANIK!!!!!!!!!!')

os.chdir(os.getcwd()[:os.getcwd().index('/brokenTogether')+15])

from loadWorld import collisionFunc  # noqa: E402

imgs = [[], []]
class Chooser(Screen):
    def __init__(self):
        self.chosen = None
        self.opts = []
        super().__init__()
    
    def _LoadUI(self):
        self.layers[0].add('Main')
        btn = GUI.Button(self, GO.PCCENTER, GO.CBLACK, "ALL!!!", GO.CWHITE)
        btn.lvl = None
        self['Main'].append(btn)
        rainbow = GO.CRAINBOW()
        for lvl in range(len(world.ldtk.levels)):
            lvlObj = world.ldtk.levels[lvl]
            for e in lvlObj.entities:
                if e.identifier == 'WrapSettings':
                    btn = GUI.Button(self, GO.PCCENTER, next(rainbow), (lvlObj.identifier))
                    self.opts.append(lvl)
                    btn.lvl = lvl
                    self['Main'].append(btn)
    
    def _ElementClick(self, obj):
        self.chosen = obj
        self.Abort()

    def _Last(self, aborted):
        return self.chosen, self.opts

chosen, opts = Chooser()()
if chosen is None:
    exit()

if chosen.lvl is None:
    levels = opts
else:
    levels = [chosen.lvl]

@Progressbar(100)
def run(slf):
    yield 'Starting'

    doneLvls = 0
    for lvl in levels:
        Top = 0.5
        Bottom = -0.5
        Limit = True
        Invert = False

        wraping = False
        segs = []
        lvlObj = world.ldtk.levels[lvl]
        for e in lvlObj.entities:
            if e.identifier == 'WrapSettings':
                wraping = True
                for i in e.fieldInstances:
                    if i['__identifier'] == 'top':
                        Top = i['__value']
                    elif i['__identifier'] == 'bottom':
                        Bottom = i['__value']
                    elif i['__identifier'] == 'limit':
                        Limit = i['__value']
                    elif i['__identifier'] == 'Invert':
                        Invert = i['__value']
            elif e.identifier == 'Segment':
                segs.append(wrap.Segment(e.ScaledPos[0], e.fieldInstances[0]['__value']['cx']*e.gridSze+e.layerOffset[0]))
        if wraping:
            doneLvls += 1
            yield 'Wrapping', {'formatter': lambda *args: DEFAULT_FORMAT_FUNC(args[0]+f' for level {lvlObj.identifier} ({doneLvls}/{len(levels)})', *args[1:])}
            i1, i2 = yield from wrap.wrapLevel(world, lvl, collisionFunc, Top, Bottom, Limit, 0, segs, [255, 255, 255, 10], Invert, True)
            imgs[0].append(i1)
            imgs[1].append(i2)

    yield 'Saving', {'formatter': DEFAULT_FORMAT_FUNC, 'amount': 100, 'done': 99}

    blanks = wrap.find_blanks(imgs[0], imgs[1])
    if chosen.lvl is None:
        wrap.save(imgs[0], worldCwd+"/generated/out.png", 256, blanks)
        wrap.save(imgs[1], worldCwd+"/generated/colls.png", 256, blanks)
        wrap.saveData(imgs[0], worldCwd+"/generated/dat.txt", [
            world.ldtk.levels[lvl].identifier for lvl in range(len(world.ldtk.levels)) if any(
                e.identifier == 'WrapSettings' for e in world.ldtk.levels[lvl].entities
            )
        ], 256, blanks)
    else:
        name = chosen.get()
        wrap.update(imgs[0][0], name, worldCwd+"/generated/out.png", worldCwd+"/generated/dat.txt", 256, blanks[0])
        wrap.update(imgs[1][0], name, worldCwd+"/generated/colls.png", worldCwd+"/generated/dat.txt", 256, blanks[0])

run()