#  
#  Copyright (C) 2001 Jacob Smullyan <smulloni@smullyan.org>
#  
#      You may distribute under the terms of either the GNU General
#      Public License or the SkunkWeb License, as specified in the
#      README file.
#   
# Time-stamp: <03/07/18 19:05:39 smulloni>
########################################################################

import cPickle
from sessionHandler.Session import SessionStore
from SkunkWeb import Configuration
import PyPgSQLcache
from pyPgSQL.PgSQL import _quote
import time

class Store(SessionStore):

    reapSQL="DELETE FROM %(table)s WHERE CURRENT_TIME - INTERVAL '%(timeout)s SECONDS' > %(timeCol)s"    

    def getConnection(self):
        return PyPgSQLcache.getConnection(Configuration.SessionHandler_PostgreSQLAlias)

    def escapeSQLString(self, s):
        return _quote(s)

