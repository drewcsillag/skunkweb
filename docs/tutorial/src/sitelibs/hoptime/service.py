# Time-stamp: <02/10/02 18:59:08 smulloni>
# $Id$

# Configuration variables go here.

# make certain that the postgresql service is loaded
import postgresql

import hopapi
hopapi.initDB(hopapi.SW_CONNECTSTRING)
from SkunkWeb.LogObj import DEBUG as _d

def _debug(message):
    _d(HOPTIME, str(message))
hopapi.DEBUG=_debug


