#
# sapdbapi.py A implementation of the Python database API 20 for SAP DB
#
#     ========== licence begin LGPL
#     Copyright (C) 2001 SAP AG
#
#     This library is free software; you can redistribute it and/or
#     modify it under the terms of the GNU Lesser General Public
#     License as published by the Free Software Foundation; either
#     version 2.1 of the License, or (at your option) any later version.
#
#     This library is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#     Lesser General Public License for more details.
#
#     You should have received a copy of the GNU Lesser General Public
#     License along with this library; if not, write to the Free Software
#     Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#     ========== licence end

import string
from exceptions import StandardError
import time
import cStringIO

try:
    import thread
    _connectionLock = thread.allocate_lock ()
except ImportError:
    class _PseudoLock:
        def acquire (self, waitflag = 0):
            pass

        def release (self):
            pass

        def locked (self):
            return None

    _connectionLock = _PseudoLock ()

import sapdb

apilevel = '2.0'

threadsafety = 1

paramstyle = 'named'

def wrapCall (call, *args):
    try:
        # print call, args
        result = apply (call, args)
        # print '==>', result
    except sapdb.SQLError, err:
        raise ProgrammingError (err)
    except sapdb.CommunicationError, err:
        raise OperationalError (err)
    return result

#
# data types
#
class _AbstractType:
    def __init__ (self, name, sqlNames):
        self.name = name
        self.sqlNames = sqlNames

    def __str__ (self):
        return self.name

    def __cmp__ (self, other):
        if other in self.sqlNames:
            return 0
        else:
            return -1

STRING = _AbstractType ('STRING',
    ['Char', 'Varchar', 'Long'])
BINARY = _AbstractType ('BINARY',
    ['Char Binary', 'Varchar Binary', 'Long Binary', 'Long byte_t'])
NUMBER = _AbstractType ('NUMBER',
    ['Integer', 'Smallint', 'Decimal', 'Fixed', 'Float'])
DATETIME = _AbstractType ('DATETIME',
    ['Date', 'Time', 'Timestamp'])
ROWID = None

#
# connection class
#
class Connection:
    def __init__ (self, user, password, database, host = '', **config):
        configList = map (lambda item: item [0] + '=' + item [1], config.items ())
        configString = string.join (configList, '&')
        try:
            _connectionLock.acquire ()
            self.__connection = wrapCall (sapdb.connect, user, password,
                database, host, configString)
        finally:
            _connectionLock.release ()
        if host:
            self.id = user + '@' + host + ':' + database
        else:
            self.id = user + '@' + database
        self.typeTranslations = None

    def close (self):
        try:
            _connectionLock.acquire ()
            if self.__connection is not None:
                wrapCall (self.__connection.release)
        finally:
            _connectionLock.release ()

    __del__ = close
    def commit (self):
        wrapCall (self.__connection.commit)

    def rollback (self):
        wrapCall (self.__connection.rollback)

    def cursor (self):
        result = Cursor (self.__connection)
        if self.typeTranslations != None:
            result.setTypeTranslation (self.typeTranslations)
        return result

    def __str__ (self):
        return '<sapdbapi.Connection ' + self.id + '>'

    def setTypeTranslation (self, transDict):
        self.typeTranslations = transDict

connect = Connection

