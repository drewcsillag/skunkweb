# Time-stamp: <2001-07-10 16:18:08 drew>
########################################################################
#  
#  Copyright (C) 2001 Andrew T. Csillag <drew_csillag@geocities.com>
#  
#      You may distribute under the terms of either the GNU General
#      Public License or the SkunkWeb License, as specified in the
#      README file.
#   

from SkunkWeb import Configuration, ServiceRegistry
from SkunkWeb.LogObj import DEBUG
from requestHandler.protocol import PreemptiveResponse
import AE.Cache
import os
import Authenticator
import sys
import base64

Configuration.mergeDefaults(
    basicAuthName = None,
    basicAuthFile = None
    )
ServiceRegistry.registerService("basicauth")
AUTH=ServiceRegistry.BASICAUTH

def getAuthorizationFromHeaders(conn, sessionDict):
    """
    pulls REMOTE_USER, REMOTE_PASSWORD, and AUTH_TYPE out of request headers.
    """
    DEBUG(AUTH, "looking for authorization headers")
    auth = conn.requestHeaders.get('Authorization',
                                   conn.requestHeaders.get('Proxy-Authorization'))
    if auth:
        DEBUG(AUTH, "found authorization")
        conn.authType, ai = auth.split()
        ucp = base64.decodestring(ai)
        colon_idx = ucp.find(':')
        conn.remoteUser = ucp[:colon_idx]
        conn.remotePassword = ucp[colon_idx+1:]
        # in case a template author is looking for these....
        conn.env['REMOTE_USER']=conn.remoteUser
        conn.env['REMOTE_PASSWORD']=conn.remotePassword
        conn.env['AUTH_TYPE']=conn.authType
    else:
        DEBUG(AUTH, "no authorization found")
        conn.authType = conn.remotePassword = conn.remoteUser = None
        
def checkAuthorization(conn, sessionDict):
    """
    tests REMOTE_USER and REMOTE_PASSWORD against basic auth constraints, if
    any, and sends a preemptive 401 response, if necessary.
    """
    DEBUG(AUTH, 'checking authorization')
    name, file = Configuration.basicAuthName, Configuration.basicAuthFile
    DEBUG(AUTH, 'name = %s, file = %s' % (name, file))
    if not (name and file):
        return
    authenticator = Authenticator.FileAuthenticator(file)
    if not authenticator.authenticate(conn.remoteUser, conn.remotePassword):
        page=getAuthorizationPage(name)
        raise PreemptiveResponse, page

# if you want a fancier page here, be my guest.
def getAuthorizationPage(realm):
    """
    Constructs a 401 page for the given realm.
    """
    global _authPage
    if not '_authPage' in dir():
        # _authPage lazily initialized.  Still happens once per process, but
        # better than doing it every 401.
        prettyBody='<HTML><HEAD><TITLE>Authorization Required</TITLE></HEAD>' \
                    '<BODY><H1>401 Authorization Required</H1></BODY></HTML>'
        _authPage='\r\n'.join(['Status: 401 Authorization Required',
                              'WWW-Authenticate: Basic realm=%s',
                              'Content-Type: text/html',
                              'Content-Length: %d' % len(prettyBody),
                              '',
                              prettyBody])
    return _authPage % realm

import web.protocol
import SkunkWeb.constants
jobGlob=SkunkWeb.constants.WEB_JOB+'*'
web.protocol.HaveConnection.addFunction(getAuthorizationFromHeaders, jobGlob)

# authorization is checked after location-specific configuration data is loaded
web.protocol.PreHandleConnection.addFunction(checkAuthorization, jobGlob, 0)

########################################################################
# $Log: __init__.py,v $
# Revision 1.2  2003/05/01 20:45:53  drew_csillag
# Changed license text
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

