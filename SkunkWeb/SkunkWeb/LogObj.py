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
#$Id: LogObj.py,v 1.1.1.1 2001/08/05 14:59:37 drew_csillag Exp $
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
#import mmlib.mmint

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
    initialDebugServices=[]
    )

Logger._logStamp = "[%d]initializing... %%s -- " % os.getpid()

# initialize the debugFlags with a memory mapped int
Logger.debugFlags=0 #mmlib.mmint.MMInt(0)

# enable the logger to print the service name from the debug flag passed
# to debug statements.
Logger.getSourceFromKind=ServiceRegistry.getSourceFromKind
Logger._stampEveryLine=Configuration.stampEveryLine
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


########################################################################
# $Log: LogObj.py,v $
# Revision 1.1.1.1  2001/08/05 14:59:37  drew_csillag
# take 2 of import
#
#
# Revision 1.20  2001/08/01 01:43:53  smulloni
# modified Logger.py so Configuration.debugLog, accessLog, errorLog, and
# regularLog can be scoped.
#
# Revision 1.19  2001/07/28 15:45:16  drew
# no longer uses shared memory for debug flags
#
# Revision 1.18  2001/07/09 20:38:40  drew
# added licence comments
#
# Revision 1.17  2001/04/23 20:17:16  smullyan
# removed SKUNKWEB_SERVER_VERSION, which I found was redundant; fixed typo in
# httpd/protocol; renamed "debugServices" configuration variable to
# "initialDebugServices".
#
# Revision 1.16  2001/04/16 17:53:01  smullyan
# some long lines split; bug in Server.py fixed (reference to deleted
# Configuration module on reload); logging of multiline messages can now
# configurably have or not have a log stamp on every line.
#
# Revision 1.15  2001/04/10 22:48:30  smullyan
# some reorganization of the installation, affecting various
# makefiles/configure targets; modifications to debug system.
# There were numerous changes, and this is still quite unstable!
#
########################################################################



