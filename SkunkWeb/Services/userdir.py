#  
#  Copyright (C) 2001 Andrew T. Csillag <drew_csillag@geocities.com>
#  
#      You may distribute under the terms of either the GNU General
#      Public License or the SkunkWeb License, as specified in the
#      README file.
#   
########################################################################

import pwd
from SkunkWeb import Configuration

Configuration.mergeDefaults(userDir = 1,
                            userDirPath = 'public_html')

from SkunkWeb import ServiceRegistry
ServiceRegistry.registerService('userdir')
from SkunkWeb.LogObj import DEBUG
from SkunkWeb.ServiceRegistry import USERDIR    

def doUserDirPre(connection, sessionDict):
    """
    hook for web.protocol.PreHandleConnection
    """
    
    if not Configuration.userDir:
        return
    if connection.uri[:2] != '/~':
        return
    else:
        DEBUG(USERDIR, 'is userdir!')
        uri = connection.uri[2:]
        slashind = uri.find('/')
        if slashind == -1: slashind = len(uri)
        uname = uri[:slashind]
        rest_of_path = uri[slashind:]
        DEBUG(USERDIR, 'new uri is %s' % rest_of_path)
        DEBUG(USERDIR, 'user is %s' % uname)
        try:
            info = pwd.getpwnam(uname)
        except KeyError:
            return #allow it to pass through

        newdocroot = info[5] + '/' + Configuration.userDirPath
        sessionDict['UserDir'] = 1
        sessionDict['UserDirDocRoot'] = Configuration.documentRoot
        sessionDict['UserDirCC'] = Configuration.compileCacheRoot

        cacheroot="%s/~%s/" % (Configuration.compileCacheRoot, uname)
        connection.uri = rest_of_path
        # this will clean itself up when the Configuration is trimmed
        Configuration.push({'documentRoot' : newdocroot,
                            'compileCacheRoot' : cacheroot,
                            'componentCacheRoot' : cacheroot})
        return
        
        
def doUserDirPost(requestData, sessionDict): 
    """
    hook for requestHandler.requestHandler.CleanupRequest
    """
    if Configuration.userDir:
        for k in ('UserDir', 'UserDirCC', 'UserDirDocRoot'):
            if sessionDict.has_key(k):
                del sessionDict[k]

def __initHooks():
    import web.protocol as wp
    import SkunkWeb.constants as sc
    import requestHandler.requestHandler as rh
    jobGlob="%s*" % sc.WEB_JOB
    wp.PreHandleConnection.addFunction(doUserDirPre, jobGlob)
    rh.CleanupRequest.addFunction(doUserDirPost, jobGlob)

__initHooks()
