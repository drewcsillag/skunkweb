# $Id: pickleProps.py,v 1.1 2002/02/06 04:48:08 smulloni Exp $
# Time-stamp: <02/11/24 22:34:53 smulloni>

######################################################################## 
#  Copyright (C) 2002 Jacob Smullyan <smulloni@smullyan.org>
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
# Revision 1.1  2002/02/06 04:48:08  smulloni
# adding picklefile-based path property store
#
########################################################################




    
    
