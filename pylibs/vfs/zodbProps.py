# $Id: zodbProps.py,v 1.1 2002/02/05 03:18:17 smulloni Exp $
# Time-stamp: <02/02/05 02:45:40 smulloni>

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
import ZODB
from Persistence import PersistentMapping
import BTrees.OOBTree
from ZEO import ClientStorage
from skunklib import normpath2 as _normpath


class ZODBPathPropertyStore(PathPropertyStore):

    """
    a PathPropertyStore implementation backed by a ZODB, using
    OOBTree and PersistentMapping, accessed via a ZEO ClientStorage.
    You specify the connection specs for the ClientStorage (see the
    ClientStorage constructor), and optionally the key under which
    the data will be stored under the root (defaults to 'pps_store')
    """
    
    def __init__(self, connectSpecs, root='pps_store'):
        storage=ClientStorage.ClientStorage(connectSpecs)
        db=ZODB.DB(storage)
        self.__conn=db.open()
        dbroot=self.__conn.root()
        if not dbroot.has_key(root):
            dbroot[root]=BTrees.OOBTree.OOBTree()
            get_transaction().commit()
        self.__db=dbroot[root]
        
    def getproperty(self, path, property):
        path=_normpath(path)
        self.__conn.sync()
        db=self.__db
        if db.has_key(path):
            pathhash=db[path]
            if pathhash.has_key(property):
                return pathhash[property]
        raise KeyError, property

    def setproperty(self, path, property, value):
        path=_normpath(path)
        self.__conn.sync()
        db=self.__db
        if db.has_key(path):
            pathhash=db[path]
        else:
            pathhash=PersistentMapping()
            db[path]=pathhash
        pathhash[property]=value
        get_transaction().commit()
        
    def properties(self, path):
        path=_normpath(path)
        self.__conn.sync()
        db=self.__db
        if db.has_key(path):
            return db[path].data.copy()
        return ()

    def hasproperty(self, path, property):
        path=_normpath(path)
        self.__conn.sync()
        db=self.__db
        return db.has_key(path) and db[path].has_key(property)

    def delproperty(self, path, property):
        path=_normpath(path)
        self.__conn.sync()
        db=self.__db
        if db.has_key(path) and db[path].has_key(property):
            del db[path][property]
            get_transaction.commit()

    
########################################################################
# $Log: zodbProps.py,v $
# Revision 1.1  2002/02/05 03:18:17  smulloni
# fixed ShelfPathPropertyStore, added a ZODB-based implementation, and added two methods to PathPropertyStore itself, one of them not virtual.
#
########################################################################
