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
import string, types

class SYSDATE: pass

##############################
## connection registry stuff
##############################
_driverConfig = {
    #driver name   module name    class in module
    'mysql':       ('mysqlconn',  'PyDOMySQL'),
    'oracle':      ('oracleconn', 'PyDOOracle'),
    'postgresql':  ('postconn',   'PyDOPostgreSQL'),
    'sapdb':       ('sapdbconn',  'PyDOsapdb'),
    'sqlite':      ('sqliteconn', 'PyDOSqlite'),
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
            colInd = string.index(rconnString, ':')
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
    
##def _getConnectionByConnString(connString):
##    if not _connStringToConnections.has_key(connString):
##        if connString[:5] != 'pydo:':
##            raise ValueError, ("invalid connect string: doesn't start"
##                               " with pydo: <%s>") % connString
##        rconnString = connString[5:]
##        colInd = string.index(rconnString, ':')
##        driverName = rconnString[:colInd]
##        driverString = rconnString[colInd+1:]
##        _connStringToConnections[connString] = _getDriver(
##            driverName)(driverString)
        
##    return _connStringToConnections[connString]
