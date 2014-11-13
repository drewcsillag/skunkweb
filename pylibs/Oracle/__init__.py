#  
#  Copyright (C) 2001 Andrew T. Csillag <drew_csillag@geocities.com>
#  
#      You may distribute under the terms of either the GNU General
#      Public License or the SkunkWeb License, as specified in the
#      README file.
#   
"""
This implements a nice wrapper around the DCOracle package
and its main function. It is used by AED sql personality, 
but is entirely usable outside of AED.

Some of its features are:

simplifies connection management
can speed up use of stored procedures by fetching their signatures before-hand
simplifies handling of query results, so you don't necessarily have to
know the ordering of the columns in the result set -- they are exposed as a
dictionary where the keys are the column names and the values are the result
values.
"""

import sys
import string
import types
import marshal

try:
    import DCOracle
except:
    import DCOracle2 as DCOracle

import Date.Format
import Date.Date

try:
    from mx import DateTime
except:
    import DateTime
    
try:
    dbiRaw, dbiDate = DCOracle.dbi.dbiRaw, DCOracle.dbi.dbiDate
except:
    dbiRaw = DCOracle.dbiRaw
    dbiDate = DCOracle.DateFromTicks
    
from SkunkExcept import *

_connections = {}
#_sthCache = {}

_connDiedErrors = (1033, 1034,3114,3113,12571,12203,12224)

class __ModuleGuard:
    def __init__(self, conns ):
        # Store a reference to connections here, to make sure we're deleted
        # before it
        self.conns = conns

    def __del__(self):
        for c in self.conns.values():
             try:
                 c.rollback()
                 c.close()
             except:
                 pass

#to make it so that if the server dies or whatever, the destruction of this
#object will ensure that the connection gets rolled back before it gets
#closed or else the current transaction will commit
__modguard = __ModuleGuard( _connections )

# The connect string dictionary 
_users = {}

def initUser ( connUser, connStr ):
    """
    Prior to using the module, you must call this function 
    to add a user and associate it with a connect string. 
    The function can be called more than once.
    """

    if _users.has_key ( connUser ):
        raise SkunkStandardError, 'user %s already initialized!' % (connUser) 

    _users[connUser] = connStr 

_signatures = {}

def loadSignatures( connUser, packageList, logFunction = None,
                    debugFunction = None ):
    """
    Loads signatures of sotred procedures in the packages named by
    packageList of connection named by connUser.
    The logFunction and debugFunction
    exist so you can do a bit of debugging to see what we are loading.

    If a package name doesn't exist, you usually get some Oracle error of
    the variety saying -- "package name foo doesn't exist".
    """
    #'
    connectString = _users[connUser]
    conn = DCOracle.Connect( connectString )
    cur = conn.cursor()
    descs = {}
    for pkg in packageList:
        if logFunction:
            logFunction( 'Loading procedure signatures from package %s' % pkg )
        owner, pkgname = string.split(string.upper(string.strip(pkg)), '.')
        cur.execute( """select distinct(object_name) from all_arguments
                       where owner = :owner and package_name = :pkgname""",
                    owner = owner,
                    pkgname = pkgname )
        procnames = map( lambda x: x[0], cur.fetchall() )
      
        for procname in procnames:
            fullprocname = '%s.%s.%s' % ( owner, pkgname, procname )
            try:
                descs[fullprocname] = DCOracle.oci_.odessp( conn._d, 
                                      fullprocname )
            except:
                # Give the name of the function
                if debugFunction:
                    debugFunction( 'was getting signature for %s' % 
                                   fullprocname )

                # Re-raise
                raise

    if not _signatures.has_key( connUser ):
        _signatures[connUser] = {}
    _signatures[connUser].update( descs )
    cur.close()
    conn.close()

def cleanUser ( connUser ):
    """
    Destroys the database connection defined by connUser.
    If there is no database connection open for connUser,
    a SkunkStandardError is thrown.
    """

    if not _users.has_key ( connUser ):
        raise SkunkStandardError, 'user %s is not initialized' % (connUser)

    del _users[connUser]

def getConnection(connUser):
    """
    Returns a database connection as defined by 
    connUser. If this module already has an open
    connection for connUser, it returns it; otherwise,
    it creates a new connection, stores it, and returns it.
    """

    if not _users.has_key ( connUser ):
        raise SkunkStandardError, 'user %s is not initialized' % (connUser)

    connectString = _users[connUser]
    
    if not _connections.has_key(connectString):
        try:
            #print 'really connecting....'; sys.stdout.flush()
            _connections[connectString] = DCOracle.Connect(connectString)
        except ('oci.error', DCOracle.DCOracle.oci_.error):
            # XXX Do not raise the conenct string! The trace may be seen
            # by users!!!
            raise SkunkStandardError, ('cannot connect to oracle: %s' % 
                  (sys.exc_info()[1],))

    return _connections[connectString]

def getCursor(connUser, stmt = None):
    """try to get a cursor, and if oracle is hosed, kill the connection
    so we'll try to reconnect later"""
    try:
        c = _getCursor(connUser, stmt)
    except ('oci.error', DCOracle.DCOracle.oci_.error), val:
        #print 'got oci.error'; sys.stdout.flush()
        if val[0] in _connDiedErrors:
            # rollback, close and remove from _connections
            cs = _users[connUser]
            if _connections.has_key(cs):
                conn = _connections[cs]
                #print 'rolling back?'
                #try: conn.rollback()
                #except: pass
                #print 'closing'
                #conn.close()
                del _connections[cs]
        raise #reraise the error
    except 'OracleError', val:
        #print 'got oracleerror'; sys.stdout.flush()
        if val[0] in _connDiedErrors:
            # rollback, close and remove from _connections
            cs = _users[connUser]
            if _connections.has_key(cs):
                conn = _connections[cs]
                #print 'rolling back?'
                #try: conn.rollback()
                #except: pass
                #print 'closing'
                #conn.close()
                del _connections[cs]
        raise #reraise the error
    #print 'returning from getCursor'
    return c

