#  
#  Copyright (C) 2001 Jacob Smullyan <smulloni@smullyan.org>
#  
#      You may distribute under the terms of either the GNU General
#      Public License or the SkunkWeb License, as specified in the
#      README file.
#   
# Time-stamp: <03/07/19 13:10:05 smulloni>

########################################################################
# a MySQL implementation

import MySQLdb
from sessionHandler.SQLSessionStore import AbstractSQLSessionStore
from SkunkWeb import Configuration
import MySQL



class Store(AbstractSQLSessionStore):

    def getConnection(self):
        return MySQL.getConnection(Configuration.SessionHandler_MySQLAlias)

    def escapeSQLString(self, string):
        return MySQLdb.escape_string(string)

    def marshalTimeStamp(self, tstamp):
        return tstamp.ticks()

MySQLSessionStoreImpl=Store

    
        
