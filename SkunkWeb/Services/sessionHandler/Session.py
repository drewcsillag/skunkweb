#  
#  Copyright (C) 2001 Jacob Smullyan <smulloni@smullyan.org>
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
# $Author: smulloni $
# $Revision: 1.3 $
# Time-stamp: <01/05/04 15:28:13 smulloni>
########################################################################

from web.protocol import HTTPConnection
from SkunkWeb import Configuration
from SkunkWeb.constants import CONNECTION
from SkunkWeb.ServiceRegistry import SESSIONHANDLER
import cPickle
import uuid
from SkunkWeb.LogObj import DEBUG, DEBUGIT, ERROR

# the key used, in cookie and/or in URL rewriting, for the session id.
_sessionIDKey=Configuration.SessionIDKey

# the session timeout
_timeout=Configuration.SessionTimeout

# at least how long, in seconds, we will wait before reaping old sessions
_reapInterval=Configuration.SessionReapInterval
DEBUG(SESSIONHANDLER, "reap interval is %d" % _reapInterval)


########################################################################
# methods that gets inserted into the HTTPConnection class

def getSession(self, create=0):           
    '''
    returns the session associated with this request.
    If create, will create a new session if there is none.
    '''
    if hasattr(self, '__userSession'):
        DEBUG(SESSIONHANDLER, "session found: %s" % self.__userSession.__dict__)
        return self.__userSession
    else:
        id=self.getSessionID(create)
        if not id:
            return None
        else:
            self.__userSession=Session(id)
            # here I should attempt to determine whether cookies are enabled, and then
            # turn on url rewriting if they are not.  TO BE DONE
            if (hasattr(self, 'requestCookie')
                and not self.requestCookie.has_key(_sessionIDKey)):
                self.responseCookie[_sessionIDKey]=id
            return self.__userSession

def removeSession(self):
    '''
    clears and removes any active session.
    '''
    DEBUG(SESSIONHANDLER, "in removeSession()")
    self.getSession(0)
    if hasattr(self, '__userSession'):
        DEBUG(SESSIONHANDLER, "calling delete()")
        self.__userSession.delete()
        del self.__userSession
    if self.responseCookie.has_key(_sessionIDKey):
        del self.responseCookie[_sessionIDKey]

def getSessionID(self, create=1):
    '''
    obtain the session id from the request cookie, or, if not
    available, create a new one.
    '''
    if (DEBUGIT(SESSIONHANDLER)
        and hasattr(self, 'requestCookie')
        and self.requestCookie):
        DEBUG(SESSIONHANDLER, str(self.requestCookie))
    if not hasattr(self, '__sessionID'):
        if (hasattr(self, 'requestCookie')
            and self.requestCookie
            and self.requestCookie.has_key(_sessionIDKey)):
            self.__sessionID=self.requestCookie[_sessionIDKey].value
        elif self.args.has_key(_sessionIDKey):
            self.__sessionID=self.args[_sessionIDKey]
        elif create:
            self.__sessionID=uuid.uuid()
        else:
            return None
    DEBUG(SESSIONHANDLER, 'session id: %s' % self.__sessionID)
    return self.__sessionID

####################################################################
# hook for ServerStart

def mungeConnection(*args, **kw):

    '''
    inserts the getSession() and getSessionID() methods into the HTTPConnection class
    '''
    DEBUG(SESSIONHANDLER, "in mungeConnection")
    setattr(HTTPConnection, "getSession", getSession)
    setattr(HTTPConnection, "removeSession", removeSession)
    setattr(HTTPConnection, "getSessionID", getSessionID)

####################################################################
# hook for InitRequest

def untouch(data, dict):
    DEBUG(SESSIONHANDLER, "in untouch()")
    if dict.has_key(CONNECTION):
        conn=dict[CONNECTION]
        session=conn.getSession(0)
        if session:
            session._touched=None


####################################################################
# hook for PostRequest

def saveSession(requestData, sessionDict):
    '''
    if the connection contains modified session information, saves it
    '''
    DEBUG(SESSIONHANDLER, "in saveSession")
    if sessionDict.has_key(CONNECTION):
        connection=sessionDict[CONNECTION]
        session=connection.getSession(0)
        if session:
            if session.isDirty():
                session.save()
            else: session.touch()
    else:
        DEBUG(SESSIONHANDLER, "no connection object found in sessionDict")


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
            ERROR("sessionHandler cannot load: unable to import %s!!!!" % fqcn)
            raise
    else:
        raise ValueError, "impossible to import: %s" % fqcn
        
            
