#  
#  Copyright (C) 2001 Andrew T. Csillag <drew_csillag@geocities.com>
#  
#      This program is free software; you can redistribute it and/or modify
#      it under the terms of the GNU General Public License as published by
#      the Free Software Foundation; either version 2 of the License, or
#      (at your option) any later version.
#  
#      This program is distributed in the hope that it will be useful,
#      but WITHOUT ANY WARRANTY; without even the implied warranty of
#      MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#      GNU General Public License for more details.
#  
#      You should have received a copy of the GNU General Public License
#      along with this program; if not, write to the Free Software
#      Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111, USA.
#   
#$Id: InitTags.py,v 1.4 2001/07/09 20:38:41 drew Exp $

import Cache
import Executables
import CacheTag
import CompArgsTag
import ReturnTag
import DateTag
import MsgCatalogTags
import ComponentTag
import TypeTag

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