def _getCursor(connUser, stmt = None):
    """
    Obtains and returns a DCOracle cursor object 
    from the database connection defined by connUser.

    This function calls getConnection to get the 
    database connection first.

    If the argument stmt is not None, then it is
    considered a SQL statement, and the cursor object is "prepared"
    with that SQL statement before being returned.
    """
    if stmt == None:
        #print 'getting connection'; sys.stdout.flush()
        c = getConnection(connUser)
        #print 'getting cursor'; sys.stdout.flush()
        c = c.cursor()
        # this is still somewhat of a hack, but it's better than the
        # previous hack, and this one shouldn't be too expensive, but I
        # still want it to work The Right Way (tm) ATC
        #print 'parsing'; sys.stdout.flush()
        c._parse('select * from dual')
        #print 'done parsing'; sys.stdout.flush()
        # but this isn't that bad anyway since doing c._parse takes less 
        # than 0.8ms (actually avgs about 0.75ms), so it's pretty darn
        # cheap.  But still irksome.
        return c
    return getConnection(connUser).prepare(stmt)

def getProcedure(connUser, procName):
    """
    Gets a stored procedure from the db connection named by
    connUser with the procedure named procName. 
    Calls getConnection to get the database connection.
    """
    if len(_signatures): #if they pre-loaded the procedure signatures
        cur = getCursor(connUser)
        try:
            return DCOracle.ociProc.Procedure(
                cur._c, procName,
                _signatures[connUser][string.upper(procName)])
        except KeyError, val:
            raise KeyError, 'no signature for procedure %s' % val
    else:
        return getattr(getCursor(connUser).procedures, procName)

    
class ResultList:
    """
    A tuple-like result set object.  
    Does conversion on the result set fetched from the database.  
    Appears as a tuple of dicts.
    """
    def __init__(self, description, results):
        """construct with the description fetched from a database cursor and
        with the result rows from a query"""
        data = []
        for result in results:
            row = {}
            for item, desc in map(None, result, description):
                if desc[1] == 'DATE':
                    if item is not None:
                        item = DateTime.gmtime(float(item))
                elif desc[1] == 'RAW':
                    item = str(item)
                row[string.lower(desc[0])] = item
  
            data.append(row)

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

# new variable "munging" functions
# purpose: to convert regular Python types/instances
# into DCOracle-compatible types/instances.

def mungeVariable(var):
    """
    A utility function. Converts DateTime objects 
    to dbiDate objects for use by DCOracle; all other
    objects are returned untouched.
    """
    # for safety (but slower), do a type check here.
    return Date.Format.isDateTime(var) and dbiDate(float(var)) or var

def mungeVariableList(var):
    """
    Munges list or tuple of objects to DCOracle-compatible types,
    calling mungeVariable with each item.
    """
    if type(var) not in (types.TupleType, types.ListType):
	raise TypeError, "argument %s must be list or tuple" % var
    return map(mungeVariable, var)

def mungeVariableDict(dict):
    """
    Converts dict of objects into DCOracle-compatible types,
    calling mungeVariable on each value and returning
    a new dictionary. You may also call this function by its
    old name, mungeBindVars.
    """
    newArgDict = {}
    for k, v in dict.items():
	newArgDict[k] = mungeVariable(v)
    return newArgDict

# backwards compatibility
mungeBindVars = mungeVariableDict

def sqlExec(connUser, stmt, bindvars = {}, start = 0, end = None, fudge = 0):
    """
    A somewhat simpler interface to execing a sql query, i.e. it does some
    input argument and result list conversions to make life in python land
    easier.

    Parameters:
    
    connUser - use the connection named by it
    bindvars - dictionary out of which to pull out bind variable values
    start - return result set starting at this index -- defaults to 0
    end - return result set up until this index -- defaults to end of
          result list
    fudge - the fudge factor, if we have only fudge more rows than we
            asked for in the entire result list, include those also
    """
    cur = getCursor(connUser, stmt)
    bindvars = mungeBindVars(bindvars)
    ret = apply(cur.execute, (), bindvars)
    if ret:
        return ret

    if start == 0 and end is None:
        results = cur.fetchall()
    elif end is None:
        results = cur.fetchall()[start : ]
    else:
        results = cur.fetchmany(end + fudge + 1)
        if len(results) > (end + fudge):
            results = results[start : end]
        else:
            results = results[start :]

    desc = cur.description
    cur.close()
    return ResultList(desc, results)

#validate that when running in gmt that these work properly
def SYSDATE(offset = 0):
    """Returns a dbiDate object representing the current time
    plus the offset parameter whose unit is in days.
    """
    return dbiDate(Date.Date() + offset)

def DateToDB(dateobj):
    """Converts a Date object to a dbiDate object.
    """
    return dbiDate(dateobj)

def DBToDate(dbiDateObj):
    """Converts a dbiDate object to a Date object.
    """
    return Date.DateTime.localtime(dbiDateObj)
