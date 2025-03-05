import json
import os
import time
import sys
import shutil

if os.getcwd().endswith('assets'):
    os.chdir(os.getcwd()+'/../')

if 'new' in sys.argv:
    npath = 'assets/maps/'+sys.argv[-1]
    os.mkdir(npath)
    shutil.copyfile('assets/main.ldtk', npath+'/main.ldtk')
    os.mkdir(npath+'/generated')
    shutil.copyfile('assets/tilesets/Blank.png', npath+'/generated/out.png')

main = json.load(open('assets/main.ldtk'))
dfs = main['defs']
for tmap in dfs['tilesets']:
    if tmap['relPath'] is not None:
        tmap['relPath'] = '../../'+tmap['relPath']
    tmap['tagsSourceEnumUid'] = None
    tmap['enumTags'] = []

for fn in os.listdir('assets/maps'):
    out = json.load(open(f'assets/maps/{fn}/main.ldtk'))

    out['customCommands'] = main['customCommands'][1:]

    ndfs = dfs.copy()
    for idx, tmap in enumerate(out['defs']['tilesets']):
        if tmap['identifier'] == 'Planets':
            tmap['relPath'] = './generated/out.png'
            ndfs['tilesets'][idx] = tmap
            break

    out['defs'] = ndfs

    json.dump(out, open(f'assets/maps/{fn}/main.ldtk', "w"))

print('Updated in all files!')
time.sleep(0.5)
