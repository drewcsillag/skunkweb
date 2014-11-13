# Time-stamp: <2004-03-02 14:57:41 drew>
########################################################################
#  
#  Copyright (C) 2001 Andrew T. Csillag <drew_csillag@geocities.com>
#  
#      You may distribute under the terms of either the GNU General
#      Public License or the SkunkWeb License, as specified in the
#      README file.
#   

from SkunkWeb import Configuration, ServiceRegistry
from SkunkWeb.LogObj import DEBUG, ERROR, logException
from requestHandler.protocol import PreemptiveResponse
import AE.Cache
import AE.Component
import os
import Authenticator
import sys
import base64
import armor

Configuration.mergeDefaults(
    authAuthorizer = None,
    authActivated = None,
    authAuthorizerCtorArgs = (),
    )
ServiceRegistry.registerService("auth")
AUTH=ServiceRegistry.AUTH

class OK(Exception): pass

# an authorizer 
#class authorizer:
#    def __init__(self, ......):
#    """
#    The ...... will be filled with the contents of
#    Configuration.authAuthorizerCtorArgs when this object is instantiated.
#    """
#
#    def checkCredentials(self, conn):
#    """
#    Examine the connection however you see fit to see if the
#    connection has the credentials needed to view the page
#    return true to accept, false to reject
#    """
#
#    def login(self, conn, username, password):
#    """
#    Take the username and password, validate them, and if they are
#    valid, give the connection credentials to validate them in the
#    future (i.e. make it so checkCredentials() returns true).  If your
#    authorizer is doing basicauth-style authentication, this method is
#    not required.
#    """
#
#    def logout(self, conn):
#    """
#    Remove any credentials from the browser.  This method is not required
#    for methods (specifically, basicauth) that do not have the concept of
#    logging out.
#    """
#
#    def authFailed(self, conn):
#    """
#    If the connections credentials are rejected, what to do.  For
#    this, unless you are using a basic-auth means, inheriting from
#    RespAuthBase is probably sufficient (it will bring up a login
#    page), otherwise inheriting from BasicAuthBase and providing an
#    appropriate validate function is sufficient.
#    """
#
#    #this method is required only if using one of the base classes that
#    #require it
#    def validate(self, username, password):
#    """
#    Return true if the username/password combo is valid, false otherwise
#    """



class RespAuthBase:
    """
    This is a base class for those authorizers that need to use a login page.
    That's pretty much any of them, with the exception of BasicAuth, as it
    doesn't need it since the browser "puts up a login page".

    The loginPage ctor arg is the page to show.  It *can* be in the protected
    area.
    """
    def __init__(self, loginPage):
        self.loginPage = loginPage

    def authFailed(self, conn):
        try:
            page=AE.Component.callComponent(
                self.loginPage, {'CONNECTION':conn})
        # string exception left here for backwards compatibility
        except ("OK", OK):
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

class AuthFileBase: #base class for those that auth against a basicauth file
    """
    Base class for authorizers that will use a simple basicauth file to
    validate user/password combinations

    The authFile ctor argument is the file that we will validate against
    """
    def __init__(self, authFile):
        self.authFile = authFile
        
    def validate(self, username, password):
        authenticator = Authenticator.FileAuthenticator(self.authFile)
        if not authenticator.authenticate(username, password):
            return None
        return 1

class BasicAuthBase: #base class that does basicauth
    """
    This class does browser based basicauth authentication where it pops up
    the login box by itself.

    This is a mixin class and is not usable by itself.  You must provide a
    way to validate (by subclassing BasicAuthBase and defining a validate
    function) the username and password that is obtained.
    """
    def __init__(self, authName):
        self.authName = authName
        self.authPage = None
        
    def checkCredentials(self, conn):
        DEBUG(AUTH, "looking for authorization headers")
        auth = conn.requestHeaders.get('Authorization',
                                       conn.requestHeaders.get(
            'Proxy-Authorization'))
        if auth:
            DEBUG(AUTH, "found authorization")
            dummy, ai = auth.split()
            ucp = base64.decodestring(ai)
            colon_idx = ucp.find(':')
            conn.remoteUser = ucp[:colon_idx]
            conn.remotePassword = ucp[colon_idx+1:]
            # in case a template author is looking for these....
            conn.env['REMOTE_USER']=conn.remoteUser
            conn.env['REMOTE_PASSWORD']=conn.remotePassword
        else:
            DEBUG(AUTH, "no authorization found")
            conn.remotePassword = conn.remoteUser = None
            return None

        
        #ok, auth must be true here
        DEBUG(AUTH, 'checking authorization')
        return self.validate(conn.remoteUser, conn.remotePassword)

    def authFailed(self, conn):
        if not self.authPage:
            # _authPage lazily initialized.  Still happens once per process, 
            # but better than doing it every 401.
            prettyBody='<HTML><HEAD><TITLE>Authorization Required</TITLE>' \
                        '</HEAD>' \
                        '<BODY><H1>401 Authorization Required</H1></BODY>' \
                        '</HTML>'
            _authPage='\r\n'.join(['Status: 401 Authorization Required',
                                  'WWW-Authenticate: Basic realm=%s',
                                  'Content-Type: text/html',
                                  'Content-Length: %d' % len(prettyBody),
                                  '',
                                  prettyBody])
            raise PreemptiveResponse, (_authPage % self.authName)

    #def no login method since the browser handles that automatically
    
