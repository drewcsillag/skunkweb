# Time-stamp: <02/10/30 09:27:03 smulloni>

# default values for Configuration variables go here.
import SkunkWeb.Configuration as C

# whether to disallow "guest" (anonymous) logins
C.mergeDefaults(HoptimeRequireValidUser=0) 

# make certain that the postgresql service is loaded
import postgresql

# initialize the db connection caching mechanism with a connectstring
import hopapi
hopapi.initDB(hopapi.SW_CONNECTSTRING)

# hopapi has a debug method that prints to stderr by default.
# replace it with SkunkWeb's debug method.
import SkunkWeb.ServiceRegistry as _SR
from SkunkWeb.LogObj import DEBUG as _d

def _munge_debug():
    _SR.registerService('hoptime.service', 'HOPTIME')
    HOPTIME=_SR.HOPTIME
    def _debug(message):
        _d(HOPTIME, str(message))
    hopapi.DEBUG=_debug

_munge_debug()
