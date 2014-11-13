#  
#  Copyright (C) 2001 Andrew T. Csillag <drew_csillag@geocities.com>
#  
#      You may distribute under the terms of either the GNU General
#      Public License or the SkunkWeb License, as specified in the
#      README file.
#   
#$Id: MimeTypes.py 1722 2006-03-11 20:55:32Z smulloni $
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


