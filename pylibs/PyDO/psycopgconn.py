#########################################################################  
#  Copyright (C) 2001, 2002 Andrew T. Csillag <drew_csillag@geocities.com>
#  
#      You may distribute under the terms of either the GNU General
#      Public License or the SkunkWeb License, as specified in the
#      README file.
########################################################################

# contributed by Sean Reifschneider, based on pypgsqlconn.py by John Derrick.

"""
currently unsupported types:

 int2vector regproc tid xid cid oidvector SET smgr point
 lseg path box polygon line unknown circle money macaddr inet cidr
 aclitem bpchar bit varbit

connect args is 'host[|port]:database:user:password:opt:debug_tty'

NOTE: "cache" option is not implemented.
"""

import types
import string
import PyDBI
try:
    from mx import DateTime
except:
    import DateTime
import psycopg


def isDateTime(x):
    return isinstance (x, DateTime.DateTimeType)

def isInterval(x):
    return isinstance(x, DateTime.DateTimeDeltaType) or \
           isinstance(x, DateTime.RelativeDateTime)


class PyDOPostgreSQL:
    def __init__(self, connectArgs):
        newConnStr = ''
        connectArgs = string.split(connectArgs,':')

        #  host name
        host = None
        if connectArgs and connectArgs[0]:
            hostList = connectArgs[0].split('|')
            host = hostList[0]
            newConnStr = newConnStr + ' host=%s' % host
            if hostList > 1:
                newConnStr = newConnStr + ' port=%s' % hostList[1]
                
        #  handle trailing verbose and cache options
        if connectArgs and connectArgs[-1] == 'verbose':
            self.verbose = 1
            connectArgs = connectArgs[:-1]
        else:
            self.verbose=0
        if connectArgs and connectArgs[-1] == 'cache':
            self.useCacheMod = 1
            connectArgs = connectArgs[:-1]
        else:
            self.useCacheMod =0
        
        #  database name
        if connectArgs and len(connectArgs > 1 and connectArgs[1]:
            newConnStr = newConnStr + ' dbname=%s' % connectArgs[1]

        #  user name
        if connectArgs and len(connectArgs > 2 and connectArgs[2]:
            newConnStr = newConnStr + ' user=%s' % connectArgs[2]

        #  password
        if connectArgs and len(connectArgs > 3 and connectArgs[3]:
            newConnStr = newConnStr + ' password=%s' % connectArgs[3]

        #  remove leading space if any
        if newConnStr[0] == ' ': newConnStr = newConnStr[1:]
        self.connectArgs = newConnStr

        if host is not None:
            self.conn = PgSQL.connect(connectArgs, host = host)
        else:
            self.conn = PgSQL.connect(connectArgs)
        self.bindVariables = 0
        self.autocommit = 0

    def setAutocommit(self, flag):
        if flag:
            self.conn.autocommit()
            self.autocommit = 1
        else:
            self.conn.autocommit(0)
            self.autocommit = 0

    def isAutocommit(self):
        return self.conn.autocommit

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
                     d[desc]=item
                 elif _isTimeKind(a):
                     d[desc]=item
                 elif _isDateKind(a):
                     d[desc] = item
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
            if not isDateTime(val) and not val == PyDBI.SYSDATE:
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
        elif _isBinary(attr):
            return PgSQL.PgQuoteBytea(val, 0)
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
        return "'%s'" % dtd.strftime('%d %H:%M:%S')
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

def _isBinary(t):
    return t.upper() in ('BYTEA',)
