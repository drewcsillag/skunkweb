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

class Config:
    def __init__(self):
        self._d = {}
        
    def mergeDefaults(self, *args, **kw):
        """
        added for compatibility with the
        config object used by SkunkWeb
        """
        self._mergeDefaultsKw(**kw)
        for dict in args:
            self._mergeDict(dict)

    def _mergeDefaultsKw(self, **kw): # for defaults
        for k, v in kw.items():
            if not self._d.has_key(k):
                self._d[k] = v
        
    def _mergeDict(self, dict): #for changes
        self._d.update(dict)
        
    def __getattr__(self, k):
        try:
            return self._d[k]
        except KeyError, k:
            raise AttributeError, k

Configuration = Config()

def serverInit():
    import Executables, CodeSources, MimeTypes, InitTags
    Executables.initTemplateMimeTypes()
    CodeSources.installIntoTraceback()
    MimeTypes.loadMimeTypes()
    InitTags.initTags()
    InitTags.initHiddenNamespace()

def childInit():
    import Cache
    Cache.initTempStuff()

