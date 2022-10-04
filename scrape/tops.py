from scrape import *

CLASS_TREE = {}
REV_CLASS_TREE = {}

for fi in FILES:
    if fi.extends is not None:
        CLASS_TREE[fi.name] = fi.extends
        REV_CLASS_TREE[fi.extends] = [fi.name] if fi.extends not in REV_CLASS_TREE else REV_CLASS_TREE[fi.extends] + [fi.name]

# print(CLASS_TREE)
import os
for fi in FILES:
    path = [x[0].upper() + x[1:] for x in fi.path.replace('./three.js/docs/api/en/','').replace('.html','').split('/')]
    # print('.'.join(path))
    pth = '../src/THREE/'+('/'.join(path))+'.purs'
    pthm1 = '/'.join(pth.split('/')[:-1])
    isExist = os.path.exists(pthm1)
    if not isExist:
        os.makedirs(pthm1)
    with open(pth, 'w') as ofi:
        psMod = '.'.join(path)
        ofi.write(f'module THREE.{psMod} where\n')
    with open(pth.replace('.purs','.js'), 'w') as ofi:
        psMod = '.'.join(path)
        jsp = 'three/src/'+('/'.join(path))+'.js'
        ofi.write(f'import * as {path[-1]} from \'{jsp}\'\n')