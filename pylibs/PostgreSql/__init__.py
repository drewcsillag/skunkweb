#  
#  Copyright (C) 2001 Andrew T. Csillag <drew_csillag@geocities.com>
#  
#      You may distribute under the terms of either the GNU General
#      Public License or the SkunkWeb License, as specified in the
#      README file.
#   
import string
import pgdb
from SkunkExcept import SkunkStandardError
# The connect string dictionary 
_users={}

# an optional connection test; should be callable, take a connection
# as an argument, and return a boolean indicating whether the
# connection is valid
connection_test = None

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
    
    if not _connections.has_key(connectParams):
        try:
            connectArgs=string.split(connectParams,':')
            host=None
            if connectArgs[0]:
                if '|' in connectArgs[0]: #if specified port
                    host=connectArgs[0].replace('|', ':')
            db=_connections[connectParams]=pgdb.connect(connectParams,
                                                        host=host)
        except pgdb.Error:
            # XXX Do not raise the connect string! The trace may be seen
            # by users!!!
            raise SkunkStandardError, ('cannot connect to PostgreSQL: %s' % 
                  (sys.exc_info()[1],))
    else:
        db=_connections[connectParams]
        if connection_test and not connection_test(db):
            del db
            del _connections[connectParams]
            db=_connections[connectParams]=pgdb.connect(connectParams,
                                                        host=host)
    return db


# a reasonable test query
def SimpleQueryTest(conn):
    try:
        # poor man's assertion
        not conn._db.closed or 1 / 0
        conn.cursor().execute("select CURRENT_USER")
        return 1
    except:
        return 0