#
#  cursor class
#
class Cursor:
    def __init__ (self, rawConnection):
        self.__connection = rawConnection
        self.description = None
        self.rowcount = -1
        self.arraysize = 1
        self.__prepared = None
        self.__lastop = None
        self.__cursor = None
        self.__typeTranslation = {}

    def close (self):
        try:
            if self.__prepared:
                self.__prepared.close ()
                self.__prepared = None
        except:
            pass
        try:
            if self.__cursor:
                self.__cursor.close ()
                self.__cursor = None
        except:
            pass
        self.__connection = None

    def __handleResult (self, result):
        if isinstance (result, sapdb.SapDB_ResultSet):
            self.__cursor = result
            self.__setDescription (result)
            if self.__typeTranslation:
                self.__instantiateTranslation ()
            result = self
        else:
            self.__cursor = None
        return result

    def __setDescription (self, cursor):
        self.description = description = []
        for i in xrange (cursor.columnCount ()):
            name, typename, size, frac = cursor.columnInfo (i)
            description.append ((name, typename, size, size, size, frac, 1))


    def __executeDirect (self, operation):
        result = self.__connection.sql (operation)
        return self.__handleResult (result)

    def __getParsed (self, operation):
        if operation and (self.__lastop != operation):
            self.__parsed = self.__connection.prepare (operation)
            self.__lastop = operation
        return self.__parsed

    def __executeParsed (self, parsed, arguments):
        return self.__handleResult (self.__parsed.execute (arguments))

    def execute (self, operation, parameters = None):
        if parameters == None:
            result = wrapCall (self.__executeDirect, operation)
        else:
            parsed = self.__getParsed (operation)
            result = wrapCall (self.__executeParsed, parsed, parameters)
        return result

    def __executemany (self, operation, seq_of_parameters):
        parsed = self.__getParsed (operation)
        for item in seq_of_parameters:
            parsed.execute (item)

    def executemany (self, operation, seq_of_parameters):
        wrapCall (self.__executemany, operation, seq_of_parameters)

    def __getCursor (self):
        result = self.__cursor
        if not result:
            exc = ProgrammingError ()
            exc.message = 'Not a cursor'
            raise exc
        return result

    def __fetchone (self):
        cursor = self.__getCursor ()
        return self.nextFromCursor (cursor)

    def fetchone (self):
        return wrapCall (self.__fetchone)

    def __fetchmany (self, arraysize):
        cursor = self.__getCursor ()
        result = []
        for i in xrange (arraysize):
            row = self.nextFromCursor (cursor)
            if not row:
                break
            result.append (row)
        return result

    def fetchmany (self, size = None):
        if size == None:
            size = self.arraysize
        return wrapCall (self.__fetchmany, size)

    def __fetchall (self):
        cursor = self.__getCursor ()
        result = []
        while 1:
            row = self.nextFromCursor (cursor)
            if not row:
                break
            result.append (row)
        return result

    def fetchall (self):
        return wrapCall (self.__fetchall)

    def setinputsizes (self, sizes):
        pass

    def setoutputsizes (self, size, column = None):
        pass

    def setTranslation (self, translatorList):
        # TODO: make sure the count equals the number of output columns
        self.__translatorList = translatorList
        self.nextFromCursor = self.__nextTranslatedFromCursor

    def __nextTranslatedFromCursor (self, cursor):
        row = cursor.next ()
        if not row:
            return None
        result = [None] * len (row)
        for i in xrange (len (row)):
            translator = self.__translatorList [i]
            if translator is None:
                result [i] = row [i]
            else:
                result [i] = translator (row [i])
        return tuple (result)

    def __nextRawFromCursor (self, cursor):
        return cursor.next ()

    nextFromCursor = __nextRawFromCursor   # untranslated is the default

    def setTypeTranslation (self, transDict):
        self.__typeTranslation.update (transDict)
        if self.__cursor:
            self.__instantiateTranslation ()

    def __instantiateTranslation (self):
        cursor = self.__cursor
        colCount = cursor.columnCount ()
        translations = [None] * colCount
        transDict = self.__typeTranslation
        for i in xrange (colCount):
            typeName = cursor.columnInfo (i) [1]
            try:
                translations [i] = transDict [typeName]
            except KeyError:
                pass
        self.setTranslation (translations)

    def callproc (self, procname, parameters = None):
        if parameters:
            questionmarks = '?' + ', ?' * (len (parameters) - 1)
        procCmd = 'call ' + procname + '(' + questionmarks + ')'
        parsed = self.__getParsed (procCmd)
        resultValues = wrapCall (parsed.execute, parameters)
        desc = parsed.getDescription ()
        resultIndex = 0
        for paramIndex in xrange (len (desc)):
            if desc [paramIndex] [-1] in ['OUT', 'INOUT']:
                parameters [paramIndex] = resultValues [resultIndex]
                resultIndex = resultIndex + 1

