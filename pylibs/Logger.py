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
# $Id: Logger.py,v 1.5 2003/04/23 02:24:13 smulloni Exp $
# Time-stamp: <01/04/16 12:58:38 smulloni>
########################################################################

import os, time, cStringIO, traceback, types, sys

class _configStub:

    def __init__(self):
        self.debugLog=None
        self.errorLog=None
        self.regularLog=None
        self.accessLog=None
        self._stampEveryLine=1
        self.logDateFormat='%a, %d %b %Y %H:%M:%S GMT'
        self.debugFlags=0

# replace this if you want with any other object
# that has the fields above
config=_configStub()

_logStamp="%s"

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
    return time.strftime(config.logDateFormat,
                         time.gmtime(time.time()))

def _stamp(logStamp, msg):
    if config._stampEveryLine:
        return ["%s%s\n" % (logStamp, x) for x in msg.split("\n")]
    else:
        return ('%s%s\n' % (logStamp, msg))


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
            for line in _stamp(stamp2, msg.strip()):
                file.write(line)
            file.flush()

def DEBUGIT(kind):
    #import sys
    return not not (config.debugLog and (config.debugFlags & kind))
    
def DEBUG(kind, msg):
    if config.debugFlags & kind:
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
        try:
            traceback.print_tb(exc_info[2], file = x)
        except:
            x.write("Strange and Weird thing happened, we ran into"
                    " an exception rendering an exception?!?!?!?!\n")
            try:
                traceback.print_tb(sys.exc_info()[2], file = x)
            except:
                #should I do os.kill(9 (or 15), os.getpid()) ???
                x.write("Ok, we're fubar!!! %s\n" %
                        str(map(str, sys.exc_info())))

                
        text = x.getvalue()
        text += "\n%s: %s" % exc_info[:2]
        ERROR(text)
        return text
    else:
        return ''