class CookieAuthBase: #class that does basic cookie authentication
    """
    This class implements a simple cookie based authentication.  Depending
    on how you want to do things, you may not (and probably don't) want to
    have the username and password encoded directly in the cookie, but
    definitely *do* use the armor module to protect whatever you do decide to
    put into the cookie as it will make them virtually tamperproof.

    As with BasicAuthBase, thisis a mixin class and is not usable by
    itself.  You must provide a way to validate (by subclassing CookieAuthBase
    and defining a function) the username and password that is obtained.
    """
    def __init__(self, cookieName, cookieNonce,
                 cookieExtras = {}):
        "cookieExtras are the cookieAttributes for the cookie, used for login"
        self.cookieName = cookieName
        self.cookieNonce = cookieNonce
        self.cookieExtras = cookieExtras
        
    def checkCredentials(self, conn):
        DEBUG(AUTH, "looking for auth cookie")
        auth = conn.requestCookie.get(self.cookieName)
        if not auth:
            return None

        #have cookie, now check, assuming basicAuth style cookie w/armoring
        auth = auth.value
        txt = armor.dearmor(self.cookieNonce, auth)
        if not txt:
            return

        bits = txt.split(':')
        user = bits[0]
        password = ':'.join(bits[1:])
        conn.remoteUser = user
        conn.remotePassword = password
        conn.env['REMOTE_USER']=conn.remoteUser
        conn.env['REMOTE_PASSWORD']=conn.remotePassword        
        return self.validate(user, password)

    #a simple login method to set the cookie as appropriate
    def login(self, conn, username, password):
        val=self.validate(username, password)
        if val:
            cookieval = armor.armor(self.cookieNonce,
                                    "%s:%s" % (username, password))
            # the slice [:-1] is to trim off the newline that armor appends
            conn.responseCookie[self.cookieName] = cookieval[:-1]
            if self.cookieExtras:
                for k,v in self.cookieExtras.items():
                    conn.responseCookie[self.cookieName][k] = v
            conn.remoteUser = username
            conn.remotePassword = password
            conn.env['REMOTE_USER']=conn.remoteUser
            conn.env['REMOTE_PASSWORD']=conn.remotePassword
            # login will now return what validate returns,
            # which is convenient if it returns a user object
            # of some kind
            return val

    def logout(self, conn):
        # the standard cookie class really sucks
        conn.responseCookie[self.cookieName]=""
        for k, v in self.cookieExtras.items():
            conn.responseCookie[self.cookieName][k]=v
        conn.responseCookie[self.cookieName]['expires']=-1-sys.maxint        

class SessionAuthBase: #class to do auth using sessions
    """
    This class uses the session object (you must have the sessionHandler
    service loaded) to handle authentication.  This is also probably not 
    something that you would really want to use in a production setup as:
    a) you probably don't want to store the password in the session.  Not that
       it's inherently evil, but it's one less thing you have to worry about
       leaking in the event that something gets screwed up.
    b) checking the credentials might just be to check if the username is set
       since all of the session info (minus the session key) is stored on
       the server and not the browser, we don't have to worry as much that
       somebody fooled around with us

    But what is here is usable as a starting point and will run.

    As with BasicAuthBase, thisis a mixin class and is not usable by
    itself.  You must provide a way to validate (by subclassing SessionAuthBase
    and defining a function) the username and password that is obtained.

    """
    def __init__(self, usernameSlot, path = None, domain = None,
                 secure = None):
        """
        username is dict entry in the session for the username
        password is dict entry in the session for the password
        path, domain and secure are passed through to CONNECTION.getSession()
        """
        self.usernameSlot = usernameSlot
        self._path = path
        self._domain = domain
        self._secure = secure

    def checkCredentials(self, conn):
        """for session authentication, you may not actually store the username
        and/password in the session (especially the password), but since
        we only use sess.get, you can leave it out if you want"""
        sess = conn.getSession()
        if not sess: return None
        username = sess.get(self.usernameSlot)
        #if the session has this, they must have already authenticated
        if username: 
            return 1

    def login(self, conn, username, password):
        """again, you may want to customize this such that the password
        isn't in the session, but that's up to you"""
        if self.validate(username, password):
            sess = conn.getSession(1, path = self._path, domain = self._domain,
                                   secure = self._secure)
            sess[self.usernameSlot] = username
            sess.save()
            return 1

    def logout(self, conn):
        sess = conn.getSession()
        if not sess: return
        del sess[self.usernameSlot]
        sess.save()

