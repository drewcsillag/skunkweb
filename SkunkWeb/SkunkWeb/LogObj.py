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
#$Id: LogObj.py,v 1.2 2002/07/11 22:57:00 smulloni Exp $
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
    if not sys.stderr.isatty():
        sys.stderr = Redirector(Logger.ERROR)
    if not sys.stdout.isatty():
        sys.stdout = Redirector(Logger.LOG)

########################################################################        

Configuration.mergeDefaults(
    accessLog =  confvars.DEFAULT_ACCESS_LOG,
    errorLog =   confvars.DEFAULT_ERROR_LOG,
    regularLog = confvars.DEFAULT_REGULAR_LOG,
    debugLog =   confvars.DEFAULT_DEBUG_LOG,
    stampEveryLine = 1,
    logDateFormat = '%a, %d %b %Y %H:%M:%S GMT',
    initialDebugServices=[],
    debugFlags=0
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
 logException)=(Logger.DEBUGIT,
                Logger.DEBUG,
                Logger.LOG,
                Logger.WARN,
                Logger.ERROR,
                Logger.ACCESS,
                Logger.logException)


