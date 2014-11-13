"""

wrapper functions for calling components so that AE.Component doesn't
need to be used directly

"""

from os.path import splitext, dirname
from skunklib import normpath

from AE.Component import callComponent, DT_DATA, \
     DT_REGULAR, DT_INCLUDE, NO, YES, DEFER, OLD, FORCE, \
     rectifyRelativeName as relpath, componentStack, topOfComponentStack

from AE.Cache import _fixPath

import SkunkWeb.Configuration as C

def guess_comptype(compname):
    ext=splitext(compname)[1][1:]
    if ext in ('comp', 'pycomp'):
        return DT_REGULAR
    elif ext in ('dcmp', 'pydcmp'):
        return DT_DATA
    elif ext in ('inc', 'pyinc'):
        return DT_INCLUDE
    else:
        raise ValueError, "unrecognized component type: %s" % compname    

def component(comp, **kwargs):
    comptype=kwargs.pop('comptype', None)
    if comptype is None:
            comptype=guess_comptype(comp)
    if comptype==DT_INCLUDE and kwargs:
            raise ValueError, "includes don't use keyword args!"
    cache=kwargs.pop('cache', NO)    
    return callComponent(comp,
                         argDict=kwargs,
                         compType=comptype,
                         cache=cache)

def stringcomp(comp, **kwargs):
    cache=kwargs.pop('cache', NO)
    return callComponent(comp,
                         argDict=kwargs,
                         compType=DT_REGULAR,
                         cache=cache)
def include(comp):
    return callComponent(comp,
                         argDict={},
                         compType=DT_INCLUDE)

def datacomp(comp, **kwargs):
    cache=kwargs.pop('cache', NO)
    return callComponent(comp,
                         argDict=kwargs,
                         compType=DT_DATA,
                         cache=cache)

def current_component():
    return normpath(relpath(componentStack[topOfComponentStack].name))

def curdir():
    return dirname(current_component())

def listdir(path):
    p=_fixPath(C.documentRoot, relpath(path))
    listing=C.documentRootFS.listdir(p)
    return listing

def docroot_open(path):
    p=_fixPath(C.documentRoot, relpath(path))
    return C.documentRootFS.open(p)

def docroot_exists(path):
    p=_fixPath(C.documentRoot, relpath(path))
    return C.documentRootFS.exists(p)

__all__=('component',
         'stringcomp',
         'include',
         'datacomp',
         'guess_comptype',
         'YES',
         'NO',
         'DEFER',
         'OLD',
         'FORCE',
         'relpath',
         'curdir',
         'docroot_open',
         'docroot_exists',
         'listdir',
         'current_component')
