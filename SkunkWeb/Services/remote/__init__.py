#  
#  Copyright (C) 2001 Jacob Smullyan <smulloni@smullyan.org>
#  
#      You may distribute under the terms of either the GNU General
#      Public License or the SkunkWeb License, as specified in the
#      README file.
#   
# Time-stamp: <01/05/04 17:39:07 smulloni>
# support for remote calls from other SkunkWeb servers using a
# python-specific protocol.
########################################################################

import ae_component
import requestHandler
from SkunkWeb import constants, ServiceRegistry, Configuration


def __initFlag():
    ServiceRegistry.registerService('remote')

def __initHandler():
    # TEMPORARILY HARD-CODED IN constants.py
    #skc.REMOTE_JOB=.rc.AE_COMPONENT_JOB + "/remote/"
    jobGlob='*%s*' % constants.REMOTE_JOB
    import handler
    requestHandler.requestHandler.HandleRequest[jobGlob]=handler.handleRequestHookFunc
    

def __initConnections():
    from protocol import SkunkWebRemoteProtocol
    Configuration.mergeDefaults(RemoteListenPorts=['TCP:localhost:9887'])
    if Configuration.RemoteListenPorts:
        requestHandler.requestHandler.addRequestHandler(SkunkWebRemoteProtocol(),
                                                        Configuration.RemoteListenPorts)
        
__initFlag()  
__initHandler()
__initConnections()

