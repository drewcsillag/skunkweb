# Time-stamp: <01/12/02 21:04:49 smulloni>
# $Id$

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
#
########################################################################

from SkunkWeb import Configuration
import MySQLdb
from SkunkExcept import SkunkStandardError

_users={}
_connections = {}

def initUser (connUser, **connParams):
    """
    Prior to using the module, you must call this function 
    to add a user and associate it with connect parameters. 
    The function can be called more than once.
    """
    if _users.has_key (connUser):
        raise SkunkStandardError, 'user %s already initialized!' % (connUser) 
    _users[connUser] = connParams

def cleanUser (connUser):
    """
    Destroys the database connection defined by connUser.
    If there is no database connection open for connUser,
    a SkunkStandardError is thrown.
    """
    if not _users.has_key (connUser):
        raise SkunkStandardError, 'user %s is not initialized' % (connUser)
    del _users[connUser]

def getConnection(connUser):
    """
    Returns a database connection as defined by 
    connUser. If this module already has an open
    connection for connUser, it returns it; otherwise,
    it creates a new connection, stores it, and returns it.
    """

    if not _users.has_key (connUser):
        raise SkunkStandardError, 'user %s is not initialized' % (connUser)

    if not _connections.has_key(connuser):
        connectParams = _users[connUser]
        try:
            _connections[connuser] = MySQLdb.connect(**connectParams)
        except MySQLdb.MySQLError:
            # XXX Do not raise the connect string! The trace may be seen
            # by users!!!
            raise SkunkStandardError, ('cannot connect to MySQL: %s' % 
                  (sys.exc_info()[1],))
    return _connections[connuser]

########################################################################

Configuration.mergeDefaults(
    MySQLConnectParams = {},
    )

for u, p in Configuration.MySQLConnectParams.items():
    initUser(u, **p)

########################################################################
# $Log$
########################################################################
