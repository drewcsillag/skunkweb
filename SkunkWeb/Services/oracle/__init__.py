#  
#  Copyright (C) 2001 Andrew T. Csillag <drew_csillag@geocities.com>
#  
#      You may distribute under the terms of either the GNU General
#      Public License or the SkunkWeb License, as specified in the
#      README file.
#   
from SkunkWeb import Configuration, LogObj, ServiceRegistry
from requestHandler.requestHandler import CleanupRequest
import Oracle

ServiceRegistry.registerService('oracle')

Configuration.mergeDefaults(
    OracleConnectStrings = {},
    OracleProcedurePackageLists = {}
    )

for u, str in Configuration.OracleConnectStrings.items():
    LogObj.DEBUG(ServiceRegistry.ORACLE, 'initializing user %s' % u)
    Oracle.initUser(u, str)

for u, pkglist in Configuration.OracleProcedurePackageLists:
    Oracle.loadSignatures(u, pkglist, LogObj.LOG,
                       lambda x: LogObj.DEBUG(ServiceRegistry.ORACLE, x))

def rollbackConnection(*args):
    for v in Oracle._connections.values():
        v.rollback()

CleanupRequest.addFunction(rollbackConnection)
