# $Id$
# Time-stamp: <02/02/05 17:17:50 smulloni>

######################################################################## 
#  Copyright (C) 2001, 2002 Jacob Smullyan <smulloni@smullyan.org>
#  
#      You may distribute under the terms of either the GNU General
#      Public License or the SkunkWeb License, as specified in the
#      README file.
########################################################################

from vfs import PathPropertyStore
import shelve
from skunklib import normpath2 as _normpath

class ShelfPathPropertyStore(PathPropertyStore):
    def __init__(self, dbname):
        self.__dbname=dbname
        try:
            import dbhash
            dbhash.open(dbname, 'c')
        except:
            shelve.open(dbname)

    def __db(self):
        return shelve.open(self.__dbname)
        
    def getproperty(self, path, property):
        path=_normpath(path)
        property=str(property)
        db=self.__db()
        if db.has_key(path):
            pathhash=db[path]
            if pathhash.has_key(property):
                return pathhash[property]
        raise KeyError, property
            
    def setproperty(self, path, property, value):
        path=_normpath(path)
        property=str(property)
        db=self.__db()
        if db.has_key(path):
            pathhash=db[path]
            pathhash[property]=value
        else:
            pathhash={property : value}
        db[path]=pathhash
        db.close()

    def properties(self, path):
        path=_normpath(path)
        db=self.__db()
        if db.has_key(path):
            return db[path]
        return {}

    def hasproperty(self, path, property):
        path=_normpath(path)
        db=self.__db()
        return db.has_key(path) and db[path].has_key(property)

    def delproperty(self, path, property):
        path=_normpath(path)
        db=self.__db()
        if db.has_key(path) and db[path].has_key(property):
            del db[path][property]
            db.close()
            
########################################################################
# $Log$
# Revision 1.6  2003/05/01 20:46:02  drew_csillag
# Changed license text
#
# Revision 1.5  2002/02/06 04:45:22  smulloni
# switched to preferring dbhash
#
# Revision 1.4  2002/02/05 19:22:24  smulloni
# bug fix to AE/Executables.py;
# alternate normpath function in skunklib;
# new PathPropertyStore using AE python datacomponents;
# tweaks to other PathPropertyStores.
#
# Revision 1.3  2002/02/05 03:18:17  smulloni
# fixed ShelfPathPropertyStore, added a ZODB-based implementation, and added two methods to PathPropertyStore itself, one of them not virtual.
#
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




    
    
