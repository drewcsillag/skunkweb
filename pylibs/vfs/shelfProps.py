# $Id$
# Time-stamp: <01/09/29 21:19:57 smulloni>

######################################################################## 
#  Copyright (C) 2001 Jocob Smullyan <smulloni@smullyan.org>
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
import shelve

class ShelfPathPropertyStore(PathPropertyStore):
    def __init__(self, dbname):
        try:
            import gdbm
            gdbm.open(dbname)
            self.__db=shelve.DbfilenameShelf(dbname)
        except:
            self.__db=shelve.open(dbname)
        
    def getproperty(self, path, property):
        property=str(property)
        if db.has_key(path):
            pathhash=db[path]
            if pathhash.has_key(property):
                return pathhash[property]
        raise KeyError, property
            
    def setproperty(self, path, property, value):
        property=str(property)
        if db.has_key(path):
            pathhash=db[path]
            pathhash[property]=value
        else:
            pathhash={property : value}
        db[path]=pathhash

    def properties(self, path):
        if db.has_key(path):
            return db[path]
        return {}

    def has_property(self, path, property):
        return self.properties().has_key(str(property))
            
########################################################################
# $Log$
# Revision 1.2  2001/12/02 20:57:50  smulloni
# First fold of work done in September (!) on dev3_2 branch into trunk:
# vfs and PyDO enhancements (webdav still to come).  Also, small enhancement
# to templating's <:img:> tag.
#
# Revision 1.1.2.2  2001/10/16 03:27:15  smulloni
# merged HEAD (basically 3.1.1) into dev3_2
#
# Revision 1.1.2.1  2001/09/27 03:36:07  smulloni
# new pylibs, work on PyDO, code cleanup.
#
########################################################################




    
    
