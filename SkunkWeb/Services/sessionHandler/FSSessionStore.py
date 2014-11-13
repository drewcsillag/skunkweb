# Time-stamp: <2005-04-01 22:46:16 drew>
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
                  "FSSessionStoreImpl needs writeable session directory %s" \
                  % _sesspath
        self._picklepath=os.path.join(_sesspath, id)
        
    def load(self):
        return self._getPickle() or {}

    def lastTouched(self):
        try:
            atime=os.path.getatime(self._picklepath)
        except OSError:
            # file doesn't exist
            return int(time.time())
        else:
            return int(atime)

    def _getPickle(self):
        if os.path.exists(self._picklepath):
            try:
                data=cPickle.load(open(self._picklepath))
            except:
                logException()
                data={}
            return data
    
    def save(self, data):
        self._setPickle(data)

    def _setPickle(self, data):
        tmppath = self._picklepath + '.tmp'
        try:
            cPickle.dump(data, open(tmppath, 'w'), 1)
            os.rename(tmppath, self._picklepath)
        except:
            logException()
        
    def delete(self):
        os.remove(self._picklepath)
        
    def touch(self):
        curtime=time.time()
        os.utime(self._picklepath, (curtime, curtime))


FSSessionStoreImpl=Store
