#  
#  Copyright (C) 2001 Jacob Smullyan <smulloni@smullyan.org>
#  
#      You may distribute under the terms of either the GNU General
#      Public License or the SkunkWeb License, as specified in the
#      README file.
#   
########################################################################

from web.protocol import HTTPConnection
from SkunkWeb import Configuration
from SkunkWeb.constants import CONNECTION
from SkunkWeb.ServiceRegistry import SESSIONHANDLER
import cPickle
import uuid
from SkunkWeb.LogObj import DEBUG, DEBUGIT, ERROR
import Cookie
import time

class SessionError(Exception):
    pass

# python 2.1 compatibility
if dict==type({}):
    _dict=dict
else:
    from UserDict import UserDict as _dict


########################################################################
# methods that gets inserted into the HTTPConnection class

def getSession(self,
               create=1,
               path=None,
               domain=None,
               secure=None):           
    '''
    returns the session associated with this request.
    If create, will create a new session if there is none.
    '''
    # permit sessions to be turned off by leaving the session store null,
    # but raise an exception if someone tries to access a session
    if Configuration.SessionStore is None:
        raise SessionError, "no session store enabled"
    try:
        sess= self.__userSession
    except AttributeError:
        pass
    else:
        if sess:
            return sess
    DEBUG(SESSIONHANDLER, "session is None")
    # session is None
    
    id=self.getSessionID(create)
    if not id:
        DEBUG(SESSIONHANDLER, "id is false for create: %s" % create)
        return None

    sess=self.__userSession=Session(id)
    sesskey=Configuration.SessionIDKey

    # test session - is it too old?
    if sess.age() >= Configuration.SessionTimeout:
        DEBUG(SESSIONHANDLER, "session is too old")
        sess.delete()
        del self.__userSession
        if self.requestCookie.has_key(sesskey):
            self.responseCookie[sesskey]=""
            self.responseCookie[sesskey]['expires']=Cookie._getdate(-10000000)
        del self.__sessionID
        id=self.getSessionID(create)
        if not id:
            return None
        sess=self.__userSession=Session(id)
    
    if (not self.requestCookie.has_key(sesskey)) or \
           [x for x in (path, domain, secure) if x is not None]:
        self.responseCookie[sesskey]=id

        morsel=self.responseCookie[sesskey]
        if path is not None:
            morsel['path']=path
        if domain is not None:
            morsel['domain']=domain
        if secure is not None:
            morsel['secure']=secure

    return self.__userSession

def removeSession(self):
    '''
    clears and removes any active session.
    '''
    DEBUG(SESSIONHANDLER, "in removeSession()")
    self.getSession(0)

    try:
        sess=self.__userSession
    except AttributeError:
        pass
    else:
        if sess:
            sess.delete()
        del self.__userSession
        self.__sessionID=None
    sesskey=Configuration.SessionIDKey
    if self.requestCookie.has_key(sesskey):
        self.responseCookie[sesskey]=""
        self.responseCookie[sesskey]['expires']=Cookie._getdate(-10000000)


def getSessionID(self, create=1):
    '''
    obtain the session id from the request cookie, or, if not
    available, create a new one.
    '''
    
    try:
        sid=self.__sessionID
    except AttributeError:
        sesskey=Configuration.SessionIDKey        
        try:
            sid=self.requestCookie[sesskey].value
        except KeyError:
            # look in connection arguments for session id
            sid=self.args.get(sesskey)
            
    if sid is None and create:
        sid=uuid.uuid()
    if sid:
        self.__sessionID=sid
        return sid


####################################################################
# hook for ServerStart

def mungeConnection(*args, **kw):

    '''
    inserts the getSession() and getSessionID() methods into the HTTPConnection class
    '''
    DEBUG(SESSIONHANDLER, "in mungeConnection")
    HTTPConnection.getSession=getSession
    HTTPConnection.removeSession=removeSession
    HTTPConnection.getSessionID=getSessionID

####################################################################
# hook for PostRequest

def saveSession(requestData, sessionDict):
    '''
    if the connection contains modified session information, saves it
    '''
    DEBUG(SESSIONHANDLER, "in saveSession")
    connection=sessionDict.get(CONNECTION)
    if connection:
        session=connection.getSession(0)
        if session:
            if session.isDirty():
                session.save()
            else:
                session.touch()
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

class Session(_dict):
 
    def __init__(self, ID):
        _dict.__init__(self)
        self.ID=ID
        storageClass=_getClass(Configuration.SessionStore)
        self.store=storageClass(ID)
        self.update(self.store.load())
        self._dirty=None
        self._touched=None
        self._deleted=0

    def save(self):
        if self._deleted:
            # can't save a deleted session;
            # raise an exception?
            return
        self.store.save(self)
        self._dirty=None
        self._touched=1

    def delete(self):
        self.store.delete()
        self._dirty=0
        self._deleted=1
                   
    def age(self):
        if self._deleted:
            return 0
        return self.store.age()

    def clear(self):
        if self._deleted:
            raise SessionError, "cannot clear deleted session"
        _dict.clear(self)
        self._dirty=1

    def __delitem__(self, key):
        _dict.__delitem__(self, key)
        self._dirty=1

    def update(self, d):
        _dict.update(self, d)
        self._dirty=1

    def __setitem__(self, key, value):
        _dict.__setitem__(self, key, value)
        self._dirty=1

    def touch(self): 
        if not self._touched:
            self.store.touch()
        self._touched=1

    def isDirty(self):
        return self._dirty

    def setDirty(self, d):
        self._dirty=d

    def isDeleted(self):
        return self._deleted

    def isTouched(self):
        return self._touched

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

    def lastTouched(self):
        raise NotImplementedError

    def age(self):
        return int(time.time()) - self.lastTouched()
    
    def reap(self):
        raise NotImplementedError
