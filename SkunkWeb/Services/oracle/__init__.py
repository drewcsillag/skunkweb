#  
#  Copyright (C) 2001 Andrew T. Csillag <drew_csillag@geocities.com>
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
