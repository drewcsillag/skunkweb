#  
#  Copyright (C) 2001 Jacob Smullyan <smulloni@smullyan.org>
#  
#      You may distribute under the terms of either the GNU General
#      Public License or the SkunkWeb License, as specified in the
#      README file.
#   
# Time-stamp: <2003-11-29 14:58:31 smulloni>
########################################################################

import cPickle
from sessionHandler.SQLSessionStore import AbstractSQLSessionStore
from SkunkWeb import Configuration
import PyPgSQLcache
from pyPgSQL.PgSQL import PgQuoteBytea, PgUnQuoteBytea
import time

class Store(AbstractSQLSessionStore):

    reapSQL="DELETE FROM %(table)s WHERE CURRENT_TIME - INTERVAL '%(timeout)s SECONDS' > %(timeCol)s"   
    touchSQL="UPDATE %(table)s SET %(timeCol)s=NOW() WHERE %(idCol)s='%(id)s'"
    setPickleSQL=("UPDATE %(table)s SET %(pickleCol)s='%(gherkin)s', %(timeCol)s = NOW() "\
                  "WHERE %(idCol)s='%(id)s'")    
    def getConnection(self):
        return PyPgSQLcache.getConnection(Configuration.SessionHandler_PostgreSQLAlias)

    def escapeSQLString(self, s):
        return PgQuoteBytea(s)[1:-1]

    def marshalTimeStamp(self, ts):
        return ts.ticks()


PostgreSQLSessionStoreImpl=Store
