#  
#  Copyright (C) 2001 Andrew T. Csillag <drew_csillag@geocities.com>
#  
#      You may distribute under the terms of either the GNU General
#      Public License or the SkunkWeb License, as specified in the
#      README file.
#   

import Cache
import Executables
import CacheTag
import CompArgsTag
import ReturnTag
try:
    import mx.DateTime
except ImportError:
    _have_mx=0
else:
    _have_mx=1
    import DateTag
    
import MsgCatalogTags
import ComponentTag
import TypeTag
from SkunkExcept import *

def initTags():
    tags=[CacheTag.CacheTag(),
          CompArgsTag.CompArgsTag(),
          ReturnTag.ReturnTag(),
          ComponentTag.ComponentTag(),
          ComponentTag.DataComponentTag(),
          ComponentTag.IncludeTag(),
          TypeTag.TypeTag()
          ]
    if _have_mx:
        tags.append(DateTag.DateTag())
    tags.extend(MsgCatalogTags.CatalogTags)
    for t in tags:
        Cache.tagRegistry.addTag(t)
    


def initHiddenNamespace():
    ns = Executables._hidden_namespace
    for i in Cache.tagRegistry.values():
        for mod in i._modules:
            mod_name = mod.__name__.split('.')[-1]

            if ns.__dict__.has_key(mod_name) and getattr(ns, mod_name) != mod:
                raise SkunkCriticalError, \
                  'module named %s exists and is different' % mod_name
            else:
                setattr ( ns, mod_name, mod )
