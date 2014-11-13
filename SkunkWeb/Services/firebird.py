# Time-stamp: <03/06/19 20:50:22 smulloni>

########################################################################
#  
#  Copyright (C) 2003 Andrew T. Csillag <drew_csillag@yahoo.com>,
#                     Jacob Smullyan <smulloni@smullyan.org>
#  
#      You may distribute under the terms of either the GNU General
#      Public License or the SkunkWeb License, as specified in the
#      README file.
#   
########################################################################

# contributed by Brian Olsen.

from SkunkWeb import Configuration
import Firebird

Configuration.mergeDefaults(
    FirebirdConnectParams = {},
    )

for u, p in Configuration.FirebirdConnectParams.items():
    Firebird.initUser(u, p)

def rollback(*args):
    for v in Firebird._connections.values():
        v.rollback()

from requestHandler.requestHandler import CleanupRequest
CleanupRequest.addFunction(rollback)
