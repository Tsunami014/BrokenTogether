from BlazeSudio.ldtk import sync
if not sync.is_synced():
    print(sync.explanation())
    print("For this file, it's best to use it with the 'after save', so it will automatically update the file.")
    print(sync.generate_sync_code('wrap.py', 'planetWrapping'))
    exit()

import os
from BlazeSudio.Game import world
from BlazeSudio.utils import wrap

if os.getcwd().endswith('/assets'):
    os.chdir(os.path.join(os.getcwd(), '../'))

world = world.World("./assets/planets.ldtk")

imgs, szes = wrap.wrapWorld(world)

pth = os.path.dirname(__file__) + "/"

wrap.save(imgs[0], pth+"assets/generated/out.png", szes)
wrap.save(imgs[1], pth+"assets/generated/colls.png", szes)
