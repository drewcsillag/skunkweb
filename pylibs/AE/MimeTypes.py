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
#$Id: MimeTypes.py,v 1.1.1.1 2001/08/05 15:00:37 drew_csillag Exp $
import os
import sys

#config vars
import cfg
cfg.Configuration.mergeDefaults(
    mimeTypesFile = 'mime.types',
    defaultMimeType = 'application/octet-stream'
    )
#/config

_mimeTypeMap = {}

#init funcs == loadMimeTypes()

def loadMimeTypes():
    lines = open(cfg.Configuration.mimeTypesFile).readlines()
    for line in lines:
        if not line or line[0] == '#': continue
        items = line.split()
        if len(items) < 2: continue
        for extension in items[1:]:
            _mimeTypeMap[extension.upper()] = items[0]
        
def getMimeType( name ):
    dotind = name.rfind('.')
    if dotind == -1:
        return cfg.Configuration.defaultMimeType
    return _mimeTypeMap.get(name[dotind+1:].upper(),
                            cfg.Configuration.defaultMimeType)


