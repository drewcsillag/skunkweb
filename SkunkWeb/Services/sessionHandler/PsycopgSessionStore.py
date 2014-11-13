#  
#  Copyright (C) 2001 Jacob Smullyan <smulloni@smullyan.org>
#  
#      You may distribute under the terms of either the GNU General
#      Public License or the SkunkWeb License, as specified in the
#      README file.
#
#
#  Modified by Nick Murtagh <nickm@go2.ie> 
#       from PostgreSQLSessionStore.py
#
#
#  Schema:
#
#      DROP TABLE Sessions;
#      CREATE TABLE Sessions
#      (
#          id VARCHAR(40) NOT NULL PRIMARY KEY,
#          pickle bytea NOT NULL,
#          accessTime TIMESTAMP NOT NULL DEFAULT now()::timestamp
#      );
#
#
#  Configuration:
#
#      SessionStore = 'sessionHandler.PsycopgSessionStore.Store'
#
#      # <connection alias> should be in PsycopgConnectParams
#      SessionHandler_PsycopgAlias = '<connection alias>'
#
# 
# Time-stamp: <2003-11-29 14:58:31 smulloni>
########################################################################

import cPickle
from sessionHandler.SQLSessionStore import AbstractSQLSessionStore
from SkunkWeb import Configuration
import PsycopgCache
import psycopg
import time

class Store(AbstractSQLSessionStore):

    reapSQL="DELETE FROM %(table)s WHERE CURRENT_TIME - INTERVAL '%(timeout)s SECONDS' > %(timeCol)s"   
    touchSQL="UPDATE %(table)s SET %(timeCol)s=NOW() WHERE %(idCol)s='%(id)s'"
    setPickleSQL=("UPDATE %(table)s SET %(pickleCol)s='%(gherkin)s', %(timeCol)s = NOW() "\
                  "WHERE %(idCol)s='%(id)s'")

    def getConnection(self):
        return PsycopgCache.getConnection(Configuration.SessionHandler_PsycopgAlias)

    def escapeSQLString(self, s):
        return str(psycopg.Binary(s))[1:-1]

    def marshalTimeStamp(self, ts):
        return ts.ticks()


PsycopgSessionStoreImpl=Store
