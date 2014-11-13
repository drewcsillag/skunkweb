#  Copyright (C) 2001 Andrew T. Csillag <drew_csillag@geocities.com>
#  
#      You may distribute under the terms of either the GNU General
#      Public License or the SkunkWeb License, as specified in the
#      README file.
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
        if item[:ll] == l:
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
                           LogObj,
                           foreground=Configuration.runInForeground)

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
        groupToRunAs=getattr(Configuration, 'groupToRunAs', None)
        userToRunAs=getattr(Configuration, 'userToRunAs', None)
        if groupToRunAs is not None or userToRunAs is not None:
            # in case we are seteuid something else, which would
            # cause setuid or getuid to fail, undo any existing
            # seteuid. (The only reason to do this is for the case
            # os.getuid()==0, AFAIK).
            try:
                seteuid=os.seteuid
            except AttributeError:
                # the OS may not support seteuid, in which
                # case everything is hotsy-totsy.
                pass
            else:
                seteuid(os.getuid())
            if groupToRunAs is not None:
                gid = grp.getgrnam(groupToRunAs)[2]
                os.setgid(gid)

            if userToRunAs is not None:
                uid = pwd.getpwnam(userToRunAs)[2]
                os.setuid(uid)
            
        Hooks.ChildStart()
        SocketMan.run(self)
        
    def reload(self):
        # extract what we need from configuration, and wipe it out
        global Configuration
        ver, cf, sr= (Configuration.SkunkWebVersion,
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
        self.foreground=Configuration.runInForeground
        
def _setConfigDefaults():
    import confvars
    Configuration.mergeDefaults(
        numProcs = 15,
        maxKillTime = 5,
        pidFile = confvars.DEFAULT_PID_FILE,
        pollPeriod = 5,
        maxRequests = 256,
        userModuleCleanup = 0,
        userModuleCleanupIgnore = [],
        runInForeground=0
    )    

def start():
    #print "server starting"
    svr.mainloop()

def addService(sockAddr, func):
    reset = None
    
    if hasattr(os, 'geteuid') and os.getuid() != os.geteuid():
        reset = os.geteuid() #uid to switch back to
        if hasattr(os, 'seteuid'):
            os.seteuid(0)
    try:
        svr.addConnection(sockAddr, func)
    finally: # make sure we go back to the initial user
        if reset is not None and hasattr(os, 'seteuid'):
            os.seteuid(reset)
    
########################################################################

_setConfigDefaults()
svr = SkunkWebServer()
svr.moduleSnapshot()    

