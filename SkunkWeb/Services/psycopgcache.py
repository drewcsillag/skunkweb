########################################################################
#  Copyright (C) 2004 Andrew T. Csillag <drew_csillag@geocities.com>,
#                     Jacob Smullyan <smulloni@smullyan.org>
#  
#      You may distribute under the terms of either the GNU General
#      Public License or the SkunkWeb License, as specified in the
#      README file.
########################################################################

from SkunkWeb import Configuration
import PsycopgCache

Configuration.mergeDefaults(PsycopgConnectParams = {})

for u, p in Configuration.PsycopgConnectParams.items():
    PsycopgCache.initUser (u, p)

def rollback(*args):
    for v in PsycopgCache._connections.values():
        v.rollback()

from requestHandler.requestHandler import CleanupRequest
CleanupRequest.addFunction(rollback)
