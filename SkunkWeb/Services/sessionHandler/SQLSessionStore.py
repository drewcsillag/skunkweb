#  
#  Copyright (C) 2001 Jacob Smullyan <smulloni@smullyan.org>
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
# $Author: drew $
# $Revision: 1.6 $
# $Id: SQLSessionStore.py,v 1.6 2001/07/09 20:38:40 drew Exp $
# Time-stamp: <01/04/01 20:52:07 smulloni>
########################################################################

from SkunkWeb.LogObj import DEBUG
import Session
from Session import SessionStore
from SkunkWeb import Configuration
import cPickle
import time
from SkunkWeb.ServiceRegistry import SESSIONHANDLER

########################################################################
# abstract session store implementation that uses a SQL database.

class AbstractSQLSessionStore(SessionStore): 
    '''
    an implementation of a session store which
    is backed with a common or garden variety SQL database which supports blobs.
    The table should look something like this MySQL table:

    +------------+---------------+------+-----+---------+-------+
    | Field      | Type          | Null | Key | Default | Extra |
    +------------+---------------+------+-----+---------+-------+
    | id         | varchar(40)   |      | PRI |         |       |
    | pickle     | longblob      |      |     |         |       |
    | accessTime | timestamp(14) | YES  |     | NULL    |       |
    +------------+---------------+------+-----+---------+-------+

    which can be created (in MySQL) with this statement:
    CREATE TABLE Sessions (id VARCHAR(40) PRIMARY KEY, pickle LONGBLOB NOT NULL, accessTime TIMESTAMP);

    The entire session dictionary is inserted as one pickled blob. 

    To write a concrete SQLSessionStore:

    * implement the getHost(), getUser(), getPass(), getDB(), getTable(), getIDCol(), getPickleCol(),
    and getTimeCol() methods to obtain configurable information about the DB in question.

    * implement the execSql() method to actually execute SQL and return a result set.
    A two-dimensional list is expected.

    *implement escapeSQLString() to escape strings literals inside of SQL.

    * implement the getGetPickleSQL(), getSetPickleSQL(), getReapSQL(), getTouchSQL,
    and getDeleteSQL() methods to specify the SQL needed for the database in question.
    Each of these methods should return a string in which the appropriate column names
    and values are interpolated by keyword.  See the docstrings of the relevant methods
    for which keywords are available.

    * add code to initialize and manage the database connection.

    * if setPickle cannot be performed in one SQL statement with your database,
    override save().

    * implemented lastReaped(), which should be an accessor method is no value is passed to it,
    and a mutator if one is.
    '''
       
    def getHost(self):
        raise NotImplementedError

    def getUser(self):
        raise NotImplementedError

    def getPass(self):
        raise NotImplementedError

    def getDB(self):
        raise NotImplementedError

    def getTable(self):
        raise NotImplementedError

    def getIDCol(self):
        raise NotImplementedError

    def getPickleCol(self):
        raise NotImplementedError

    def getTimeCol(self):
        raise NotImplementedError
        
    def execSql(self, sql):
        raise NotImplementedError

    def escapeSQLString(self, string):
        raise NotImplementedError

    def __init__(self, id):
        self.__id=id 

    def getTouchSQL(self):
        """
        SQL to update the timestamp for a given session id.
        keywords available:
        'table' : the table
        'timeCol' : the time column
        'idCol' : the id column
        'id' : the session id
        """
        raise NotImplementedError
    
    def touch(self):
        """
        resets the timestamp for the session's corresponding record,
        and, if reaping is enabled, removes any expired records
        from the database if the reap interval has elapsed since the last reap.
        """
        DEBUG(SESSIONHANDLER, "in touch")
        args={'table' : self.getTable(),
              'timeCol' : self.getTimeCol(), 
              'idCol' : self.getIDCol(), 
              'id' : self.__id}
        self.execSql(self.getTouchSQL() % args)
        self._checkReap()        

    def getGetPickleSQL(self):
        """
        SQL to obtain the pickled session information for a given id.
        keywords available:
        'table' : the table
        'idCol' : the id column
        'id' : the session id
        'gherkin' : the pickle-data column
        """
        raise NotImplementedError
    
    def __getPickle(self):
        args={'table' : self.getTable(),
              'idCol' : self.getIDCol(), 
              'id' : self.__id,
              'gherkin' : self.getPickleCol()}
        resultSet=self.execSql(self.getGetPickleSQL() % args)
        if resultSet and len(resultSet)>0 and len(resultSet[0])>0:
            return cPickle.loads(resultSet[0][0])
        else:
            return None

    def getSetPickleSQL(self):
        """
        SQL to insert pickled session data for a given id.
        keywords available:
        'id' : the session id
        'idCol' : the id column
        'pickleCol' : the pickle column
        'gherkin' : SQL-escaped pickled session information
        'timeCol' : the timestamp column
        'table' : the table
        """
        raise NotImplementedError

    def __setPickle(self, sessionHash):
        DEBUG(SESSIONHANDLER, "in __setPickle with sessionHash %s" % sessionHash)
        args={'id' : self.__id,
              'idCol' : self.getIDCol(),
              'pickleCol' : self.getPickleCol(),
              'gherkin' : self.escapeSQLString(cPickle.dumps(sessionHash, 1)),
              'timeCol' : self.getTimeCol(),
              'table': self.getTable()}
        self.execSql(self.getSetPickleSQL() % args)

    def load(self):
        self._checkReap()
        return self.__getPickle() or {}

    def save(self, data):
        self.__setPickle(data)
        # check if it is time to reap
        self._checkReap()

    def getDeleteSQL(self):
        """
        SQL to delete session data for a given id.
        keywords available:
        'id' : session id
        'idCol' : the id column
        'table' : the table
        """
        raise NotImplementedError
        
    def delete(self):
        DEBUG(SESSIONHANDLER, "in delete")
        args={'id' : self.__id,
              'idCol' : self.getIDCol(),
              'table' : self.getTable()}        
        self.execSql(self.getDeleteSQL() % args)

    def _checkReap(self):
        DEBUG(SESSIONHANDLER, "in _checkReap")
        DEBUG(SESSIONHANDLER, "reap interval is %d" % Session._reapInterval)
        DEBUG(SESSIONHANDLER, "last reaped: %d" % self.lastReaped())
        if Session._reapInterval>0:
            currentTime=int(time.time())
            if currentTime>=(self.lastReaped() + Session._reapInterval):
                self.reapOldRecords()
                self.lastReaped(currentTime)

    def getReapSQL(self):
        """
        SQL to remove expired session records
        keywords available:
        'timeCol' : timestamp column
        'table' : the table
        'timeout' : the session timeout
        """
        raise NotImplementedError

    def reapOldRecords(self):
        DEBUG(SESSIONHANDLER, "in reapOldRecords")
        args={'timeCol' : self.getTimeCol(),
              'timeout' : Session._timeout,
              'table' : self.getTable()}      
        self.execSql(self.getReapSQL() % args)

    def lastReaped(self, newVal=None):
        raise NotImplementedError

########################################################################        
# $Log: SQLSessionStore.py,v $
# Revision 1.6  2001/07/09 20:38:40  drew
# added licence comments
#
# Revision 1.5  2001/04/02 00:54:17  smullyan
# modifications to use new requestHandler hook mechanism.
#
# Revision 1.4  2001/03/29 20:17:11  smullyan
# experimental, non-working code for requestHandler and derived services.
#
# Revision 1.3  2001/03/16 21:20:18  smullyan
# removed dead variable, _lastReaped, from SQLSessionStore
#
# Revision 1.2  2001/03/16 21:10:48  smullyan
# fixed reaping, which I had inadvertently broken
#
# Revision 1.1  2001/03/16 19:09:40  smullyan
# service that provides session handling capabilities.
#
########################################################################

