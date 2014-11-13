# Time-stamp: <03/04/22 22:18:20 smulloni>

########################################################################  
#  Copyright (C) 2001 Andrew T. Csillag <drew_csillag@geocities.com>
#  
#      You may distribute under the terms of either the GNU General
#      Public License or the SkunkWeb License, as specified in the
#      README file.
#
########################################################################

from SkunkWeb import Configuration
import MySQL
from SkunkExcept import SkunkStandardError
from requestHandler.requestHandler import CleanupRequest

Configuration.mergeDefaults(
    MySQLConnectParams = {},
    MySQLRollback=0,
    MySQLTestFunc=None
    )

# add test function (used by MySQL connection cache to test
# connections before handing them out)
MySQL.connection_test=Configuration.MySQLTestFunc

for u, p in Configuration.MySQLConnectParams.items():
    MySQL.initUser(u, p)

# optional rollback
def rollback(*args):
    for v in MySQL._connections.values():
        try:
            v.rollback()
        except:
            pass
        
if Configuration.MySQLRollback:
    CleanupRequest.addFunction(rollback)

