#  
#  Copyright (C) 2001 Andrew T. Csillag <drew_csillag@geocities.com>
#  
#      You may distribute under the terms of either the GNU General
#      Public License or the SkunkWeb License, as specified in the
#      README file.
#   
#$Id: InitTags.py,v 1.2 2002/06/18 15:09:50 drew_csillag Exp $

import Cache
import Executables
import CacheTag
import CompArgsTag
import ReturnTag
import DateTag
import MsgCatalogTags
import ComponentTag
import TypeTag
from SkunkExcept import *
#init funcs == initTags()  initHiddenNamespace()

def initTags():
    [Cache.tagRegistry.addTag(i) for i in [
        CacheTag.CacheTag(),
        CompArgsTag.CompArgsTag(),
        ReturnTag.ReturnTag(),
        DateTag.DateTag(),
        ComponentTag.ComponentTag(),
        ComponentTag.DataComponentTag(),
        ComponentTag.IncludeTag(),
        TypeTag.TypeTag(),
        ] + MsgCatalogTags.CatalogTags
     ]

def initHiddenNamespace():
    ns = Executables._hidden_namespace
    for i in Cache.tagRegistry.values():
        for mod in i._modules:
            #mod_name = string.split ( mod.__name__, '.' )[-1]
            mod_name = mod.__name__.split('.')[-1]

            if ns.__dict__.has_key(mod_name) and getattr(ns, mod_name) != mod:
                raise SkunkCriticalError, \
                  'module named %s exists and is different' % mod_name
            else:
                setattr ( ns, mod_name, mod )
