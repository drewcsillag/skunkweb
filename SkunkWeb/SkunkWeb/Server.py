# -*-python-*-
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
# $Id: Server.py,v 1.6 2002/08/16 15:56:15 drew_csillag Exp $
########################################################################

########################################################################
###IMPORTANT!!!!
###if you add imports to this module, make sure to update
###bootloader._stupidfunc (contained in bootloader.init) so that reload
###will continue to work
########################################################################
from SocketMan.SocketMan import SocketMan
import Configuration
import LogObj
import signal
import sys
from SkunkWeb.ServiceRegistry import CORE
import pwd
import os
import grp

def _aPrefixIn(item, l):
    for i in l:
        ll = len(l)
        if item[:l] == l:
            return 1
    return None

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
            if (k not in self._umcMods and
                not _aPrefixIn(k, Configuration.userModuleCleanupIgnore)):
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

        #now make sure that the kids can't setuid back to root
        if hasattr(Configuration, 'groupToRunAs'):
            gid = grp.getgrnam(Configuration.groupToRunAs)[2]
            os.setgid(gid)

        if hasattr(Configuration, 'userToRunAs'):
            uid = pwd.getpwnam(Configuration.userToRunAs)[2]
            os.seteuid(os.getuid())
            os.setuid(uid)
            
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

        #global Configuration
        import Configuration
        _setConfigDefaults()
            
        self.userModuleCleanup = Configuration.userModuleCleanup
        self.maxRequests = Configuration.maxRequests
        self.numProcs = Configuration.numProcs
        self.pidFile = Configuration.pidFile
        self.pollPeriod = Configuration.pollPeriod
        self.maxKillTime = Configuration.maxKillTime
            
def _setConfigDefaults():
    import confvars
    Configuration.mergeDefaults(
        numProcs = 15,
        maxKillTime = 5,
        pidFile = confvars.DEFAULT_PID_FILE,
        pollPeriod = 5,
        maxRequests = 256,
        userModuleCleanup = 0,
        userModuleCleanupIgnore = []
    )    

def start():
    #print "server starting"
    svr.mainloop()

def addService(sockAddr, func):
    reset = None
    
    if os.getuid() != os.geteuid():
        reset = os.geteuid() #uid to switch back to
        os.seteuid(0)
    try:
        svr.addConnection(sockAddr, func)
    finally: # make sure we go back to the initial user
        if reset is not None:
            os.seteuid(reset)
    
########################################################################

_setConfigDefaults()
svr = SkunkWebServer()
svr.moduleSnapshot()    

########################################################################
# $Log: Server.py,v $
# Revision 1.6  2002/08/16 15:56:15  drew_csillag
# added userModuleCleanupIgnore option to make the umc cleaner not clean out
# specified modules
#
# Revision 1.5  2002/07/25 17:27:46  drew_csillag
# made it do uid switching
#
# Revision 1.4  2002/07/11 22:57:00  smulloni
# configure changes to support other layouts
#
# Revision 1.3  2002/06/05 20:29:20  drew_csillag
# 	* SkunkWeb/SkunkWeb/Server.py: added comment at the top to remind
# 	us that in the event that we add an import, that we add that import
# 	to _stupidfunc in the bootloader
#
# 	* SkunkWeb/SkunkWeb/bootloader.py.in(init): now has some logic
# 	to produce a true module snapshot that should always do the right
# 	thing so reload will work
#
# 	* SkunkWeb/skunkweb.py.in: adjusted for bootloader change so reload
# 	should now work properly -- again
#
# Revision 1.2  2001/08/17 16:47:21  drew_csillag
# fixed syntax warning
#
# Revision 1.1.1.1  2001/08/05 14:59:37  drew_csillag
# take 2 of import
#
#
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
