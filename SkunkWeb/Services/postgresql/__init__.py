#  
#  Copyright (C) 2001 Andrew T. Csillag <drew_csillag@geocities.com>
#  
#      You may distribute under the terms of either the GNU General
#      Public License or the SkunkWeb License, as specified in the
#      README file.
#   
from SkunkWeb import Configuration
import PostgreSql

Configuration.mergeDefaults(
    PostgreSQLConnectParams = {},
    )

for u, p in Configuration.PostgreSQLConnectParams.items():
    PostgreSql.initUser ( u, p )

def rollback(*args):
    for v in PostgreSql._connections.values():
        v.rollback()

from requestHandler.requestHandler import CleanupRequest
CleanupRequest.addFunction(rollback)
