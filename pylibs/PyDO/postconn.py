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

"""
currently unsupported PostgreSql types:

 bytea int2vector regproc tid xid cid oidvector SET smgr point
 lseg path box polygon line unknown circle money macaddr inet cidr
 aclitem bpchar bit varbit

connect args is 'host[|port]:database:user:password:opt:debug_tty'

field names should be in lower case!
"""

import types
import string
import PyDBI
try:
    from mx import DateTime
except:
    import DateTime
import pgdb


def isDateTime(x):
    return isinstance ( x, DateTime.DateTimeType )

def isInterval(x):
    return isinstance(x, DateTime.DateTimeDeltaType) or \
           isinstance(x, DateTime.RelativeDateTime)


class PyDOPostgreSQL:
    def __init__(self, connectArgs):
        connectArgs = string.split(connectArgs,':')
        host = None
        if connectArgs and connectArgs[0]: #if host is there
            if '|' in connectArgs[0]: #if specified port
                host = connectArgs[0].replace('|', ':')
                
        if connectArgs and connectArgs[-1] == 'verbose':
            self.verbose = 1
            connectArgs = connectArgs[:-1]
        else:
            self.verbose=0
        if connectArgs and connectArgs[-1] == 'cache':
            self.useCacheMod = 1
            connectArgs = string.join(connectArgs[:-1], ':')
        else:
            connectArgs = string.join(connectArgs, ':')
            self.useCacheMod =0
        
        self.connectArgs = connectArgs
        if self.useCacheMod:
            import PostgreSql
            self.conn = PostgreSql.getConnection(connectArgs)
        else:
            if host is not None:
                self.conn = pgdb.connect(connectArgs, host = host)
            else:
                self.conn = pgdb.connect(connectArgs)
        self.bindVariables = 0

    def getConnection(self):
        return self.conn

    def sqlStringAndValue(self, val, attr, dbtype):
        newval = self.typeCheckAndConvert(val, attr, dbtype)
        if _isString(dbtype) and not val == None:
            newval = "'" + _escape(str(newval)) + "'"
        return str(newval), None

    def getBindVariable(self):
        raise NotImplemented, 'No bind variables for postgresql driver'

    def execute(self, sql, values, attributes):
        if self.verbose:
            print 'SQL> ', sql
        cur = self.conn.cursor()
        cur.execute(sql)
        try:
            result = cur.fetchall()
        except:
            return 1
        fields = cur.description
        fields = map(lambda x:x[0], fields)
        if attributes is None:
            return result, fields
        return self.convertResultRows(fields, attributes, result)

    def convertResultRows(self, colnames, attributes, rows):
         newresult = []
         for row in rows:
             d = {}
             for item, desc in map(None, row, colnames):
                 #do dbtype->python type conversions here
                 a = attributes[desc].upper()
                 if _isIntervalKind(a):
                     d[desc]=_intervalConvertFromDB(item)
                 elif _isTimeKind(a):
                     d[desc]=_timeConvertFromDB(item)
                 elif _isDateKind(a):
                     d[desc] = _dateConvertFromDB(item)
                 elif _isNumber(a) and not item is None:
                     if a in ('FLOAT4', 'FLOAT8'):
                         f = float
                     elif a == 'INT8':
                         f = lambda x: long(float(x))
                     else:
                         f = lambda x: int(float(x))
                     d[desc] = f(item)
                 else:
                     d[desc] = item
             newresult.append(d)

         return newresult

    def typeCheckAndConvert(self, val, aname, attr):
        if val == None:
            val = "NULL"
        elif _isIntervalKind(attr):
            if not isInterval(val):
                raise TypeError, (
                    'trying to assign %s to %s and is not an interval , '\
                    'being of type %s '
                    ) %  (val, aname, type(val))
            val=_intervalConvertToDB(val)
        elif _isTimeKind(attr):
            if not isDateTime(val) and not val ==PyDBI.SYSDATE:
                raise TypeError, (
                    'trying to assign %s to %s and is not a time, '\
                    'being of type %s '
                    ) %  (val, aname, type(val))
            val = _timeConvertToDB(val)
        elif _isDateKind(attr):
            if (not isDateTime(val)) and not val == PyDBI.SYSDATE:
                raise TypeError,(
                    'trying to assign %s to %s and is not a date, '\
                    'being of type %s '
                    ) %  (val, aname, type(val))
            val = _dateConvertToDB(val)
        elif _isNumber(attr):
            if attr in ('FLOAT4', 'FLOAT8'):
                f = float
            elif attr in ('BIGINT', 'INT8'):
                f = lambda x: long(x)
            else:
                f = lambda x: int(float(x))
            try:
                return f(val)
            except:
                raise TypeError, ('trying to assign %s to %s and is not'
                                  ' a number') % (val, aname)
        elif _isString(attr) and not isinstance(val, types.StringType):
            raise TypeError, 'trying to assign %s to %s and is not a string'% (
                val, aname)
        elif attr.upper() == 'BOOL':
            if val:
                return 'TRUE'
            else:
                return 'FALSE'
        return val

    def getSequence(self, name):
        cur = self.conn.cursor()
        sql = "select nextval('%s')" % name
        if self.verbose:
            print 'SQL> ', sql
        cur.execute(sql)
        return cur.fetchall()[0][0]
        
    def commit(self):
        self.conn.commit()
        
    def rollback(self):
        self.conn.rollback()
    
    #methods not needed for postgresql
    def getAutoIncrement(self, name): pass
    def resetQuery(self): pass
    def postInsertUpdate(self, object, newvals, isinsert): pass

