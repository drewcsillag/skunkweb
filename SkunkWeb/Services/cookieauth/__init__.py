# $Id: __init__.py,v 1.1 2002/04/17 19:25:51 drew_csillag Exp $
# Time-stamp: <2002-04-17 14:53:26 drew>
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
    )
ServiceRegistry.registerService("cookieauth")
AUTH=ServiceRegistry.COOKIEAUTH

def getAuthorizationFromHeaders(conn, sessionDict):
    """
    pulls auth cookie
    """
    DEBUG(AUTH, "looking for authorization cookie")
    try:
        #DEBUG(AUTH, '%s' % conn.requestCookie)
        auth = conn.requestCookie[Configuration.cookieAuthName].value
    except:
        auth = None

    if auth:
        #DEBUG(AUTH, "dearmoring cookie %s" % auth)
        try:
            #DEBUG(AUTH, "Nonce is %s" % Configuration.cookieNonce)
            auth = armor.dearmor_detail(Configuration.cookieNonce, auth)
        except:
            #DEBUG(AUTH, "failed %s" % sys.exc_type)
            auth=None
        
    if not auth:
        #DEBUG(AUTH, "no authorization found")
        conn.authType = conn.remotePassword = conn.remoteUser = None
        return

    if auth:
        #DEBUG(AUTH, "found authorization %s" % auth)
        conn.authType='cookieauth'
        colon_idx = auth.find(':')
        conn.remoteUser = auth[:colon_idx]
        conn.remotePassword = auth[colon_idx+1:]
        # in case a template author is looking for these....
        conn.env['REMOTE_USER']=conn.remoteUser
        conn.env['REMOTE_PASSWORD']=conn.remotePassword
        conn.env['AUTH_TYPE']='cookieauth'
        #DEBUG(AUTH, "HERE!")
        
def checkAuthorization(conn, sessionDict):
    """
    tests REMOTE_USER and REMOTE_PASSWORD against basic auth constraints, if
    any, and sends a preemptive 401 response, if necessary.
    """
    DEBUG(AUTH, 'checking authorization')
    file = Configuration.cookieAuthFile
    #DEBUG(AUTH, 'file = %s' % file)
    if not file:
        return
    authenticator = Authenticator.FileAuthenticator(file)
    if not authenticator.authenticate(conn.remoteUser, conn.remotePassword):
        #DEBUG(AUTH, 'not authenticate')
        try:
            page=AE.Component.callComponent(
                Configuration.cookieLoginPage, {'CONNECTION':conn})
        except "OK":
            #this is the magical "do whatever you would've done" bit
            AE.Component.resetComponentStack()
            return
        
        except:
            #DEBUG(AUTH, 'ACK! exception rendering login page')
            logException()
            page = "error occurred rendering login page"
            
        conn._output.write(page)
        resp = conn.response()
        #DEBUG(AUTH, "page is %s" % resp)
        raise PreemptiveResponse, resp
    else:
        pass
        #DEBUG(AUTH, 'auth returned true')

def logout(responseCookie):
    responseCookie[Configuration.cookieAuthName] = ""
    if Configuration.cookieExtras:
        for k,v in Configuration.cookieExtras.items():
            responseCookie[Configuration.cookieAuthName][k] = v

    
def authorize(username, password, responseCookie):
    """attempts to authorize.  If succeeds, sets the cookie and returns a true
    value, otherwise, returns false"""
    DEBUG(AUTH, 'authing authorization')
    file = Configuration.cookieAuthFile
    DEBUG(AUTH, 'file = %s' % file)
    if not file:
        return
    authenticator = Authenticator.FileAuthenticator(file)
    #DEBUG(AUTH, 'user=%s, password=%s' % (username, password))

    if not authenticator.authenticate(username, password):
        return None

    #DEBUG(AUTH, "Nonce is %s" % Configuration.cookieNonce)
    responseCookie[Configuration.cookieAuthName] = armor.armor(
        Configuration.cookieNonce, '%s:%s' % (username, password))[:-1]
    if Configuration.cookieExtras:
        for k,v in Configuration.cookieExtras.items():
            responseCookie[Configuration.cookieAuthName][k] = v
    #DEBUG(AUTH, "cookie is %s" % responseCookie)
    return 1
    
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
# Revision 1.1  2002/04/17 19:25:51  drew_csillag
# added
#
# Revision 1.1.1.1  2001/08/05 14:59:58  drew_csillag
# take 2 of import
#
#
# Revision 1.8  2001/07/09 20:38:40  drew
# added licence comments
#
# Revision 1.7  2001/05/04 18:38:48  smullyan
# architectural overhaul, possibly a reductio ad absurdum of the current
# config overlay technique.
#
# Revision 1.6  2001/04/25 20:18:44  smullyan
# moved the "experimental" services (web_experimental and
# templating_experimental) back to web and templating.
#
# Revision 1.5  2001/04/23 18:52:54  smullyan
# basicauth repaired.
#
# Revision 1.4  2001/04/23 17:30:06  smullyan
# basic fixes to basic auth and httpd; added KeepAliveTimeout to requestHandler,
# using select().
#
########################################################################

