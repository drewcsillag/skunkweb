#  
#  Copyright (C) 2001 Andrew T. Csillag <drew_csillag@geocities.com>
#  
#      You may distribute under the terms of either the GNU General
#      Public License or the SkunkWeb License, as specified in the
#      README file.
#   
import ProcessMgr.ProcessMgr
import fcntl
import select
import socket
import errno
if hasattr(fcntl, 'F_SETFD'): # to avoid deprecation warning with 2.2
    FCNTL = fcntl
else:
    import FCNTL
import sys
import cStringIO
import traceback
import os
import stat
    
class SocketMan(ProcessMgr.ProcessMgr.ProcessMgr):
    def __init__(self, maxRequests=None, *args, **kw):
        self.maxRequests = maxRequests
        self.socketMap = {}
        ProcessMgr.ProcessMgr.ProcessMgr.__init__(self, *args, **kw)

    def preHandle(self):
        pass

    def postHandle(self):
        pass
    
    def _run(self):
        connectionCount = 0
        while 1:
            connectionCount += 1
            if self.maxRequests and connectionCount > self.maxRequests:
                self.logInterface.LOG('hit maxRequests, recycling')
                break
            have_connection = 0
            while not have_connection:
                try:
                    r,w,e = select.select(self.socketMap.keys(), [], [])
                except:
                    #this should only happen if errno is EINTR, but
                    #exiting is still probably the best idea here
                    v = sys.exc_info()[1]
                    if hasattr(v, 'errno') and v.errno != errno.EINTR:
                        self.logInterface.LOG("error on select: %s %s" % (
                            sys.exc_type, sys.exc_value))
                    else:
                        self.logInterface.LOG('select failed! %s:%s' %
                                              sys.exc_info()[:2])
                        self.logInterface.LOG('socketmap is %s' % (
                            self.socketMap.keys()))
                        
                    break

                s = r[0]
                try:
                    sock, addr = s.accept()
                    sock.setblocking(1)
                except socket.error, (err, errstr):
                    if err not in [errno.EAGAIN, errno.EWOULDBLOCK]:
                        raise
                else:
                    have_connection = 1

            if not have_connection: #because of a select error
                self.logInterface.LOG('SM exiting due to no connection')
                break # die!
            
            r = None
            try:
                #self.logInterface.LOG('calling %s for %s' % (
                #    self.socketMap[s], sock))
                try:
                    self.preHandle()
                except:
                    self.logInterface.ERROR('preHandle died %s %s %s' %
                                            sys.exc_info())
                    
                r = self.socketMap[s][0](sock, addr)
                try:
                    self.postHandle()
                except:
                    self.logInterface.ERROR('postHandle died %s %s %s' %
                                            sys.exc_info())

            except:
                self.logInterface.ERROR(
                    "handler %s died with exception info %s" %
                    (self.socketMap[s][0], sys.exc_info()))
                self.logInterface.logException()
            sock.close()
            if r:
                self.logInterface.LOG('SM exiting due to r being true') 
                break
                
    def run(self):
        try:
            self._run()
        except:
            self.logInterface.ERROR("BUG! %s, %s, %s" % sys.exc_info())
            out = cStringIO.StringIO()
            traceback.print_tb(sys.exc_info()[2], file=out)
            self.logInterface.ERROR(out.getvalue())
            raise
        
    def reload(self):
        ProcessMgr.ProcessMgr.ProcessMgr.reload(self)
        self._reset()

    def addConnection(self, addrspec, handler_func):
        if addrspec[0] == 'TCP':
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.setblocking(0)
            s.setsockopt (socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            # Make sure the socket will be closed on exec
            fcntl.fcntl (s.fileno(), FCNTL.F_SETFD, 1)
            s.bind(addrspec[1:])
            s.listen(5)
        elif addrspec[0] == 'UNIX':
            try:
                pathstat=os.stat(addrspec[1])
            except OSError:
                pathstat=None
            if pathstat:
                # oops, file exists; is it a UNIX socket?
                if stat.S_ISSOCK(pathstat[0]):
                    # yes, delete it and start over;
                    # let any exception propagate
                    os.unlink(addrspec[1])
                else:
                    # if you've got something else there,
                    # I'm not going to delete it.
                    raise IOError, \
                          "file exists where unix "\
                          "socket is to be created: %s" % addrspec[1]
                    
            s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            s.setblocking(0)
            # Make sure the socket will be closed on exec
            fcntl.fcntl(s.fileno(), FCNTL.F_SETFD, 1)
            s.bind(addrspec[1])
            if len(addrspec) == 3:
                os.chmod(addrspec[1], addrspec[2])
            s.listen(5)
        else:
            raise ValueError, "unknown bind address type"
        self.socketMap[s] = handler_func, addrspec
            
    def stop(self):
        self._reset()

    def _reset(self):
        for k, (f, a) in self.socketMap.items():
            k.close()
            if a[0] == 'UNIX':
                try:
                    os.remove(a[1])
                except:
                    self.logInterface.ERROR(('removal of unix socket %s '
                                             'failed, continuing and hoping'
                                             ' for the best') % a[1])

        self.socketMap = {}
