#  
#  Copyright (C) 2001 Andrew T. Csillag <drew_csillag@geocities.com>
#  
#      You may distribute under the terms of either the GNU General
#      Public License or the SkunkWeb License, as specified in the
#      README file.
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

