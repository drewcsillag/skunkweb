#  
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
import string
import pgdb

# The connect string dictionary 
_users = {}

def initUser ( connUser, connParams ):
    """
    Prior to using the module, you must call this function 
    to add a user and associate it with a connect string. 
    The function can be called more than once.
    """

    if _users.has_key ( connUser ):
        raise SkunkStandardError, 'user %s already initialized!' % (connUser) 

    _users[connUser] = connParams

def cleanUser ( connUser ):
    """
    Destroys the database connection defined by connUser.
    If there is no database connection open for connUser,
    a SkunkStandardError is thrown.
    """

    if not _users.has_key ( connUser ):
        raise SkunkStandardError, 'user %s is not initialized' % (connUser)

    del _users[connUser]

#the connection dict
_connections = {}

def getConnection(connUser):
    """
    Returns a database connection as defined by 
    connUser. If this module already has an open
    connection for connUser, it returns it; otherwise,
    it creates a new connection, stores it, and returns it.
    """

    if not _users.has_key ( connUser ):
        raise SkunkStandardError, 'user %s is not initialized' % (connUser)

    connectParams = _users[connUser]
    
    if not _connections.has_key(connectParams):
        try:
            _connections[connectParams] = apply(pgdb.connect, connectParams)
        except pgdb.error:
            # XXX Do not raise the conenct string! The trace may be seen
            # by users!!!
            raise SkunkStandardError, ('cannot connect to PostgreSQL: %s' % 
                  (sys.exc_info()[1],))

    return _connections[connectParams]

class ImmutableDict:
    """
    An immutable dictionary that represents a row of
    data fetched from a database cursor. It's immutable because
    result records from database cursors should generally not
    be mutable...

    The methods on me are the same as you would find on 
    a regular dictionary, except for __setitem__ and
    __delitem__, of course.
    """
    def __init__(self, dict):
        self.__dict = dict

    def __hash__(self):
        return hash(tuple(self.__dict.items()))

    def keys(self):
        return self.__dict.keys()

    def values(self):
        return self.__dict.values()

    def items(self):
        return self.__dict.items()
    
    def get(self, item, default=None):
	if self.__dict.has_key(item):
	    return self.__dict[item]
	else:
	    return default
	
    def __len__(self):
        return len(self.__dict)
    
    def __getitem__(self, item):
        return self.__dict[item]

    def __repr__(self):
        return repr(self.__dict)
    
class ResultList:
    """
    A tuple-like result set object.  
    Does conversion on the result set fetched from the database.  
    Appears as a tuple of ImmutableDict objects.
    """
    def __init__(self, description, results):
        """construct with the description fetched from a database cursor and
        with the result rows from a query"""
        data = []
        for result in results:
            row = {}
            for item, desc in map(None, result, description):
                #if desc[1] == 'DATE':
                #    if item is not None:
                #        item = DateTime.gmtime(float(item))
                #elif desc[1] == 'RAW':
                #    item = str(item)
                row[string.lower(desc)] = item
  
            data.append(ImmutableDict(row))
        self.data = tuple(data)
        
    def __getitem__(self, itemno):
        return self.data[itemno]

    def __hash__(self):
        return hash(self.data)

    def __len__(self):
        return len(self.data)
    
    def __repr__(self):
        return repr(self.data)

    def index ( self, item ):
        """same as index on a regular tuple"""
	return self.data.index ( item )
  
    def count( self, item ):
	return self.data.count ( item )

def sqlExec(connUser, stmt, start = 0, end = None, fudge = 0):
    """
    A somewhat simpler interface to execing a sql query, i.e. it does some
    input argument and result list conversions to make life in python land
    easier.

    Parameters:
    
    connUser - use the connection named by it
    start - return result set starting at this index -- defaults to 0
    end - return result set up until this index -- defaults to end of
          result list
    fudge - the fudge factor, if we have only fudge more rows than we
            asked for in the entire result list, include those also
    """
    conn = getConnection(connUser)
    r = conn.query(stmt)
    if type(r) == type(1):
        return 0

    if start == 0 and end is None:
        results = r.getresult()
    elif end is None:
        results = r.getresult()[start : ]
    else:
        results = r.getresult()
        if len(results) > (end + fudge):
            results = results[start : end]
        else:
            results = results[start :]

    desc = r.listfields()
    return ResultList(desc, results)
