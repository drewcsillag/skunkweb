# Time-stamp: <03/07/18 10:05:44 smulloni>
# $Id: FSSessionStore.py,v 1.4 2003/05/01 20:45:54 drew_csillag Exp $
#  Copyright (C) 2001, 2003 Jacob Smullyan <smulloni@smullyan.org>
#  
#      You may distribute under the terms of either the GNU General
#      Public License or the SkunkWeb License, as specified in the
#      README file.
#   
########################################################################

import cPickle
import fcntl
import os
import time
from SkunkExcept import SkunkStandardError
from SkunkWeb import Configuration
from SkunkWeb.LogObj import DEBUG, logException
from SkunkWeb.ServiceRegistry import SESSIONHANDLER
from sessionHandler.Session import SessionStore

class Store(SessionStore):
    
    """
    a SessionStore implementation that stores session pickles in
    files, one per session.  Can only be used for standalone servers
    or in load-balancing setups where distributed sessions aren't
    necessary (which, given the fixed size of the SkunkWeb pool, is
    probably not a good fit).
    """
#    _lastReaped=int(time.time())
    
    def __init__(self, id):
        self.id=id        
        _sesspath=Configuration.SessionHandler_FSSessionDir
        # if the session dir doesn't exist, try to create it
        if not os.path.exists(_sesspath):
            try:
                os.makedirs(_sesspath)
            except:
                msg="FSSessionStoreImpl needs to create writeable "\
                     "session directory %s" % _sesspath
                ERROR(msg)
                raise
        if not os.access(_sesspath, os.W_OK):
            raise SkunkStandardError, \
                  "FSSessionStoreImpl needs writeable session directory %s" % _sesspath
        self._picklepath=os.path.join(_sesspath, id)
        
    def load(self):
        # this is being done in Session.py, don't do it here
        #if time.time() - self.lastTouched() >= Configuration.SessionTimeout:
        #    os.remove(self._picklepath)
        #    return {}
        return self.__getPickle() or {}

    def lastTouched(self):
        try:
            atime=os.path.getatime(self._picklepath)
        except OSError:
            # file doesn't exist
            return int(time.time())
        else:
            return int(atime)

    def __getPickle(self):
        if os.path.exists(self._picklepath):
            f=open(self._picklepath)
            fd=f.fileno()
            # let reads coexist
            fcntl.flock(fd, fcntl.LOCK_SH)
            try:
                data=cPickle.load(f)
            except:
                logException()
                data={}
            fcntl.flock(fd, fcntl.LOCK_UN)
            f.close()
            return data
    
    def save(self, data):
        self.__setPickle(data)
#        self._checkReap()

    def __setPickle(self, data):
        f=open(self._picklepath, 'w')
        fd=f.fileno()
        fcntl.flock(fd, fcntl.LOCK_EX)
        try:
            cPickle.dump(data, f, 1)
        except:
            logException()
        fcntl.flock(fd, fcntl.LOCK_UN)
        f.close()
        
##    def _checkReap(self):
##        # DEBUG(SESSIONHANDLER, "in _checkReap")
##        reapInterval=Configuration.SessionReapInterval
##        # DEBUG(SESSIONHANDLER, "reap interval is %d" % reapInterval)
##        # DEBUG(SESSIONHANDLER, "last reaped: %d" % self.lastReaped())
##        if reapInterval>0:
##            currentTime=int(time.time())
##            if currentTime>=(self._lastReaped + reapInterval):
##                self.reapOldRecords()
##                self._lastReaped=currentTime

##    def reapOldRecords(self):
##        # walk through contents of session directory and delete any
##        # lapsed files
##        now=time.time()
##        _sesspath=Configuration.SessionHandler_FSSessionDir
##        for f in os.listdir(_sesspath):
##            p=os.path.join(_sesspath, f)
##            lastAccess=os.path.getatime(p)
##            if now-lastAccess>Configuration.SessionTimeout:
##                os.remove(p)

    def delete(self):
        os.remove(self._picklepath)
        
    def touch(self):
        curtime=time.time()
        os.utime(self._picklepath, (curtime, curtime))