####################################################################
# the Session class

class Session:
 
    def __init__(self, id):
        self.__ID=id
        storageClass=_getClass(Configuration.SessionStore)
        self.__store=storageClass(id)
        self.__data=self.__store.load()
        self.__dirty=None
        self._touched=None

    def getID(self):
        return self.__ID

    def isDirty(self):
        return self.__dirty

    def save(self):
        self.__store.save(self.__data)
        self.__dirty=None
        self._touched=1

    def delete(self):
        self.__store.delete()

    def keys(self):
        return self.__data.keys()

    def has_key(self, key):
        return self.__data.has_key(key)

    def clear(self):
        self.__data.clear()
        self.__dirty=1

    def __getitem__(self, key):
        return self.__data[key]

    def __delitem__(self, key):
        del self.__data[key]
        self.__dirty=1

    def __len__(self):
        return len(self.__data)

    def update(self, dict):
        self.__data.update(dict)
        self.__dirty=1

    def items(self):
        return self.__data.items()

    def values(self):
        return self.__data.values()

    def __setitem__(self, key, value):
        self.__data[key]=value
        self.__dirty=1

    def get(self, key, default):
        return self.__data.get(key, default)

    def touch(self): 
        if not self._touched:
            self.__store.touch()
        self._touched=1

########################################################################

class SessionStore:
    '''
    an interface that must be implemented by session stores
    '''
    
    def __init__(self, id):
        raise NotImplementedError

    def load(self):
        raise NotImplementedError

    def save(self, data):
        raise NotImplementedError

    def delete(self):
        raise NotImplementedError

    def touch(self):
        raise NotImplementedError
    
########################################################################
# $Log: Session.py,v $
# Revision 1.3  2001/08/13 01:08:09  smulloni
# added an evil boolean flag and an InitRequest hook to reset it.  These ensure
# that a session store is only touched if the session has not already been
# saved.  Unfortunately,  when a session is made dirty and then a
# redirect is performed, the next request can be handled by another process
# before the previous process is done persisting the session data, and the
# best workaround at present is to manually save the session before the
# redirect.  But this would have caused two database (or filesystem) hits
# for that request alone, one to save the session and another to update its
# timestamp; this change prevents that.
#
# Revision 1.2  2001/08/10 20:59:55  smulloni
# fix to removeSession()
#
# Revision 1.1.1.1  2001/08/05 15:00:07  drew_csillag
# take 2 of import
#
#
# Revision 1.10  2001/07/25 13:34:31  smulloni
# modified sessionHandler so that the SessionStore parameter is a string, not
# a class; added comments to sw.conf.in for sessionHandler-related goodies.
#
# Revision 1.9  2001/07/09 20:38:40  drew
# added licence comments
#
# Revision 1.8  2001/05/04 20:04:40  smullyan
# fix: sessionHandler needed to use SkunkWeb.constants;
# fix: web.protocol (which no longer has a protocol in it, oy!) now
# cleans up a little more carefully and no longer deletes the connection
# object from sessionDict (I may recycle it)
#
# Revision 1.7  2001/04/25 20:18:46  smullyan
# moved the "experimental" services (web_experimental and
# templating_experimental) back to web and templating.
#
# Revision 1.6  2001/04/23 04:55:47  smullyan
# cleaned up some older code to use the requestHandler framework; modified
# all hooks and Protocol methods to take a session dictionary argument;
# added script to find long lines to util.
#
# Revision 1.5  2001/04/11 20:47:11  smullyan
# more modifications to the debugging system to facilitate runtime change of
# debug settings.  Segfault in mmint.c fixed (due to not incrementing a
# reference count in the coercion method).
#
# Revision 1.4  2001/04/02 22:31:41  smullyan
# bug fixes.
#
# Revision 1.3  2001/04/02 00:54:18  smullyan
# modifications to use new requestHandler hook mechanism.
#
# Revision 1.2  2001/03/29 20:17:11  smullyan
# experimental, non-working code for requestHandler and derived services.
#
# Revision 1.1  2001/03/16 19:09:40  smullyan
# service that provides session handling capabilities.
#
########################################################################

