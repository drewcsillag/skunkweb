from threading import local
import SkunkWeb
from SkunkWeb.constants import WEB_JOB, CONNECTION
from web.protocol import HaveConnection
from requestHandler.requestHandler import CleanupRequest
            
SkunkWeb.Context=_ctxt=local()

def install(requestData, sessionDict):
    conn=sessionDict[CONNECTION]
    _ctxt.connection=sessionDict[CONNECTION]


def uninstall(conn, sessionDict):
    try:
        del _ctxt.connection
    except AttributeError:
        pass

glob='%s*' % WEB_JOB
HaveConnection.addFunction(install, glob, 0)
CleanupRequest[glob]=uninstall
    

    
