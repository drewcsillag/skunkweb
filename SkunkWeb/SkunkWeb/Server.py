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
# $Id: Server.py,v 1.16 2001/07/09 20:38:40 drew Exp $
# Time-stamp: <01/04/16 14:10:32 smulloni>
########################################################################

from SocketMan.SocketMan import SocketMan
import Configuration
import LogObj
import signal
import sys
from SkunkWeb.ServiceRegistry import CORE

class SkunkWebServer(SocketMan):
    def __init__(self):
        SocketMan.__init__(self,
                           Configuration.maxRequests,
                           Configuration.numProcs,
                           Configuration.maxKillTime,
                           Configuration.pidFile,
                           Configuration.pollPeriod,
                           LogObj)

        signal.signal(signal.SIGINT, self._SIGTERMHandler)

    def preHandle(self):
        LogObj.DEBUG(CORE,'in preHandle()')
        if not Configuration.userModuleCleanup:
            return
        self._umcMods = sys.modules.keys()
        
    def postHandle(self):
        LogObj.DEBUG(CORE, 'in postHandle()')
        if not Configuration.userModuleCleanup:
            return
        for k, v in sys.modules.items():
            if k not in self._umcMods:
                LogObj.DEBUG(CORE, 'killing module - %s' % k)
                if sys.modules[k]:
                    LogObj.DEBUG(CORE, 'mod is real')
                    mm = sys.modules[k]
                    bits = k.split('.')
                    if len(bits) > 1: #mod part of package
                        LogObj.DEBUG(CORE, 'part of pkg')
                        parent = '.'.join(bits[:-1])
                        if sys.modules.has_key(parent):
                            LogObj.DEBUG(CORE, 'have parent')
                            pmod = sys.modules[parent]
                            if (hasattr(parent, bits[-1])
                                and id(getattr(parent, bits[-1])) == id(mm)):
                                #delete module from parent package
                                delattr(parent, bits[-1])
                                LogObj.DEBUG(CORE, 'deling from parent')
                    LogObj.DEBUG(CORE, 'clearing module dict')
                    mm.__dict__.clear()
                LogObj.DEBUG(CORE, 'removing from sys.modules')
                del sys.modules[k]

    def run(self):
        import Hooks
        Hooks.ChildStart()
        SocketMan.run(self)
        
    def reload(self):
        # extract what we need from configuration, and wipe it out
        global Configuration
        ver, cf, sr = (Configuration.SkunkWebVersion,
                       Configuration._config_files_,
                       Configuration.SkunkRoot)
        SocketMan.reload(self)
        del Configuration
        
        global LogObj
        del LogObj
        
        sm = ['ConfigAdditives',
              'Configuration',
              'Hooks',
              'KickStart',
              'ServiceRegistry',
              'LogObj']
        for i in sm:
            del sys.modules['SkunkWeb.%s' % i]
        
        f = sys.modules.keys(); f.sort()
        f = sys.modules['SkunkWeb']
        for i in sm:
            delattr(f, i)
            
        import bootloader
        bootloader.init(cf, sr)
        import LogObj
        # replace the previous (massacred) LogObj with the new one
        self.logInterface=LogObj
        bootloader.load()

        global Configuration
        import Configuration
        _setConfigDefaults()
            
        self.userModuleCleanup = Configuration.userModuleCleanup
        self.maxRequests = Configuration.maxRequests
        self.numProcs = Configuration.numProcs
        self.pidFile = Configuration.pidFile
        self.pollPeriod = Configuration.pollPeriod
        self.maxKillTime = Configuration.maxKillTime
            
def _setConfigDefaults():

    Configuration.mergeDefaults(
        numProcs = 15,
        maxKillTime = 5,
        pidFile = "%s/var/run/sw.pid" % Configuration.SkunkRoot,
        pollPeriod = 5,
        maxRequests = 256,
        userModuleCleanup = 0,
    )    

def start():
    print "server starting"
    svr.mainloop()

def addService(sockAddr, func):
    svr.addConnection(sockAddr, func)

########################################################################

_setConfigDefaults()
svr = SkunkWebServer()
svr.moduleSnapshot()    

########################################################################
# $Log: Server.py,v $
# Revision 1.16  2001/07/09 20:38:40  drew
# added licence comments
#
# Revision 1.15  2001/04/16 18:10:16  smullyan
# fix to reload in Server.py; debug flags in AE module now reconciled with
# ServiceRegistry.
#
# Revision 1.14  2001/04/16 17:53:01  smullyan
# some long lines split; bug in Server.py fixed (reference to deleted
# Configuration module on reload); logging of multiline messages can now
# configurably have or not have a log stamp on every line.
#
# Revision 1.13  2001/04/10 22:48:31  smullyan
# some reorganization of the installation, affecting various
# makefiles/configure targets; modifications to debug system.
# There were numerous changes, and this is still quite unstable!
#
########################################################################
