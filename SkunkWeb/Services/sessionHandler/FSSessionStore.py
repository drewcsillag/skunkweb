# Time-stamp: <01/08/06 13:10:07 smulloni>
# $Id$

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
# $Author$
# $Revision$
########################################################################


import cPickle
import fcntl
import os
import time
from SkunkExcept import SkunkStandardError
from SkunkWeb import Configuration
from SkunkWeb.LogObj import DEBUG
from SkunkWeb.ServiceRegistry import SESSIONHANDLER
from sessionHandler.Session import SessionStore

_sesspath=Configuration.SessionHandler_FSSessionDir

class FSSessionStoreImpl(SessionStore):
    """
    a SessionStore implementation that stores session pickles in files, one per session.
    Can only be used for standalone servers or in load-balancing setups where distributed
    sessions aren't necessary (which, given the fixed size of the SkunkWeb pool, is probably
    not a good fit).
    """ 
    _lastReaped=int(time.time())    
    
    def __init__(self, id):
        self.id=id        
        self.__picklepath=os.path.join(_sesspath, 
                                       id)
        # if the session dir doesn't exist, try to create it
        if not os.path.exists(_sesspath):
            try:
                os.makedirs(_sesspath)
            except:
                ERROR("FSSessionStoreImpl needs writeable session directory %s" % _sesspath)
                raise
        if not os.access(_sesspath, os.W_OK):
            raise SkunkStandardError, "FSSessionStoreImpl needs writeable session directory %s" % _sesspath
         
    def load(self):
        self._checkReap()
        return self.__getPickle() or {}

    def __getPickle(self):
        if os.path.exists(self.__picklepath):
            f=open(self.__picklepath)
            fd=f.fileno()
            # let reads coexist
            fcntl.flock(fd, fcntl.LOCK_SH)
            data=cPickle.load(f)
            fcntl.flock(fd, fcntl.LOCK_UN)
            f.close()
            return data
    
    def save(self, data):
        self.__setPickle(data)
        self._checkReap()

    def __setPickle(self, data):
        # lock and unlock, TBD
        f=open(self.__picklepath, 'w')
        fd=f.fileno()
        fcntl.flock(fd, fcntl.LOCK_EX)
        cPickle.dump(data, f, 1)
        fcntl.flock(fd, fcntl.LOCK_UN)
        f.close()
        
    def _checkReap(self):
        DEBUG(SESSIONHANDLER, "in _checkReap")
        reapInterval=Configuration.SessionReapInterval
        DEBUG(SESSIONHANDLER, "reap interval is %d" % reapInterval)
        DEBUG(SESSIONHANDLER, "last reaped: %d" % self.lastReaped())
        if reapInterval>0:
            currentTime=int(time.time())
            if currentTime>=(self.lastReaped() + reapInterval):
                self.reapOldRecords()
                self.lastReaped(currentTime)

    def reapOldRecords(self):
        # walk through contents of session directory and delete any
        # lapsed files
        for f in os.listdir(_sesspath):
            p=os.join(_sesspath, f)
            lastAccess=os.path.getatime(p)
            now=time.time()
            if now-lastAccess>Configuration.SessionTimeout:
                os.remove(p)

    def lastReaped(self, newVal=None):
        if not newVal:
            return FSSessionStoreImpl._lastReaped
        else:
            FSSessionStoreImpl._lastReaped=newVal
                
    def delete(self):
        os.remove(self.__picklepath)
        
    def touch(self):
        curtime=time.time()
        os.utime(self.__picklepath, (curtime, curtime))

########################################################################
# $Log$
########################################################################
