# $Id: __init__.py,v 1.3 2002/04/17 20:47:57 smulloni Exp $
# Time-stamp: <2002-04-27 23:05:54 drew>
########################################################################
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

from SkunkWeb import Configuration, ServiceRegistry
from SkunkWeb.LogObj import DEBUG, logException
from requestHandler.protocol import PreemptiveResponse
import AE.Cache
import AE.Component
import os
import Authenticator
import sys
import base64
import armor

Configuration.mergeDefaults(
    cookieAuthName = 'auth',
    cookieAuthFile = None,
    cookieNonce = "ChangeMe",
    cookieLoginPage = None,
    cookieExtras = None,
    cookieAuthAuthorizer = None,
    cookieAuthActivated = None
    )
ServiceRegistry.registerService("cookieauth")
AUTH=ServiceRegistry.COOKIEAUTH

class defaultAuthKind:
    def checkAuth(self, authCred, conn, sessionDict):
        txt = armor.dearmor(Configuration.cookieNonce, authCred)
        if not txt:
            return

        bits = txt.split(':')
        user = bits[0]
        password = ':'.join(bits[1:])

        auth = Authenticator.FileAuthenticator(Configuration.cookieAuthFile)
        return auth.authenticate(user, password)

    def login(self, username, password):
        auth = Authenticator.FileAuthenticator(Configuration.cookieAuthFile)
        if not auth.authenticate(username, password):
            return

        st = armor.armor(Configuration.cookieNonce,
                         '%s:%s' % (username, password))
        return st
    
PlainAuthorizer = defaultAuthKind()
def authorize(username, password, responseCookie): #for use if using default authorizer
    st = PlainAuthorizer.login(username, password)
    if not st:
        return
    responseCookie[Configuration.cookieAuthName] = armor.armor(
        Configuration.cookieNonce, '%s:%s' % (username, password))[:-1]
    if Configuration.cookieExtras:
        for k,v in Configuration.cookieExtras.items():
            responseCookie[Configuration.cookieAuthName][k] = v
    return 1

def getAuthorizationFromHeaders(conn, sessionDict):
    """
    pulls auth cookie
    """
    if not Configuration.cookieAuthActivated:
        return
    
    DEBUG(AUTH, "looking for authorization cookie")
    try:
        #DEBUG(AUTH, '%s' % conn.requestCookie)
        auth = conn.requestCookie[Configuration.cookieAuthName].value
    except:
        auth = None

    conn.authType='cookieauth'
    conn.authCred = auth

def checkAuthorization(conn, sessionDict):
    """
    tests REMOTE_USER and REMOTE_PASSWORD against basic auth constraints, if
    any, and sends a preemptive 401 response, if necessary.
    """
    if not Configuration.cookieAuthActivated:
        return

    DEBUG(AUTH, 'checking authorization')

    if Configuration.cookieAuthAuthorizer is None:
        authorizer = PlainAuthorizer
    else:
        authorizer = Configuration.cookieAuthAuthorizer

    if not authorizer.checkAuth(conn.authCred, conn, sessionDict):
        DEBUG(AUTH, 'not authenticated')
        try:
            page=AE.Component.callComponent(
                Configuration.cookieLoginPage, {'CONNECTION':conn})
        except "OK":
            #this is the magical "do whatever you would've done" bit
            AE.Component.resetComponentStack()
            return
        
        except:
            DEBUG(AUTH, 'ACK! exception rendering login page')
            logException()
            page = "error occurred rendering login page"
            
        conn._output.write(page)
        resp = conn.response()
        DEBUG(AUTH, "page is %s" % resp)
        raise PreemptiveResponse, resp
    else:
        pass
        DEBUG(AUTH, 'auth returned true')

import web.protocol
import SkunkWeb.constants
jobGlob=SkunkWeb.constants.WEB_JOB+'*'

#usedtocould be HaveConnection
web.protocol.PreHandleConnection.addFunction(getAuthorizationFromHeaders,
                                             jobGlob, 0)

# authorization is checked after location-specific configuration data is loaded
web.protocol.PreHandleConnection.addFunction(checkAuthorization, jobGlob, 1)


########################################################################
# $Log: __init__.py,v $
# Revision 1.3  2002/04/17 20:47:57  smulloni
# added support for 'bpchar' type designation in PyDO/postconn.py;
# removed log comments that came from another file in cookieauth/__init__.py
#
# Revision 1.2  2002/04/17 19:37:48  drew_csillag
# minor tweak to debug info
#
# Revision 1.1  2002/04/17 19:25:51  drew_csillag
# added
########################################################################

