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
from mx import DateTime
import string
from PyDO import SYSDATE #circular import ok, since we're loaded after PyDO
import sapdbapi
import sapdb
from string import split

class _NO_VALUE: pass

def _isdml(sql):
    if sql[:7] in ('UPDATE ', 'DELETE ', 'INSERT '):
        return 1
    
class PyDOsapdb:
    """PyDBI - PyDO sapdb driver"""
    def __init__(self, connectString):
        self.connectString = connectString
        user,pwd,dbname,host,self.verbose = self._parseConnectString(connectString)
        self.realConn = (user,pwd,dbname,host)
        self.conn = sapdbapi.connect(user,pwd,dbname,host,timeout="0")
        self.bvcount = 0
        self.bindVariables = 1
        if self.verbose:
            print 'CONNECTED'
        
    def _parseConnectString(self, s):
        bits = string.split(s, '|')
        verbose = 0
        items = split(bits[0])
        if not items: raise ValueError,"Invalid connection string"
        db_host, items = items[0], items[1:]
        if '@' in db_host:
            db, host = split(db_host,'@',1)
            database = db
        else:
            database = db_host
	user, items = items[0], items[1:]
        password, items = items[0], items[1:]

        if len(bits) == 1:
	    return user,password,database,host,0
	else:
            if bits[1] == 'verbose':
                verbose = 1
	    return user,password,database,host,verbose

    def getConnection(self):
        return self.conn

    def sqlStringAndValue(self, val, attr, dbtype):
        if val == SYSDATE:
            return 'SYSDATE', _NO_VALUE
        if Date.isDateTime(val):
            val = _dateConvertToDB(val)
        # if string.upper(dbtype) == "LONG RAW":
        #    val = sapdbapi.dbi.dbiRaw(val)
        self.bvcount = self.bvcount + 1
        return '?', val

    def getBindVariable(self):
        self.bvcount = self.bvcount + 1
        return '?'

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
                if _isLongKind(a) and item is not None:
                   item = _longConvertFromDB(item)
		elif _isDateKind(a):
		   item = _dateConvertFromDB(item,a)
		
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
        if _isDateKind(attr):
	    if not (Date.isDateTime(val) or val is SYSDATE):
		val = DateTime.DateTimeFrom(val)
	    val = _dateConvertToDB(val,attr)
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
        pass

    def getCursor(self):
        return self.conn.cursor()

    def convertCursorResult(self, cursor, attrMap):
        res = cur.fetchall()
        desc = map(lambda x:x[0], cursor.description)
        return self.convertResultRows(desc, attrMap, res)
    
#so connections get rolled back on mod destruction, otherwise conns commit.
        
def _isDateKind(type):
    if type in ['Date','Time','Timestamp']:
        return 1
	
def _dateConvertToDB(val,attr):
    if attr == 'Date':
        return sapdbapi.Date(val.year,val.month,val.day)
    elif attr == 'Time':
        return sapdbapi.Time(val.hour,val.minute,val.second)
    elif attr == 'Timestamp':
        return sapdbapi.Timestamp(val.year,val.month,val.day,val.hour,val.minute,val.second)

    
def _dateConvertFromDB(val,type):
    return DateTime.DateTimeFrom(sapdbapi.valTranslation[type](val))

def _isNumber(attr):
    if attr in ['Integer','Smallint'] or attr[:4] == 'Float' or attr[:5] == 'Fixed':
        return 1
    
def _isLongKind(attr):
    if attr == 'Long':
        return 1

def _longConvertFromDB(val):
    ret = ''
    while 1:
        d = val.read(1000)
	if len(d) == 0:
	    break
	ret = ret + d
    return ret

def _isString(attr):
    return attr[:7] == 'Varchar' or attr[:4] == 'Char'

def _remTable(desc):
    desc = desc[0]
    ind = string.rfind(desc, '.')
    if ind == -1:
        return desc
    else:
        return desc[ind+1:]
