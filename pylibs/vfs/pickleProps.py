# Time-stamp: <02/11/24 22:34:53 smulloni>

######################################################################## 
#  Copyright (C) 2002 Jacob Smullyan <smulloni@smullyan.org>
#  
#      You may distribute under the terms of either the GNU General
#      Public License or the SkunkWeb License, as specified in the
#      README file.
########################################################################

from vfs import PathPropertyStore
import cPickle
from skunklib import normpath2 as _normpath
import fcntl
import os
import re

_slashre=re.compile('/')

class PicklePathPropertyStore(PathPropertyStore):
    def __init__(self, propsDir):
        self.__picklepath=_normpath(propsDir)
        if not os.path.exists(self.__picklepath):
                os.makedirs(self.__picklepath)

    def __splitpath(self, path):
        d, fname=os.path.split(path)
        if not fname and d=='/':
            fname='/'
        return d, fname

    def __getpicklefile(self, path):
        return os.path.join(self.__picklepath,
                            "p%s" % _slashre.sub('!', path))

    def __getproperties(self, path):
        picklefile=self.__getpicklefile(path)
        if not os.path.exists(picklefile):
            return {}
        f=open(picklefile)
        fd=f.fileno()
        fcntl.flock(fd, fcntl.LOCK_SH)
        data=cPickle.load(f)
        fcntl.flock(fd, fcntl.LOCK_UN)
        f.close()
        return data

    def __saveproperties(self, path, properties):
        f=open(self.__getpicklefile(path), 'w')
        fd=f.fileno()
        fcntl.flock(fd, fcntl.LOCK_EX)
        cPickle.dump(properties, f, 1)
        fcntl.flock(fd, fcntl.LOCK_UN)
        f.close()
        
    def getproperty(self, path, property):
        return self.properties(_normpath(path))[property]
            
    def setproperty(self, path, property, value):
        path=_normpath(path)
        properties=self.__getproperties(path)
        properties[property]=value
        self.__saveproperties(path, properties)

    def properties(self, path):
        return self.__getproperties(_normpath(path))

    def hasproperty(self, path, property):
        return self.properties(path).has_key(property)

    def delproperty(self, path, property):
        path=_normpath(path)
        properties=self.__getproperties(path)
        if properties.has_key(property):
            del properties[property]
        self.__saveproperties(path, properties)

########################################################################
# $Log: pickleProps.py,v $
# Revision 1.3  2003/05/01 20:46:02  drew_csillag
# Changed license text
#
# Revision 1.2  2002/11/25 03:59:34  smulloni
# fixed some typos.
#
# Revision 1.1  2002/02/06 04:48:08  smulloni
# adding picklefile-based path property store
#
########################################################################




    
    
