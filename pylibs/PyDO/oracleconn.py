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
import types
import Date
from Date import DateTime
import string
from PyDO import SYSDATE #circular import ok, since we're loaded after PyDO
import DCOracle
import Oracle

class _NO_VALUE: pass

def _isdml(sql):
    if sql[:7] in ('UPDATE ', 'DELETE ', 'INSERT '):
        return 1
    
class PyDOOracle:
    """PyDBI - PyDO oracle driver"""
    def __init__(self, connectString):
        self.connectString = connectString
        realConn, self.useOracleMod, self.verbose = self._parseConnectString(
            connectString)
        self.realConn = realConn
        if self.useOracleMod:
            self.conn = Oracle.getConnection(realConn)
        else:
            self.conn = DCOracle.Connect(realConn)
        self.bvcount = 0
        oraConns.append(self.conn)
        self.bindVariables = 1
        if self.verbose:
            print 'CONNECTED'
        
    def _parseConnectString(self, s):
        bits = string.split(s, '|')
        verbose = 0
        useOracleMod = 0
        if len(bits) == 1:
            return bits[0], 0, 0
        else:
            if bits[1] == 'cache':
                useOracleMod = 1
                bits = bits[1:]
            if len(bits) > 0 and bits[1] == 'verbose':
                verbose = 1
            return bits[0], useOracleMod, verbose

    def getConnection(self):
        return self.conn

    def sqlStringAndValue(self, val, attr, dbtype):
        if val == SYSDATE:
            return 'SYSDATE', _NO_VALUE
        if Date.isDateTime(val):
            val = _dateConvertToDB(val)
        if string.upper(dbtype) == "LONG RAW":
            val = DCOracle.dbi.dbiRaw(val)
        self.bvcount = self.bvcount + 1
        return ':p%d' % self.bvcount, val

    def getBindVariable(self):
        self.bvcount = self.bvcount + 1
        return ':p%d' % self.bvcount

    def convertData(self, val, dbtype):
        return self.typeCheckAndConvert(val, 'bogus', dbtype)
    
    def resetQuery(self):
        self.bvcount = 0

    def getAutoIncrement(self, name): pass
    def getSequence(self, name):
        cur = self.conn.cursor()
        sql = 'select %s.nextval from dual' % name
        if self.verbose:
            print 'SQL>', sql
        cur.execute(sql)
        return cur.fetchall()[0][0]

    def execute(self, sql, values, attributes):
        cur = self.conn.cursor()

        values = filter(lambda x: x != _NO_VALUE, values)
        if self.verbose:
            print 'SQL>', sql
            print 'VALUES>', values

        r = cur.execute(sql, tuple(values))
        #if self.verbose:
        #    print 'RETURN>', r
        if _isdml(sql):
            return r
        result = []
        while 1:
            row = cur.fetchone()
            if not row:
                break
            result.append(row)
            
        desc = map(lambda x: _remTable(x), cur.description)
        if attributes is None:
            return result, desc
        return self.convertResultRows(desc, attributes, result)

    def convertResultRows(self, colnames, attributes, rows):
        newresult = []
        for row in rows:
            d = {}
            for item, col in map(None, row, colnames):
                #do date conversions here if possible (yes! - attributes)
                a = attributes[col]
                if _isDateKind(a):
                    d[col] = _dateConvertFromDB(item)
                else:
                    d[col] = item
            newresult.append(d)

        return newresult
    
    def commit(self):
        self.conn.commit()
        if self.verbose:
            print 'COMMITTING'
            
    def rollback(self):
        self.conn.rollback()
        if self.verbose:
            print 'ROLLING BACK'
            
    def postInsertUpdate(self, object, newvals, isinsert):
        pass
    
    def typeCheckAndConvert(self, val, aname, attr):
        #nulls always allowed (unless the db says no)
        if val is None: return val
        if _isDateKind(attr) and not (Date.isDateTime(val) or val is SYSDATE):
            raise TypeError,'trying to assign %s to %s and is not a date'%(
                val, aname)
            val = _dateConvertToDB(val)
        elif (_isNumber(attr) and
              not isinstance(val, types.FloatType) and
              not isinstance(val, types.IntType)):
                raise TypeError, ('trying to assign %s to %s and is not'
                                  ' a number') % (val, aname)
        elif _isString(attr) and not isinstance(val, types.StringType):
            raise TypeError, 'trying to assign %s to %s and is not a string'% (
                val, aname)
        
        return val

    def getProcedure(self, procName):
        if self.useOracleMod:
            return Oracle.getProcedure(self.realConn, procName)
        else:
            return getattr(self.getCursor().procedures, procName)

    def getCursor(self):
        return self.conn.cursor()

    def convertCursorResult(self, cursor, attrMap):
        res = cur.fetchall()
        desc = map(lambda x:x[0], cursor.description)
        return self.convertResultRows(desc, attrMap, res)
    
#so connections get rolled back on mod destruction, otherwise conns commit.
        
oraConns = []

class _modguard:
    def __init__(self):
        self.foo=oraConns
        
    def __del__(self):
        for c in self.foo:
            c.rollback()

_modguardinst = _modguard()

def _isDateKind(type):
    if type in ('TIME', 'DATETIME', 'DATE'):
        return 1

def _dateConvertFromDB(dbd):
    return DateTime.localtime(dbd)

def _dateConvertToDB(dt):
    return DCOracle.dbi.dbiDate(float(dt))

def _isNumber(attr):
    return attr == 'INTEGER'

def _isString(attr):
    return attr[:7] == 'VARCHAR' or attr[:4] == 'CHAR'

def _remTable(desc):
    desc = desc[0]
    ind = string.rfind(desc, '.')
    if ind == -1:
        return desc
    else:
        return desc[ind+1:]
