import os
import sys
from scrape import *

CLASS_TREE = {}
REV_CLASS_TREE = {}

FILES_BY_NAME = {}
for fi in FILES:
    FILES_BY_NAME[fi.name] = fi
    if fi.extends is not None:
        CLASS_TREE[fi.name] = fi.extends
        REV_CLASS_TREE[fi.extends] = [
            fi.name] if fi.extends not in REV_CLASS_TREE else REV_CLASS_TREE[fi.extends] + [fi.name]


def pathize(i): return [x[0].upper() + x[1:] for x in i.replace(
    './three.js/docs/api/en/', '').replace('.html', '').split('/')]


with open('../src/THREE/Types.purs', 'w') as types:
    allTypes = []
    for fi in FILES:
        allTypes.append(fi.name)
    types.write(
        'module THREE.Types where\nimport Unsafe.Coerce (unsafeCoerce)\n')
    for tp in set([x for x in allTypes if type(x) == type('ugh')]):
        if tp in FILES_BY_NAME:
            types.write(f'data {tp}\n')


def normalizeArg(i):
    return '(Array ('+normalizeArg(i.val)+'))' if isinstance(i, ArrayArg) else '{' + ','.join([i.name + ' :: ' + normalizeArg(i.tp) for x in i.args]) + '}' if isinstance(
        i, ObjectArg) else 'HTMLVideoElement' if i == 'Video' else 'HTMLImageElement' if i == 'Image' else 'Number' if i == 'Float' else 'Int' if i == 'Integer' else i

CONSTANT_FILES = []
for fi in FILES:
    if fi.name == 'Core Constants':
        # don't use core for now
        # use it if/when we need it
        continue
    if fi.fileType != FileType.CONSTANTS:
        continue
    path = pathize(fi.path)
    # print('.'.join(path))
    pth = '../src/THREE/'+('/'.join(path))+'.purs'
    pthm1 = '/'.join(pth.split('/')[:-1])
    isExist = os.path.exists(pthm1)
    psMod = '.'.join(path)
    CONSTANT_FILES.append(psMod)

# sys.exit(0)
for fi in FILES:
    if fi.name == 'Core Constants':
        # don't use core for now
        # use it if/when we need it
        continue
    path = pathize(fi.path)
    # print('.'.join(path))
    pth = '../src/THREE/'+('/'.join(path))+'.purs'
    pthm1 = '/'.join(pth.split('/')[:-1])
    isExist = os.path.exists(pthm1)
    if not isExist:
        os.makedirs(pthm1)
    with open(pth, 'w') as ofi:
        psMod = '.'.join(path)
        constantImports = '\n'.join(['import THREE.'+cf for cf in CONSTANT_FILES]) if fi.fileType == FileType.CLASS else ''
        ofi.write(
            f'module THREE.{psMod} where\n\nimport Prelude\nimport Effect (Effect)\nimport Effect.Uncurried\n{constantImports}\nimport Web.HTML.HTMLVideoElement\nimport Web.HTML.HTMLImageElement\nimport THREE.Types\nimport Unsafe.Coerce(unsafeCoerce)\n')
        supers = []
        ext = CLASS_TREE[fi.name] if fi.name in CLASS_TREE else '@!$#$@$'
        while True:
            # print(ext)
            if ext not in CLASS_TREE:
                break
            toImport = 'THREE.'+('.'.join(pathize(FILES_BY_NAME[ext].path)))
            ofi.write(f'import {toImport}\n')
            supers.append(ext)
            ext = CLASS_TREE[ext]
        # logic for array replacement
        ####
        # if fi.fileType == FileType.CLASS:
        #     ofi.write(f'data {fi.name}\n')
        with open('../src/THREE/Types.purs', 'a') as types:
            if fi.name in REV_CLASS_TREE:
                types.write(f'class Is{fi.name} (a :: Type)\n')
                types.write(
                    f'as{fi.name} :: forall a. Is{fi.name} a => a -> {fi.name}\nas{fi.name} = unsafeCoerce\n')
            for super in supers:
                types.write(f'instance Is{super} {fi.name}\n')
        if fi.constants is not None:
            doneAlready = set()
            for c in fi.constants:
                cname = c.name[0].upper()+c.name[1:]
                ofi.write(f'data {cname}\n')
                ofi.write(f'class Is{cname} (a :: Type)\n')
                ofi.write(
                    f'as{cname} :: forall a. Is{cname} a => a -> {cname}\nas{cname} = unsafeCoerce\n')
                for constant in c.constants:
                    lc = constant[0].lower() + constant[1:]
                    constant = constant[0].upper() + constant[1:]
                    if constant not in doneAlready:
                        ofi.write(
                            f'data {constant}\nforeign import {lc} :: {constant}\n')
                    doneAlready.add(constant)
                    ofi.write(f'instance Is{cname} {constant}\n')
        if fi.ctor is not None:
            ctorArgs = [normalizeArg(x.tp) for x in fi.ctor.args]
            ctorArgsE = (' -> '.join(ctorArgs) + ' -> Effect '+fi.name) if len(ctorArgs) != 0 else ('Effect '+fi.name)
            ctorArgsEfn = ('EffectFn' + \
                str(len(ctorArgs)) + ' ' + ' '.join(ctorArgs) + ' '+fi.name)  if len(ctorArgs) != 0 else ('Effect '+fi.name)
            ofi.write(f'foreign import ctor :: {ctorArgsE}\n')
            ofi.write(f'foreign import ctorE :: {ctorArgsEfn}\n')
    with open(pth.replace('.purs', '.js'), 'w') as ofi:
        psMod = '.'.join(path)
        jsp = 'three/src/constants.js' if fi.fileType == FileType.CONSTANTS else 'three/src/' + \
            ('/'.join(path))+'.js'
        ofi.write(f'import * as {path[-1]} from \'{jsp}\'\n')
        if fi.constants is not None:
            # print(fi.constants)
            doneAlready = set()
            for c in fi.constants:
                for constant in c.constants:
                    lc = constant[0].lower() + constant[1:]
                    if constant not in doneAlready:
                        ofi.write(
                            f'export const {lc} = {path[-1]}.{constant}\n')
                        doneAlready.add(constant)
        if fi.ctor is not None:
            ctorArgs = [(x.name) for x in fi.ctor.args]
            ctorArgsE = (' => '.join([f'({x})' for x in ctorArgs]) + ' => () => new '+path[-1]+'.'+path[-1]+'('+ (','.join([f'{x}' for x in ctorArgs])) +')') if len(ctorArgs) != 0 else ('() => new '+path[-1]+'()')
            ofi.write(f'export const ctor = {ctorArgsE}\n')
            ofi.write(f'export const ctorE = (...args) => new {path[-1]}.{path[-1]}(...args) \n')
