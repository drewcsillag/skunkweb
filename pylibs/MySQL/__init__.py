# Time-stamp: <03/04/22 22:34:02 smulloni>
# $Id: __init__.py,v 1.8 2002/07/10 17:55:17 drew_csillag Exp $

########################################################################
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
########################################################################

import sys
import MySQLdb
from SkunkExcept import *

# The connect params dictionary 
_users = {}

# actual connections
_connections = {}

# an optional connection test; should be callable, take a connection
# as an argument, and return a boolean indicating whether the
# connection is valid
connection_test = None

# a reasonable test query
def SimpleQueryTest(conn):
    try:
        conn.ping()
    except MySQLdb.DatabaseError:
        return 0
    else:
        return 1

def initUser(connUser, connParams):
    """
    Prior to using the module, you must call this function 
    to add a user and associate it with a connect string. 
    The function can be called more than once.
    """
    if not _users.has_key(connUser):
        _users[connUser] = connParams

def cleanUser(connUser):
    """
    Destroys the database connection defined by connUser.
    If there is no database connection open for connUser,
    a SkunkStandardError is thrown.
    """
    if not _users.has_key(connUser) :
        raise SkunkStandardError, 'user %s is not initialized' % (connUser)

    del _users[connUser]
    if _connections.has_key(connUser):
        del _connections[connUser]

def getConnection(connUser):
    """
    Returns a database connection as defined by 
    connUser. If this module already has an open
    connection for connUser, it returns it; otherwise,
    it creates a new connection, stores it, and returns it.
    """
    try:
        connectParams = _users[connUser]
    except KeyError:
        raise SkunkStandardError, 'user %s is not initialized' % (connUser)
    
    if not _connections.has_key(connUser):
        db = _connections[connUser] = _real_connect(connUser, connectParams)
    else:
        db=_connections[connUser]
        # hook for testing the connection before returning it from the cache
        if connection_test and not connection_test(db):
            # there is apparently a bug in some versions of MySQLdb
            # that causes connections not to be closed properly
            # when garbage collected.  This attempts to resolve that
            # problem when possible.
            try:
                db.close()
            except:
                pass
            # these next are redundant
            del db
            del _connections[connUser]
            
            db=_real_connect(connUser, connectParams)
            _connections[connUser]=db
    return db

def _real_connect(connUser, connParams):
    return MySQLdb.connect(**connParams)
    
def _initStuff():
    #here so that these will be imported ahead of time so that
    #userModuleCleanup won't clobber them
    import MySQLdb
    from MySQLdb import connections, converters, cursors, sets, times
    from MySQLdb import constants, _mysql
    from MySQLdb.constants import CLIENT, CR, ER, FIELD_TYPE, FLAG, REFRESH
    
_initStuff()
