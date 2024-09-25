from BlazeSudio.ldtk import sync
if not sync.is_synced():
    print(sync.explanation())
    print("For this file, it's best to use it with the 'after save', so it will automatically update the file.")
    print(sync.generate_sync_code('wrap.py', 'planetWrapping'))
    exit()

import os
from BlazeSudio.Game import world
from BlazeSudio.utils import wrap

world = world.World("./planets.ldtk")

imgs, szes = wrap.wrapWorld(world)

pth = os.path.dirname(__file__) + "/"

wrap.save(imgs[0], pth+"out/out.png", szes)
wrap.save(imgs[1], pth+"out/colls.png", szes)