#
# exception classes
#
class Error (StandardError):
    __internalException = None
    def __init__ (self, exception = None):
        StandardError.__init__ (self)
        if exception:
            self.__dict__.update (exception.__dict__)
            self.__internalException = exception

    def __str__ (self):
        if self.__internalException:
            return str (self.__internalException)
        else:
            return StandardError.__str__ (self)

class DatabaseError (Error):
    pass

class OperationalError (DatabaseError):
    pass

class ProgrammingError (DatabaseError):
    pass

#
# input conversions
#

def Date (year, month, day):
    return "%04d%02d%02d" % (year, month, day)

def Time (hour, minute, second):
    return "%04d%02d%02d" % (hour, minute, second)

def Timestamp (year, month, day, hour, minute, second, micros = 0):
    return "%04d%02d%02d%02d%02d%02d%06d" % (year, month, day, hour, minute, second, micros)

def DateFromTicks (ticks):
    return apply (Date, time.localtime (ticks) [:3])

def TimeFromTicks (ticks):
    return apply (Time, time.localtime (ticks) [3:6])

def TimestampFromTicks (ticks):
    return apply (Timestamp, time.localtime (ticks) [:6])


def Binary (data):
    return cStringIO.StringIO (data)

#
# output conversions
#
# Date: YYYYMMDD
# Time: 00HHMMSS
# Timestamp: YYYYMMDDHHMMSSmmmmmm

def dateTuple (sapdbDate):
    if sapdbDate is None:
        return None
    return int (sapdbDate[:4]), int (sapdbDate[4:6]), int (sapdbDate[6:])

def timeTuple (sapdbTime):
    if sapdbTime is None:
        return None
    return int (sapdbTime[2:4]), int (sapdbTime[4:6]), int (sapdbTime[6:])

def timestampTuple (sapdbTimestamp):
    if sapdbTimestamp is None:
        return None
    return time.localtime (timestampVal (sapdbTimestamp))

tupleTranslation = {
    'Date': dateTuple,
    'Time': timeTuple,
    'Timestamp': timestampTuple,
}

def dateVal (sapdbDate):
    if sapdbDate is None:
        return None
    year, month, day = dateTuple (sapdbDate)
    return time.mktime ((year, month, day, -1, -1, -1, -1, -1, -1,))

def timeVal (sapdbTime):
    if sapdbTime is None:
        return None
    hour, minute, second = timeTuple (sapdbTime)
    return time.mktime ((1970, 1, 2, hour, minute, second, -1, -1, -1,))

def timestampVal (sapdbTimestamp):
    if sapdbTimestamp is None:
        return None
    year = int (sapdbTimestamp [:4])
    month = int (sapdbTimestamp [4:6])
    day = int (sapdbTimestamp [6:8])
    hour = int (sapdbTimestamp [8:10])
    minute = int (sapdbTimestamp [10:12])
    second = int (sapdbTimestamp [12:14])
    micros = int (sapdbTimestamp [14:])
    return time.mktime ((year, month, day, hour, minute, second, -1, -1, -1,))


valTranslation = {
    'Date': dateVal,
    'Time': timeVal,
    'Timestamp': timestampVal,
}

class AbstractTimeFormat:
    def __init__ (self, fmt):
        self.fmt = fmt

    def __call__ (self, sapdbString):
        localtime = time.localtime ( self.toTime(sapdbString))
        return time.strftime (self.fmt, localtime)

class DateFormat (AbstractTimeFormat):
    def toTime (self, sapdbDate):
        return dateVal (sapdbDate)

class TimeFormat (AbstractTimeFormat):
    def toTime (self, sapdbTime):
        return timeVal (sapdbTime)

class TimestampFormat (AbstractTimeFormat):
    def toTime (self, sapdbTimestamp):
        return timestampVal (sapdbTimestamp)

