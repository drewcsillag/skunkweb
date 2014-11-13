#  
#  Copyright (C) 2001 Andrew T. Csillag <drew_csillag@geocities.com>
#  
#      You may distribute under the terms of either the GNU General
#      Public License or the SkunkWeb License, as specified in the
#      README file.
#   
# Time-stamp: <01/04/16 12:58:38 smulloni>
########################################################################

import os, time, cStringIO, traceback, types, sys

class _configStub:

    def __init__(self):
        self.debugLog=None
        self.errorLog=None
        self.regularLog=None
        self.accessLog=None
        self.httpAccessLog=None
        self.stampEveryLine=1
        self.logDateFormat='%a, %d %b %Y %H:%M:%S GMT'
#        self.debugFlags=0

# replace this if you want with any other object
# that has the fields above
config=_configStub()

debugFlags=0
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
    if config.stampEveryLine:
        return ["%s%s\n" % (logStamp, x) for x in msg.split("\n")]
    else:
        return ('%s%s\n' % (logStamp, msg))


def _doMsg(filename, msg, kind=0, prefix='', preStamped=0):
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
            if preStamped:
                stamp2=''
            else:
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

def HTTP_ACCESS(remote,
                request,
                status=200,
                length=0,
                rfc_user="-",
                auth_user="-"):
    stamp=_fmtDate()
    msg="%s %s %s [%s] \"%s\" %s %s" % (remote,
                                        rfc_user,
                                        auth_user,
                                        stamp,
                                        request,
                                        status,
                                        length)
    _doMsg(config.httpAccessLog,
           msg,
           preStamped=1)
    
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

