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
# $Id: userdir.py,v 1.3 2001/10/10 15:06:27 drew_csillag Exp $
########################################################################
import pwd
from SkunkWeb import Configuration

Configuration.mergeDefaults(userDir = 1,
                            userDirPath = 'public_html')

def __initFlag():
    from SkunkWeb import ServiceRegistry
    ServiceRegistry.registerService('userdir')

def doUserDirPre(connection, sessionDict):
    from SkunkWeb.LogObj import DEBUG
    from SkunkWeb.ServiceRegistry import USERDIR
    
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
        #sessionDict['UserDirURI'] = connection.uri
        sessionDict['UserDirCC'] = Configuration.compileCacheRoot

        Configuration.documentRoot = newdocroot
        connection.uri = rest_of_path 
        Configuration.compileCacheRoot = Configuration.compileCacheRoot + \
                                         '/~%s/' % uname
        return
        
        
def doUserDirPost(sessionDict): #requestHandler.requestHandler.EndSession
    if not Configuration.userDir:
        return
    if not sessionDict.has_key('UserDir'):
        return
    if not sessionDict['UserDir']:
        return

    Configuration.documentRoot = sessionDict['UserDirDocRoot']
    Configuration.compileCacheRoot = sessionDict['UserDirCC']
    del sessionDict['UserDirCC'], sessionDict['UserDirDocRoot']
    del sessionDict['UserDir']
    return

def __initHooks():
    from web.protocol import HandleConnection
    HandleConnection.addFunction(doUserDirPre, '*', 0)
    import requestHandler.requestHandler as rh
    rh.EndSession.addFunction(doUserDirPost)

__initFlag()
__initHooks()