def _escape(s):
    return string.replace(s, "'", "\\'")

def _isDateKind(t):
    return string.upper(t) in (
        'TIMESTAMP', 'INTERVAL', 'DATE', 'TIME', 'ABSTIME', 'RELTIME',
        'TINTERVAL')

def _isTimeKind(t):
    return t.upper() in ('TIME', 'TIMETZ')

def _isIntervalKind(t):
    return string.upper(t) in ('INTERVAL', 'TINTERVAL')

def _dateConvertFromDB(d):
    if d==None:
        return None
    for format in ('%Y-%m-%d', #  Y/M/D
                   '%H:%M:%S', #  hh:mm:ss
                   '%H:%M',    #  hh:mm
                   '%Y-%m'):   #  Y-M
        try:
            return DateTime.strptime(d, format)
        except:
            pass
    dashind = max(d.rfind('-'), d.rfind('+'))
    tz = d[dashind:]
    d = d[:dashind]

    #maybe it has a miliseconds ?
    dotind = string.rfind(d, '.')
    if dotind > 0:
        d = d[:dotind]

    try:
        return DateTime.strptime(d, '%H:%M:%S'), tz # timetz
    except:
        pass
    if 1:#try:
        # why is tz returned above and not here?
        return DateTime.strptime(d, '%Y-%m-%d %H:%M:%S') # full date
    #except: 
    #    pass


def _timeConvertFromDB(t):
    if t==None:
        return None
    for format in ('%H:%M:%S',
                   '%H:%M'):
        try:
            return DateTime.strptime(t, format)
        except:
            pass
    raise DateTime.Error, "could not parse time: %s" % t

def _intervalConvertFromDB(i):
    if i==None:
        return None
    # this is actually rather tricky; I need to be able to return
    # a RelativeDateTime
    raise NotImplementedError 

def _dateConvertToDB(d):
    if not isDateTime(d) and d == PyDBI.SYSDATE:
        return "'now'"
    return "'" + str(d)[:-3] + "'"

def _timeConvertToDB(dt):
    if dt == PyDBI.SYSDATE:
        return "CURRENT_TIME";
    return "'%s'" % dt.strftime('%H:%M:%S')

def _intervalConvertToDB(dtd):
    if isinstance(dtd, DateTime.DateTimeDeltaType):
        return "'%s'" % dtd.strftime('%d:%H:%M:%S')
    else:
        return str(dtd)

def _isNumber(t):
    return string.upper(t) in (
        'OID', 'DECIMAL', 'FLOAT4', 'FLOAT8', 'INT2', 'INT4', 'INT8',
        'NUMERIC', 'BIGINT', 'SMALLINT')

def _isString(t):
    pfx = string.split(t, '(')[0]
    return string.upper(pfx) in (
        'BPCHAR', 'CHAR', 'TEXT', 'VARCHAR', 'NAME', 'ISBN', 'ISSN')
