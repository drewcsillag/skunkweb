#  
#  Copyright (C) 2001 Andrew T. Csillag <drew_csillag@geocities.com>
#  
#      You may distribute under the terms of either the GNU General
#      Public License or the SkunkWeb License, as specified in the
#      README file.

# Time-stamp: <03/09/07 19:56:22 smulloni>   
# $Id: __init__.py 1752 2006-05-09 19:15:02Z smulloni $


def __initFlag():
    from SkunkWeb import ServiceRegistry
    ServiceRegistry.registerService('web', 'WEB')
    import SkunkWeb.Configuration as C
    C.mergeDefaults(mergeQueryStringWithPostData=1,
                    HttpLoggingOn=0)
    
def __initHooks():
    import requestHandler.requestHandler
    import protocol
    import SkunkWeb.constants

    jobGlob=SkunkWeb.constants.WEB_JOB+'*'
    requestHandler.requestHandler.HandleRequest[jobGlob]=protocol._processRequest
    requestHandler.requestHandler.CleanupRequest[jobGlob]=protocol._cleanupConfig
    requestHandler.requestHandler.PostRequest[jobGlob]=protocol._accesslog

__initFlag()
__initHooks()

