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
"""
A static process manager (no grow/shrink) that can handle reloads.
Derive from the ProcessMgr class to do it.

Used currently by the AED to handle management of the child processes and
server restart.  If children die, it will create new children to take their
place. 

If you want to write a multi-process, static number of kids (until reload
anyway) server, this is for you.

"""
import time
import signal
import os
import sys

from SkunkExcept import *

class DummyLogger:
    def LOG(self, *args, **kwargs):
        self._log(args, kwargs)        
    def ERROR(self, *args, **kwargs):
        self._log(args, kwargs)
    def _log(self, args, kwargs):
        print args, kwargs
        sys.stdout.flush()
    
# Some exceptions
class _SignalException(SkunkStandardError):
    def __init__(self, sig_name ):
        SkunkStandardError.__init__ ( self, 'signal caught: %s' % sig_name )

class _TermSignal ( _SignalException ):
    def __init__ ( self ):
        _SignalException.__init__ ( self, 'SIGTERM' )

class _HupSignal ( _SignalException ):
    def __init__ ( self ):
        _SignalException.__init__ ( self, 'SIGHUP' )

#the process manager
class ProcessMgr:
    """a fixed, preforking process manager"""
    def __init__( self, numProcs = 0, maxKillTime = 5, pidFile=None,
                  pollPeriod = 5, logInterface = DummyLogger() ):
        
        self.numProcs = numProcs
        self.pidFile = pidFile
        self.pollPeriod = pollPeriod
        self.maxKillTime = maxKillTime
        self.logInterface = logInterface
        self._modules = None
        self._children = {}

        #catch sigchild and reap kids (mainly to interrupt a sleep() call)
        signal.signal(signal.SIGCHLD, self._SIGCHLDHandler)

        #handle these signals to propagate them
        signal.signal(signal.SIGHUP, self._SIGHUPHandler)
        signal.signal(signal.SIGTERM, self._SIGTERMHandler)

        self._sig = None

    def _SIGCHLDHandler(self, *args):
        pass

    def _SIGHUPHandler(self, *args):
        self._sig = "SIGHUP"
            
    def _SIGTERMHandler(self, *args):
        self._sig = "SIGTERM"

    def moduleSnapshot( self ):
        """
        Take a snapshot of modules that need to stick through inits()
        """
        self._modules = sys.modules.keys()
        self._modules.sort()

    def periodic( self ):
        """
        override this method if you want to do something in the parent
        process periodically
        """
        pass

    def init( self ):
        """override this method to do something before the server starts
        """
        pass

    def run( self ):
        """override this method to actually do something in the child
        process
        """
        raise NotImplementedError, 'run method not overridden'

    def mainloop( self ):
        """the method used to actually fire off the server"""
        self.init()
        if self.numProcs == 1:
            self.logInterface.LOG('running in non-daemon mode')
            #do no detach
            self.run()
            sys.exit()

        #become daemon and process group leader
        self.logInterface.LOG("daemonizing...")
        if os.fork():
            sys.exit()
        if os.fork():
            sys.exit()
        os.setsid()

        #write the pid file
        open(self.pidFile,'w').write('%s' % os.getpid())

        while 1:
            try:
                #do any periodic tasks
                self.periodic()

                #reap any process corpses
                self._reap()

                #are we short of procs, spawn some new ones
                if len( self._children ) < self.numProcs:
                    self._spawn()

                #wait, we'll be interrupted by SIGCHLD if anything
                #important happens
                try: time.sleep(self.pollPeriod)
                except: pass

                #any coolio signals to do something about?
                if self._sig == 'SIGTERM': raise _TermSignal 
                if self._sig == 'SIGHUP': raise _HupSignal
                
            except (_TermSignal, KeyboardInterrupt):
                #server shutdown
                self.logInterface.LOG('shutting down')
                self._die()
                self.stop()
                try:
                    os.unlink( self.pidFile )
                except:
                    self.logInterface.WARN('pid file already gone!')
                self.logInterface.LOG('server shut down')
                sys.exit()

            except _HupSignal:
                #nice restart
                self.logInterface.LOG('restarting')
                self._die()
                self.reload()
                self._sig = None
                self.init()

    def _reap( self ):
        while 1:
            try:
                pid, exitStatus = os.waitpid(-1, os.WNOHANG)
                if pid == 0:
                    break
                self.logInterface.LOG(
                    'child, pid %d died status %s' % (pid, exitStatus))
                del self._children[ pid ]
            except:
                break

    def _spawn( self ):
        numToSpawn = self.numProcs - len( self._children )
        if not numToSpawn:
            return

        self.logInterface.LOG('spawning %d child(ren)' % numToSpawn)
        for i in range(self.numProcs - len( self._children )):
            self.logInterface.LOG('spawning child')
            kidPid = os.fork()
            if not kidPid: #we're the kid
                #set the signal handlers to their normal bit
                signal.signal( signal.SIGCHLD, signal.SIG_DFL )
                signal.signal( signal.SIGHUP, signal.SIG_DFL )
                signal.signal( signal.SIGTERM, signal.SIG_DFL )
                self.run()
                sys.exit()
            self._children[ kidPid ] = 1

    def _die( self ):
        curTime = time.time()

        #nuke all processes
        self.logInterface.LOG('killing all children with TERM')
        for pid in self._children.keys():
            os.kill( pid, signal.SIGTERM )
            
        #wait for them to die
        while len( self._children ):
            try: time.sleep(1)
            except: pass
            self._reap()
            if time.time() - curTime > self.maxKillTime:
                break

        if len( self._children ): #grrr, they're still there!!!
            #kill them hard
            self.logInterface.LOG('killing remaining children with KILL')
            for pid in self._children.keys():
                os.kill( pid, signal.SIGKILL )

        #now wait for them to die
        while len( self._children ):
            try: time.sleep(1)
            except: pass
            self._reap()

    def reload( self ):
        """override this method to handle reload events.
        You probably want to call your superclass first!, then do
        what you must.
        """
        
        # Check that snapshot_modules been called
        if not self.__dict__.has_key ( '_modules' ) or not self._modules:
             raise SkunkRuntimeError, 'moduleSnapshot() was not called' 

        # Just reload ALL the modules but the ones we keep 
        for m in sys.modules.keys():
            if m not in self._modules:
                if sys.modules[m]:
                    mm = sys.modules[m]
                    bits = m.split('.')
                    if len(bits) > 1: #module is part of a package
                        #sys.__stderr__.write('module %s is in pkg\n' % mm)
                        parent = '.'.join(bits[:-1])
                        if sys.modules.has_key(parent):
                            #sys.__stderr__.write('parent of %s is\n' % m)
                            pmod = sys.modules[parent]
                            if (
                                hasattr(parent, bits[-1])
                                and id(getattr(parent, bits[-1])) == id(mm)):
                                #delete module from parent package
                                #sys.__stderr__.write('deleting %s from parent\n'
                                #                     % m)
                                delattr(parent, bits[-1])

                    # Not None, tear down its dictionary
                    mm.__dict__.clear()
                    mm.__mname__ = m
                                
                    
                del sys.modules[m]

    def stop( self ):
        """override this to be called when the server is shut down
        """
        pass
