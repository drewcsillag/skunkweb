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
# Time-stamp: <01/04/16 12:00:37 smulloni>

########################################################################
# a MySQL implementation

import MySQLdb
import time
from SkunkWeb.ServiceRegistry import SESSIONHANDLER
from sessionHandler.SQLSessionStore import AbstractSQLSessionStore
from SkunkWeb import Configuration
from SkunkWeb.LogObj import DEBUG

class MySQLSessionStoreImpl(AbstractSQLSessionStore):

    # number of instances of this class.  When there are some,
    # a database connection is created;
    # when there are none, the connection is closed.
    
    _instances=0
    _lastReaped=int(time.time())

    def __init__(self, id): 
        AbstractSQLSessionStore.__init__(self, id)
        MySQLSessionStoreImpl._instances=MySQLSessionStoreImpl._instances + 1
        if MySQLSessionStoreImpl._instances==1:
            self._initConnection()

    def _initConnection(self):
        try:
            MySQLSessionStoreImpl._dbconn=MySQLdb.Connect(host=self.getHost(),
                                    user=self.getUser(),
                                    passwd=self.getPass(),
                                    db=self.getDB())
        except Exception, e:
            DEBUG(SESSIONHANDLER, "could not connect to database: %s" % e)
            raise e

    def __del__(self):
        MySQLSessionStoreImpl._instances=MySQLSessionStoreImpl._instances - 1
        if MySQLSessionStoreImpl._instances==0:
            MySQLSessionStoreImpl._dbconn.close()

    def lastReaped(self, newVal=None):
        if not newVal:
            return MySQLSessionStoreImpl._lastReaped
        else:
            MySQLSessionStoreImpl._lastReaped=newVal
            
    def getHost(self):
        return Configuration.SessionHandler_MySQLHost

    def getUser(self):
        return Configuration.SessionHandler_MySQLUser

    def getPass(self):
        return Configuration.SessionHandler_MySQLPass

    def getDB(self):
        return Configuration.SessionHandler_MySQLDB

    def getTable(self):
        return Configuration.SessionHandler_MySQLTable

    def getIDCol(self):
        return Configuration.SessionHandler_MySQLIDColumn

    def getPickleCol(self):
        return Configuration.SessionHandler_MySQLPickleColumn

    def getTimeCol(self):
        return Configuration.SessionHandler_MySQLTimestampColumn
        
    def execSql(self, sql):
        try:
            cursor=MySQLSessionStoreImpl._dbconn.cursor()
            cursor.execute(sql)
            DEBUG(SESSIONHANDLER, "executed sql")
            retVal=cursor.fetchall()
            DEBUG(SESSIONHANDLER, "fetched result set")
            return retVal
        except Exception, e:
            DEBUG(SESSIONHANDLER, "exception caught: %s" % e)
            return None        
    
    def escapeSQLString(self, string):
        return MySQLdb.escape_string(string)
    
    def getGetPickleSQL(self):
        return "SELECT %(gherkin)s FROM %(table)s WHERE %(idCol)s='%(id)s'"
    
    def getSetPickleSQL(self):
        return "REPLACE INTO %(table)s SET %(idCol)s = '%(id)s', "\
               "%(pickleCol)s = '%(gherkin)s', %(timeCol)s = NULL"
    
    def getTouchSQL(self):
        return "UPDATE %(table)s SET %(timeCol)s=NULL WHERE %(idCol)s='%(id)s'" 
    
    def getDeleteSQL(self):
        return "DELETE FROM %(table)s WHERE %(idCol)s = '%(id)s'"
    
    def getReapSQL(self):
        return "DELETE FROM %(table)s WHERE DATE_SUB(NOW(), "\
               "INTERVAL %(timeout)s SECOND) > %(timeCol)s"
        
########################################################################
# $Log: MySQLSessionStore.py,v $
# Revision 1.6  2001/07/09 20:38:40  drew
# added licence comments
#
# Revision 1.5  2001/04/16 17:53:00  smullyan
# some long lines split; bug in Server.py fixed (reference to deleted
# Configuration module on reload); logging of multiline messages can now
# configurably have or not have a log stamp on every line.
#
# Revision 1.4  2001/04/02 00:54:17  smullyan
# modifications to use new requestHandler hook mechanism.
#
# Revision 1.3  2001/03/29 20:17:10  smullyan
# experimental, non-working code for requestHandler and derived services.
#
# Revision 1.2  2001/03/16 21:10:48  smullyan
# fixed reaping, which I had inadvertently broken
#
# Revision 1.1  2001/03/16 19:09:39  smullyan
# service that provides session handling capabilities.
#
########################################################################

