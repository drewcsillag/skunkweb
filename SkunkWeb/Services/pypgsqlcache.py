########################################################################
#  Copyright (C) 2002 Andrew T. Csillag <drew_csillag@geocities.com>
#  
#      You may distribute under the terms of either the GNU General
#      Public License or the SkunkWeb License, as specified in the
#      README file.
########################################################################

from SkunkWeb import Configuration
import PyPgSQLCache

Configuration.mergeDefaults(
    PyPgSQLConnectParams = {},
    )

for u, p in Configuration.PyPgSQLConnectParams.items():
    PyPgSQLCache.initUser ( u, p )

def rollback(*args):
    for v in PyPgSQLCache._connections.values():
        v.rollback()

from requestHandler.requestHandler import CleanupRequest
CleanupRequest.addFunction(rollback)
