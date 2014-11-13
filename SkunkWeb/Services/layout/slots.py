import os
import datetime
import computils
from AE.Component import DT_INCLUDE
import SkunkWeb.Configuration as C

C.mergeDefaults(skinDir='/comp/skins',
                defaultSkin='default')

import threading
_local=threading.local()
_local.SLOTSTACK=[]

def getCurrentSlot():
    if _local.SLOTSTACK:
        return _local.SLOTSTACK[-1]

def push_slot(slot):
    _local.SLOTSTACK.append(slot)

def pop_slot():
    if _local.SLOTSTACK:
        _local.SLOTSTACK.pop()

class Slot(object):
    def __init__(self, name):
        self.name=name

class ComponentSlot(Slot):
    def __init__(self, name, compname, comptype=None, cache=computils.NO, **kw):
        Slot.__init__(self, name)
        self.compname=computils.relpath(compname)
        if comptype is None:
            self.comptype=computils.guess_comptype(compname)
        self.cache=cache
        self.extra=kw

        
    def __call__(self, **kwargs):
        cache=kwargs.pop('cache', self.cache)
        kwargs.update(self.extra)
        try:
            push_slot(self.name)
            if self.comptype==DT_INCLUDE:
                res=computils.include(self.compname)
            else:
                res=computils.component(self.compname,
                                        comptype=self.comptype,
                                        cache=cache,
                                        **kwargs)

        finally:
            pop_slot()
        return res


__all__=['Slot', 'ComponentSlot', 'getCurrentSlot']
