#
#  Copyright (C) 2001 Andrew T. Csillag <drew_csillag@geocities.com>
#  
#      You may distribute under the terms of either the GNU General
#      Public License or the SkunkWeb License, as specified in the
#      README file.
#   
########################################################################

"""
this module contains pre-fork initialization for logging.
"""

import os
import sys
from SkunkWeb import Configuration, Hooks, ServiceRegistry
import time
import traceback
import cStringIO
import Logger
import confvars

class Redirector:
    def __init__(self, func):
        self.lbuf = ''
        self.func = func
        
    def write(self, s):
        self.lbuf = self.lbuf + s
        if '\n' not in self.lbuf:
            return
        bits = self.lbuf.split('\n')
        for line in bits[:-1]:
            self.func(line)
        if not self.lbuf[-1] == '\n':
            self.lbuf = bits[-1]
        else:
            self.lbuf = ''
            
def redirectStdOutErr():
    if sys.__stderr__ == sys.stderr and not sys.stderr.isatty():
        sys.stderr = Redirector(Logger.ERROR)
    if sys.__stderr__ == sys.stderr and not sys.stdout.isatty():
        sys.stdout = Redirector(Logger.LOG)

########################################################################        

Configuration.mergeDefaults(
    accessLog =  confvars.DEFAULT_ACCESS_LOG,
    errorLog =   confvars.DEFAULT_ERROR_LOG,
    regularLog = confvars.DEFAULT_REGULAR_LOG,
    debugLog =   confvars.DEFAULT_DEBUG_LOG,
    httpAccessLog = confvars.DEFAULT_HTTP_ACCESS_LOG,
    stampEveryLine = 1,
    logDateFormat = '%a, %d %b %Y %H:%M:%S GMT',
    debugServices=[]
    )

Logger._logStamp = "[%d]initializing... %%s -- " % os.getpid()

# enable the logger to print the service name from the debug flag passed
# to debug statements.
Logger.getSourceFromKind=ServiceRegistry.getSourceFromKind
Logger.config=Configuration        

Hooks.ServerStart.append(Logger.initLogStamp)
Hooks.ServerStart.append(redirectStdOutErr)
Hooks.ChildStart.append(Logger.initLogStamp)

(DEBUGIT,
 DEBUG,
 LOG,
 WARN,
 ERROR,
 ACCESS,
 HTTP_ACCESS,
 logException)=(Logger.DEBUGIT,
                Logger.DEBUG,
                Logger.LOG,
                Logger.WARN,
                Logger.ERROR,
                Logger.ACCESS,
                Logger.HTTP_ACCESS,
                Logger.logException)
