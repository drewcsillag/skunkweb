#  
#  Copyright (C) 2001 Andrew T. Csillag <drew_csillag@geocities.com>
#  
#      You may distribute under the terms of either the GNU General
#      Public License or the SkunkWeb License, as specified in the
#      README file.
#   
import types

class SYSDATE: pass

##############################
## connection registry stuff
##############################
_driverConfig = {
    #driver name   module name    class in module
    'mysql':       ('mysqlconn',   'PyDOMySQL'),
    'oracle':      ('oracleconn',  'PyDOOracle'),
    'postgresql':  ('postconn',    'PyDOPostgreSQL'),
    'pypgsql':	    ('pypgsqlconn', 'PyDOPostgreSQL'),
    'psycopg':	    ('psycopgconn', 'PyDOPostgreSQL'),
    'sapdb':       ('sapdbconn',   'PyDOsapdb'),
    'sqlite':      ('sqliteconn',  'PyDOSqlite'),
    }
_loadedDrivers = {}

_aliasToConnArgs= {}
_aliasToConnections = {}

def DBIInitAlias(alias, connectArgs):
    _aliasToConnArgs[alias] = connectArgs

def DBIGetConnection(alias):
    if alias is None:
        raise ValueError, 'connection alias is None!'

    if not _aliasToConnections.has_key(alias):
        connArgs = _aliasToConnArgs.get(alias)
        if not connArgs:
            raise ValueError, "alias %s not recognized" % alias
        argType=type(connArgs)
        if argType in (types.StringType, types.UnicodeType):
            if connArgs[:5] != 'pydo:':
                raise ValueError, ("invalid connect string: doesn't start"
                                   " with pydo: <%s>") % connArgs
            rconnString = connArgs[5:]
            colInd = rconnString.index(':')
            driverName = rconnString[:colInd]
            driverArgs = rconnString[colInd+1:]
        elif argType==types.DictType:
            driverName=connArgs.get('driver')
            if not driverName:
                raise ValueError, "no driver specified!"
            driverArgs=connArgs.copy()
            del driverArgs['driver']
        _aliasToConnections[alias]=_getDriver(driverName)(driverArgs)
            
    return _aliasToConnections[alias]

def _getDriver(driverName):
    if not _loadedDrivers.has_key(driverName):
        mod, attr = _driverConfig[driverName]
        PyDOMod = __import__('PyDO.'+ mod)
        driverMod = getattr(PyDOMod, mod)
        _loadedDrivers[driverName] = getattr(driverMod, attr)
        
    return _loadedDrivers[driverName]
    
