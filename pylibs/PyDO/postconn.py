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

 bool bytea int2vector regproc tid xid cid oidvector SET smgr point
 lseg path box polygon line unknown circle money macaddr inet cidr
 aclitem bpchar bit varbit

connect args is 'host:database:user:password:opt:debug_tty'

field names should be in lower case!
"""

import types
import string
import PyDBI
import Date
import DateTime
import pgdb


class PyDOPostgreSQL:
    def __init__(self, connectArgs):
        connectArgs = string.split(connectArgs,':')
        if connectArgs and connectArgs[-1] == 'verbose':
            self.verbose = 1
            connectArgs = connectArgs[:-1]
            #connectArgs = string.join(connectArgs[:-1], ':')
        else:
            #connectArgs = string.join(connectArgs, ':')
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
            PostgreSql.getConnection(connectArgs)
        else:
            self.conn = pgdb.connect(connectArgs)
        self.bindVariables = 0

    def getConnection(self):
        return self.conn

    def sqlStringAndValue(self, val, attr, dbtype):
        newval = self.typeCheckAndConvert(val, attr, dbtype)
        if _isString(dbtype):
            newval = "'" + _escape(str(newval)) + "'"
        return str(newval), None

    def getBindVariable(self):
        raise NotImplemented, 'No bind variables for postgresql driver'

    def execute(self, sql, values, attributes):
        if self.verbose:
            print 'SQL>', sql
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
                a = attributes[desc]
                if _isDateKind(a):
                    d[desc] = _dateConvertFromDB(item)
                elif _isNumber(a):
                    if a in ('FLOAT4', 'FLOAT8'):
                        f = float
                    else:
                        f = lambda x: int(float(x))
                    d[desc] = f(item)
                else:
                    d[desc] = item
            newresult.append(d)

        return newresult

    def typeCheckAndConvert(self, val, aname, attr):
        if _isDateKind(attr):
            if (not Date.isDateTime(val)) and not val == PyDBI.SYSDATE:
                raise TypeError,'trying to assign %s to %s and is not a date, being of type %s ' %  (val,
                                                                                                     aname,
                                                                                                     type(val))
            val = _dateConvertToDB(val)
        elif _isNumber(attr):
            if attr in ('FLOAT4', 'FLOAT8'):
                f = float
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
                return '1=1'
            else:
                return '0=1'
        return val

    def getSequence(self, name):
        cur = self.conn.cursor()
        sql = "select nextval('%s')" % name
        if self.verbose:
            print 'SQL>', sql
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

def _dateConvertFromDB(d):    
    try: return DateTime.strptime(d, '%Y-%m-%d') #just Y/M/D
    except: pass
    
    try: return DateTime.strptime(d, '%H:%M:%S') #just hh:mm:ss
    except: pass

    dashind = string.rindex(d, '-')
    tz = d[dashind:]
    d = d[:dashind]
    try: return DateTime.strptime(d, '%H:%M:%S'), tz # timetz
    except: pass
    # NO -- it was already stripped off, above!  -- js Thu Aug  9 11:51:23 2001
    #strip off offset from gmt
    #d = d[:string.rindex(d, '-')]
    try:
        return DateTime.strptime(d, '%Y-%m-%d %H:%M:%S') # full date
    except: 
        #print "date passed to convert function: |%s|" % d
        raise
    

def _dateConvertToDB(d):
    if not Date.isDateTime(d) and d == PyDBI.SYSDATE:
        return "'now'"
    return "'" + str(d)[:-3] + "'"

def _isNumber(t):
    return string.upper(t) in (
        'OID', 'DECIMAL', 'FLOAT4', 'FLOAT8', 'INT2', 'INT4', 'INT8',
        'NUMERIC')

def _isString(t):
    pfx = string.split(t, '(')[0]
    return string.upper(pfx) in (
        'CHAR', 'TEXT', 'VARCHAR', 'NAME')
