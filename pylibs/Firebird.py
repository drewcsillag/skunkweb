# Time-stamp: <03/06/19 20:52:44 smulloni>
# $Id$

########################################################################
#  
#  Copyright (C) 2003 Andrew T. Csillag <drew_csillag@yahoo.com>,
#                     Jacob Smullyan <smulloni@smullyan.org>
#  
#      You may distribute under the terms of either the GNU General
#      Public License or the SkunkWeb License, as specified in the
#      README file.
#   
########################################################################

import string
import kinterbasdb
from SkunkExcept import SkunkStandardError
import sys
# The connect string dictionary 
_users={}

def initUser(connUser, connParams):
    """
    Prior to using the module, you must call this function 
    to add a user and associate it with a connect string. 
    The function can be called more than once.
    """

    if _users.has_key(connUser):
        raise SkunkStandardError, 'user %s already initialized!' % (connUser) 

    _users[connUser]=connParams

def cleanUser(connUser):
    """
    Destroys the database connection defined by connUser.
    If there is no database connection open for connUser,
    a SkunkStandardError is thrown.
    """

    if not _users.has_key(connUser):
        raise SkunkStandardError, 'user %s is not initialized' % (connUser)

    del _users[connUser]

#the connection dict
_connections={}

def getConnection(connUser):
    """
    Returns a database connection as defined by 
    connUser. If this module already has an open
    connection for connUser, it returns it; otherwise,
    it creates a new connection, stores it, and returns it.
    """

    if not _users.has_key(connUser):
        raise SkunkStandardError, 'user %s is not initialized' % (connUser)

    connectParams=_users[connUser]
    
    if not _connections.has_key(connUser):
        try:
			_connections[connUser] = kinterbasdb.connect(**connectParams)           
        except kinterbasdb.Error:
            # XXX Do not raise the connect string! The trace may be seen
            # by users!!!
            raise SkunkStandardError, ('cannot connect to Firebird: %s' % 
                  (sys.exc_info()[1],))

    return _connections[connUser]

