#  
#  Copyright (C) 2001 Jacob Smullyan <smulloni@smullyan.org>
#  
#      You may distribute under the terms of either the GNU General
#      Public License or the SkunkWeb License, as specified in the
#      README file.
#   
# $Id: SQLSessionStore.py,v 1.3 2003/07/18 18:28:26 smulloni Exp $
# Time-stamp: <01/04/01 20:52:07 smulloni>
########################################################################

from SkunkWeb.LogObj import DEBUG
from SkunkWeb.ServiceRegistry import SESSIONHANDLER
import Session
from SkunkWeb import Configuration
import cPickle
import time

########################################################################
# abstract session store implementation that uses a SQL database.

class AbstractSQLSessionStore(Session.SessionStore): 
    """

    an implementation of a session store which is backed with a common
    or garden variety SQL database which supports blobs.  The table
    should look something like this MySQL table:

    +------------+---------------+------+-----+---------+-------+
    | Field      | Type          | Null | Key | Default | Extra |
    +------------+---------------+------+-----+---------+-------+
    | id         | varchar(40)   |      | PRI |         |       |
    | pickle     | longblob      |      |     |         |       |
    | accessTime | timestamp(14) | YES  |     | NULL    |       |
    +------------+---------------+------+-----+---------+-------+

    which can be created (in MySQL) with this statement:

    CREATE TABLE Sessions (
      id VARCHAR(40) PRIMARY KEY,
      pickle LONGBLOB NOT NULL,
      accessTime TIMESTAMP
    );

    The entire session dictionary is inserted as one pickled blob. 

    To write a concrete SQLSessionStore:

    * implement escapeSQLString() to escape strings literals inside of
    SQL.  (This approach is taken so that we don't need to know the
    escaping style of any particular driver.)

    * Shadow as appropriate the following class attributes:
        
        * getPickleSQL
        * setPickleSQL
        * reapSQL 
        * touchSQL
        * deleteSQL
        * ageSQL
        
    to specify the SQL needed for the database in question.

    * if setPickle cannot be performed in one SQL statement with your database,
    override save().

    * implement getConnection(), return a database connection object.

    """

    getPickleSQL="SELECT %(gherkin)s, %(timeCol)s FROM %(table)s WHERE %(idCol)s='%(id)s'"

    setPickleSQL=("REPLACE INTO %(table)s "\
                  "%(pickleCol)s = '%(gherkin)s', %(timeCol)s = NULL"\
                  "WHERE %(idCol)s = '%(id)s' ")

    touchSQL="UPDATE %(table)s SET %(timeCol)s=NULL WHERE %(idCol)s='%(id)s'" 

    deleteSQL="DELETE FROM %(table)s WHERE %(idCol)s = '%(id)s'"

    reapSQL="DELETE FROM %(table)s WHERE DATE_SUB(NOW(), "\
             "INTERVAL %(timeout)s SECOND) > %(timeCol)s"

    ageSQL="SELECT %(timeCol)s FROM %(table)s WHERE %(idCol)s=%(id)s"
    
    def getConnection(self):
        raise NotImplementedError

    def execSql(self, sql, args=None):
        try:
            db=self.getConnection()
            cursor=db.cursor()
            cursor.execute(sql, args)
            retval=cursor.fetchall()
            cursor.close()
            db.commit()
            return retval
        except Exception, e:
            DEBUG(SESSIONHANDLER, "sql exception -- see error log")
            logException()
            try:
                db.rollback()
            except:
                pass

    def escapeSQLString(self, string):
        raise NotImplementedError

    def __init__(self,
                 id):
        self.__id=id
        self.table=Configuration.SessionHandler_SQLTable
        self.idCol=Configuration.SessionHandler_SQLIDColumn
        self.pickleCol=Configuration.SessionHandler_SQLPickleColumn
        self.timeCol=Configuration.SessionHandler_SQLTimestampColumn
        self._touched=int(time.time())
        
##        # for reaping to work correctly with scoping, it needs
##        # to be keyed to the configuration values above
##        self._reapKey='|'.join(self.table,
##                               self.idCol,
##                               self.pickleCol,
##                               self.timeCol)
##        try:
##            self.__class__._lastReaped
##        except AttributeError:
##            self.__class__._lastReaped={self._reapKey: int(time.time())}
##        else:
##            try:
##                self.__class__._lastReaped[self._reapKey]
##            except KeyError:
##                self.__class__._lastReaped[self._reapKey]=int(time.time())}
        
    
    def touch(self):
        """
        resets the timestamp for the session's corresponding record.
        """
        DEBUG(SESSIONHANDLER, "in touch")
        args={'table' : self.table,
              'timeCol' : self.timeCol, 
              'idCol' : self.idCol, 
              'id' : self.__id}
        self.execSql(self.touchSQL % args)
        self._touched=int(time.time())

    def _getPickle(self):
        args={'table' : self.table,
              'idCol' : self.idCol,
              'timeCol' : self.timeCol,
              'id' : self.__id,
              'gherkin' : self.pickleCol}
        resultSet=self.execSql(self.getPickleSQL % args)
        if resultSet and resultSet[0]:
            gherkin, tstamp=resultSet[0]
            self._touched=tstamp
            return cPickle.loads(gherkin)
        else:
            self._touched=int(time.time())
            return {}

    def _setPickle(self, sessionHash):
        args={'id' : self.__id,
              'idCol' : self.idCol,
              'pickleCol' : self.pickleCol,
              'gherkin' : self.escapeSQLString(cPickle.dumps(sessionHash, 1)),
              'timeCol' : self.timeCol,
              'table': self.table}
        self.execSql(self.setPickleSQL % args)
        self._touched=int(time.time())

    def load(self):
        return self._getPickle()

    def save(self, data):
        self._setPickle(data)
##        # check if it is time to reap
##        self._checkReap()

        
    def delete(self):
        DEBUG(SESSIONHANDLER, "in delete")
        args={'id' : self.__id,
              'idCol' : self.idCol,
              'table' : self.table}        
        self.execSql(self.deleteSQL % args)
        self._touched=int(time.time())

##    def _checkReap(self):
##        DEBUG(SESSIONHANDLER, "in _checkReap")
##        DEBUG(SESSIONHANDLER, "reap interval is %d" % Session._reapInterval)
##        if Session._reapInterval>0:
##            currentTime=int(time.time())
##            if currentTime>=(self.getLastReaped() + Session._reapInterval):
##                self.reapOldRecords()
##                self.setLastReaped(currentTime)

##    def reapOldRecords(self):
##        DEBUG(SESSIONHANDLER, "in reapOldRecords")
##        args={'timeCol' : self.timeCol,
##              'timeout' : Session._timeout,
##              'table' : self.table}      
##        self.execSql(self.reapSQL % args)

##    def getLastReaped(self):
##        return self.__class__._lastReaped[self._reapKey]

##    def setLastReaped(self, newval):
##        self.__class__._lastReaped[self._reapKey]=newval

    def lastTouched(self):
        return self._touched

    
##        currentTime=int(time.time())
##        args={'id' : self.__id,
##              'idCol' : self.idCol,
##              'timeCol' : self.timeCol,
##              'table' : self.table}
##        retval=self.execSql(self.ageSQL % args)
##        if retval and retval[0]:
##            return currentTime-retval[0][0]
##        else:
##            return 0

    def reap(self):
        DEBUG(SESSIONHANDLER, "in reap()")
        args={'timeCol' : self.timeCol,
              'timeout' : Session._timeout,
              'table' : self.table}      
        self.execSql(self.reapSQL % args)