#the classes that are usable as authAuthorizers
class BasicAuth(BasicAuthBase, AuthFileBase):
    def __init__(self, authName, authFile):
        BasicAuthBase.__init__(self, authName)
        AuthFileBase.__init__(self, authFile)

class PlainCookieAuth(CookieAuthBase, AuthFileBase, RespAuthBase):
    def __init__(self, authFile, loginPage, cookieName, nonce, extras):
        CookieAuthBase.__init__(self, cookieName, nonce, extras)
        AuthFileBase.__init__(self, authFile)
        RespAuthBase.__init__(self, loginPage)

class PlainSessionAuth(SessionAuthBase, AuthFileBase, RespAuthBase):
    def __init__(self, usernameSlot, authFile, loginPage):
        SessionAuthBase.__init__(self, usernameSlot)
        AuthFileBase.__init__(self, authFile)
        RespAuthBase.__init__(self, loginPage)

_AuthObjCache={}

def getAuthorizer():
    key = (Configuration.authAuthorizer, id(Configuration.authAuthorizerCtorArgs))
    authorizer = _AuthObjCache.get(key)
    if authorizer is None:
        authorizer = _AuthObjCache[key] = _getClass(key[0])(*Configuration.authAuthorizerCtorArgs)
    return authorizer

def checkAuthorization(conn, sessionDict):
    """
    any, and sends a preemptive 401 response, if necessary.
    """
    if not Configuration.authActivated:
        return

    DEBUG(AUTH, 'checking authorization')
    authorizer = getAuthorizer()
        
    #if type(authorizer) == type(''): #if string, load module and replace
    #    authorizer = Configuration.authAuthorizer = _getClass(authorizer)(
    #        *Configuration.authAuthorizerCtorArgs)
        
    if not authorizer.checkCredentials(conn):
        DEBUG(AUTH, 'not authenticated')
        authorizer.authFailed(conn)
    else:
        DEBUG(AUTH, 'auth returned true')

def _getClass(fqcn): # fully qualified class name: package.module.fooClass
    lastDot=fqcn.rfind('.')   
    if lastDot==0:
        raise ValueError, "unable to import %s" %fqcn
    if lastDot>0:
        modName=fqcn[:lastDot]
        className=fqcn[lastDot+1:]
        try:
            module=__import__(modName, globals(), locals(), [className])
            return vars(module)[className]
        except (ImportError, AttributeError):
            ERROR("auth cannot load: unable to import %s!!!!" % fqcn)
            raise
    else:
        raise ValueError, "impossible to import: %s" % fqcn

import web.protocol
import SkunkWeb.constants
jobGlob=SkunkWeb.constants.WEB_JOB+'*'

web.protocol.PreHandleConnection.addFunction(checkAuthorization, jobGlob, 1)


########################################################################
# $Log: __init__.py,v $
# Revision 1.12  2004/03/02 19:48:34  drew_csillag
# now you
# 	can pass path, domain and secure to the constructor to set the
# 	appropriate parameters on the session cookie
#
# Revision 1.11  2003/05/01 20:45:53  drew_csillag
# Changed license text
#
# Revision 1.10  2002/11/07 19:34:17  smulloni
# fix for cookie expiration in auth; many changes in tutorial demo app.
#
# Revision 1.9  2002/11/01 17:54:06  smulloni
# progress on hoptime demo for tutorial.
#
# Revision 1.8  2002/10/15 17:24:20  smulloni
# deprecated string exception, set environmental variables more
# consistently.
#
# Revision 1.7  2002/06/30 17:28:56  drew_csillag
#  made it so
# 	we don't need the PseudoDict thing we used to need.
#
# Revision 1.6  2002/06/27 21:18:46  drew_csillag
# fixed so that you can have two different auth schemes going at the same time
# in different dirs and still have it all work.
#
# Revision 1.5  2002/06/06 13:53:58  drew_csillag
# now cookieauth will set conn.remoteUser and conn.remotePassword when logging in
#
# Revision 1.4  2002/05/15 16:19:39  smulloni
# fixing broken import
#
# Revision 1.3  2002/05/14 17:37:53  smulloni
# bug fix
#
# Revision 1.2  2002/04/30 02:59:16  drew_csillag
# added more documentation in
# 	the comment describing authorizer objects as well as did a few
# 	grammar/spelling/capitalization fixes.
#
# 	The SessionAuthBase also no longer stores the password in the
# 	session.  That was pretty stupid.  If somebody actually wants that,
# 	they can do it themselves.
#
# Revision 1.1  2002/04/29 21:09:48  drew_csillag
# added
#
########################################################################
