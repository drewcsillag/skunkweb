#  
#  Copyright (C) 2001 Jacob Smullyan <smulloni@smullyan.org>
#  
#      You may distribute under the terms of either the GNU General
#      Public License or the SkunkWeb License, as specified in the
#      README file.
#   
# Time-stamp: <03/05/19 09:37:50 smulloni>

########################################################################
# a MySQL implementation

import MySQLdb
from sessionHandler.SQLSessionStore import AbstractSQLSessionStore, reap_main
from SkunkWeb import Configuration
import MySQL
import sys
import getopt

class Store(AbstractSQLSessionStore):

    def getConnection(self):
        return MySQL.getConnection(Configuration.SessionHandler_MySQLAlias)

    def escapeSQLString(self, string):
        return MySQLdb.escape_string(string)



    
        
