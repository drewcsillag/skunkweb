#  
#  Copyright (C) 2001 Andrew T. Csillag <drew_csillag@geocities.com>
#  
#      You may distribute under the terms of either the GNU General
#      Public License or the SkunkWeb License, as specified in the
#      README file.
#

import types
import Date
from Date import DateTime
import string
import MySQLdb
import PyDBI

class PyDOMySQL:
    
    def __init__(self, connectArgs):        
        verbose, cacheUser, connectParams= self.__unpackConnectArgs(connectArgs)
        self.verbose=verbose
        if cacheUser:
            import MySQL
            self.conn=MySQL.getConnection(cacheUser)
        else:
            self.conn=MySQLdb.connect(**connectParams)
        self.bindVariables = 0

    def __unpackConnectArgs(self, connectArgs):
        if type(connectArgs) in (types.StringType, types.UnicodeType):
            fields='host', 'db', 'user', 'passwd', 'cacheUser', 'verbose'
            d={}
            for k, v in zip(fields, connectArgs.split(':')):
                d[k]=v
        else:
            d=connectArgs.copy()
        if d.has_key('verbose'):
            verbose=d['verbose']
            del d['verbose']
        else:
            verbose=0
        if d.has_key('cacheUser'):
            cacheUser=d['cacheUser']
            del d['cacheUser']
        else:
            cacheUser=''
        return verbose, cacheUser, d 
    
    def getConnection(self): return self.conn

    def numberType(self, dbtype):
        dbtype = string.lower(dbtype)
        if dbtype[:4] == 'int(' or dbtype == 'integer':
            return 1
    
    def sqlStringAndValue(self, val, attr, dbtype):
        newval = self.typeCheckAndConvert(val, attr, dbtype)
        if _isString(dbtype) and not val is None:
            newval = "'" + MySQLdb.escape_string(str(newval)) + "'"
        return str(newval), None


    def getBindVariable(self):
        raise NotImplemented, 'No bind variables for mysql driver'
    
    def getAutoIncrement(self, name):
        if hasattr(self.conn, 'insert_id'):
            return self.conn.insert_id()
        # this does not seem to work any more,
        # if it ever did, but I'll keep it here
        # in case an early version of the driver needs it.
        return self.conn._db.insert_id()
    def execute(self, sql, values, attributes):
        if self.verbose:
            print 'SQL> ', sql
        cur=self.conn.cursor()
        cur.execute(sql)
        result = cur.fetchall()
        if not result and None==cur.fetchone():
            return cur.rowcount
        if attributes is None:
            return result, [x[0] for x in cur.description]
        fields = [x[0] for x in cur.description]
        return self.convertResultRows(fields, attributes, result)

    def convertResultRows(self, colnames, attributes, rows):
        newresult = []
        for row in rows:
            d = {}
            for item, desc in map(None, row, colnames):
                # do dbtype->python type conversions here
                a = attributes[desc]
                if _isDateKind(a):
                    d[desc] = _dateConvertFromDB(item)
                else:
                    d[desc] = item
            newresult.append(d)

        return newresult

    def typeCheckAndConvert(self, val, aname, attr):
        if val == None:
            return 'NULL'
            
        if _isDateKind(attr):
            if not Date.isDateTime(val) and not val == PyDBI.SYSDATE:
                raise TypeError,'trying to assign %s to %s and is not a date'%(
                    val, aname)
            val = _dateConvertToDB(val)
        elif (_isNumber(attr) and
              not isinstance(val, types.FloatType) and
              not isinstance(val, types.LongType) and
              not isinstance(val, types.IntType)):
                raise TypeError, ('trying to assign %s to %s and is not'
                                  ' a number') % (val, aname)
        elif _isString(attr) and not isinstance(val, types.StringType):
            raise TypeError, 'trying to assign %s to %s and is not a string'% (
                val, aname)
        
        return val

    #methods not needed for mysql
    def resetQuery(self): pass
    def getSequence(self, name): pass
    def postInsertUpdate(self, object, newvals, isinsert): pass
    def commit(self): pass
    def rollback(self): pass
    

def _isNumber(attr):
    attr = string.upper(attr)
    for i in ('TINYINT', 'SMALLINT', 'MEDIUMINT', 'INT', 'INTEGER',
              'BIGINT', 'REAL', 'DOUBLE', 'FLOAT', 'DECIMAL', 'NUMERIC'):
        if attr[:len(i)] == i:
            return 1

def _isString(attr):
    attr = string.upper(attr)

    for i in ('VARCHAR', 'CHAR'):
        if attr[:len(i)] == i:
            return 1
    return attr in ('TINYBLOB', 'BLOB', 'MEDIUMBLOB', 'LONGBLOB',
                    'TINYTEXT', 'TEXT', 'MEDUIMTEXT', 'LONGTEXT')
        
def _isDateKind(type):
    type = string.upper(type)
    if type in ('TIME', 'TIMESTAMP', 'DATETIME', 'DATE'):
        return 1

def _dateConvertFromDB(item):
    if item is None:
        return item
    # MySQLdb will now return DateTime objects is egenix is present.
    if type(item)==DateTime.DateTimeType:
        return item
    if string.find(item, '-') == -1: #timestamp form
        y = item[:4]
        mo = item[4:6]
        d = item[6:8]
        h = item[8:10]
        mi = item[10:12]
        s = item[12:14]
    else:
        y=item[:4]
        mo = item[5:7]
        d = item[8:10]
        h = item[11:13]
        mi = item[14:16]
        s = item[17:19]
    return DateTime.DateTime(int(y), int(mo), int(d), int(h), int(mi),
                             int(s))

def _dateConvertToDB(dt):
    if dt == PyDBI.SYSDATE:
        dt = DateTime.now()
    return '%04d%02d%02d%02d%02d%02d' % (dt.year, dt.month, dt.day,
                                         dt.hour, dt.minute, dt.second)
