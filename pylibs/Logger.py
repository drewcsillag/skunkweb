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
# $Id: Logger.py,v 1.1.1.1 2001/08/05 15:00:33 drew_csillag Exp $
# Time-stamp: <01/04/16 12:58:38 smulloni>
########################################################################

import os, time, cStringIO, traceback, types, sys

class _configStub:

    def __init__(self):
        self.debugLog=None
        self.errorLog=None
        self.regularLog=None
        self.accessLog=None

# replace this if you want with any other object
# that has the fields 'debugFile', 'errorFile', 'logFile', and 'accessFile'.
config=_configStub()

# reset this if you want to log debug statements.
debugFlags=0

_logStamp="%s"

# whether to append a log stamp to every line of a multiline string, or
# just to the first line.
_stampEveryLine=1

# a map of logfile paths and their open file objects
_logFiles={}

def initLogStamp():
    global _logStamp
    pid = os.getpid()
    _logStamp = "[%%s] [%s] " % pid

def getSourceFromKind(kind):
    '''
    replace this function if you want to log the source of the debug
    argument differently
    '''
    return None

def _fmtDate():
    return time.strftime ('%a, %d %b %Y %H:%M:%S GMT' , time.gmtime ( time.time() ))

def _stamp(logStamp, msg):
    if _stampEveryLine:
        return "\n".join([logStamp+x for x in msg.split("\n")]) + "\n"
    else:
        return logStamp + msg + "\n"


def _doMsg(filename, msg, kind=0, prefix=''):
    if filename:
        if type(filename)==types.FileType:
            file=filename
        elif _logFiles.has_key(filename):
            file=_logFiles[filename]
        else:
            file=open(filename, 'a')
            _logFiles[filename]=file
        if file:
            source=getSourceFromKind(kind)
            stamp=_logStamp % _fmtDate()
            if source and prefix:
                stamp2="%s %s %s " % (stamp, source, prefix)
            elif source:
                stamp2="%s %s " % (stamp, source)
            elif prefix:
                stamp2= "%s %s " % (stamp, prefix)
            else:
                stamp2="%s " % stamp
            file.write(_stamp(stamp2, msg.strip()))
            file.flush()

def DEBUGIT(kind):
    #import sys
    return not not (config.debugLog and (debugFlags & kind))
    
def DEBUG(kind, msg):
    if debugFlags & kind:
        _doMsg(config.debugLog,
               msg,
               kind,
               "DEBUG:")
        
def LOG(msg):
    _doMsg(config.regularLog,
           msg,             
           prefix="LOG:")

def WARN(msg):
    _doMsg(config.errorLog,
           msg,
           prefix="WARNING:")

def ERROR(msg):
    _doMsg(config.errorLog,
           msg,
           prefix="ERROR:")

def ACCESS(msg):
    _doMsg(config.accessLog, msg)

def logException():
    exc_info=sys.exc_info()
    if exc_info:
        x = cStringIO.StringIO()
        traceback.print_tb(exc_info[2], file = x)
        text = x.getvalue()
        text += "\n%s: %s" % exc_info[:2]
        ERROR(text)
        return text
    else:
        return ''

########################################################################
# $Log: Logger.py,v $
# Revision 1.1.1.1  2001/08/05 15:00:33  drew_csillag
# take 2 of import
#
#
# Revision 1.5  2001/08/01 01:43:53  smulloni
# modified Logger.py so Configuration.debugLog, accessLog, errorLog, and
# regularLog can be scoped.
#
# Revision 1.4  2001/07/09 20:38:40  drew
# added licence comments
#
# Revision 1.3  2001/04/16 17:53:02  smullyan
# some long lines split; bug in Server.py fixed (reference to deleted
# Configuration module on reload); logging of multiline messages can now
# configurably have or not have a log stamp on every line.
#
# Revision 1.2  2001/04/11 20:47:12  smullyan
# more modifications to the debugging system to facilitate runtime change of
# debug settings.  Segfault in mmint.c fixed (due to not incrementing a
# reference count in the coercion method).
#
# Revision 1.1  2001/04/10 22:48:32  smullyan
# some reorganization of the installation, affecting various
# makefiles/configure targets; modifications to debug system.
# There were numerous changes, and this is still quite unstable!
#
########################################################################
