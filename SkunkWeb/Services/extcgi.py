#  
#  Copyright (C) 2002 Andrew Csillag <drew_csillag@yahoo.com>
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
# $Id: aecgi.py,v 1.2 2002/05/24 20:56:20 smulloni Exp $
# Time-stamp: <01/05/04 17:32:39 smulloni>
########################################################################

from SkunkWeb import Configuration, ServiceRegistry, Hooks
from SkunkWeb.LogObj import DEBUG, DEBUGIT, logException
import os
import select
import sys
import rfc822
import cStringIO

ServiceRegistry.registerService('extcgi')
EXTCGI=ServiceRegistry.EXTCGI

Configuration.mergeDefaults(CGIProgram = None,
                            CGIProgramArgs = (),
                            CGIProgramBase = None)

def _fix(dict):
    nd = {}
    for k,v in dict.items():
        nd[str(k)] = str(v)
    pb = Configuration.CGIProgramBase
    if nd["SCRIPT_NAME"][:len(pb)] == pb:
        remnant = nd["SCRIPT_NAME"][len(pb):]
        if remnant:
            nd["PATH_INFO"] = '/' + remnant
        else:
            nd["PATH_INFO"] = ''
        
        if pb[-1] == '/':
            nd["SCRIPT_NAME"] = pb[:-1]
        else:
            nd["SCRIPT_NAME"] = pb
    return nd

def _dispenv(env):
    s = []
#    for i in ['SCRIPT_NAME', 'REQUEST_URI', 'PATH_INFO']:
    for i in env:
        if env.has_key(i):
            s.append('%s: %s' % (i,env[i]))
    return '\n'.join(s)
    
def _processRequest(conn, sessionDict):
    DEBUG(EXTCGI, 'extcgi Processing Request')
    #dict of environ, headers, stdin
    kid_stdin, parent_to_kid_stdin = os.pipe()
    parent_to_kid_stdout, kid_stdout = os.pipe()
    parent_to_kid_stderr, kid_stderr = os.pipe()
    pid = os.fork()
    if pid: #ok I'm the parent
        DEBUG(EXTCGI, 'child pid is %d' % pid)
        #close kid sides
        os.close(kid_stdin)
        os.close(kid_stdout)
        os.close(kid_stderr)

        stdin = conn._stdin
        if stdin:
            os.write(parent_to_kid_stdin, stdin)

        return _doCGI(conn, pid, parent_to_kid_stdin,
                      parent_to_kid_stdout,
                      parent_to_kid_stderr, stdin)
        
    else: #I'm the kid
        #close parent side of pipes
        os.close(parent_to_kid_stdin)
        os.close(parent_to_kid_stdout)
        os.close(parent_to_kid_stderr)
        #dup kid sides to my stdin/out/err
        os.dup2(kid_stdin, 0)
        os.dup2(kid_stdout, 1)
        os.dup2(kid_stderr, 2)
        env = _fix(conn.env)
        if DEBUGIT(EXTCGI):
            DEBUG(EXTCGI, "environment is %s" % _dispenv(env))
        prog = Configuration.CGIProgram
        args = ( (prog,) + (prog,) +
                 Configuration.CGIProgramArgs +(env,))
        #DEBUG(EXTCGI, 'args is %s' % repr(args))
        try:
            os.execle(*args)
        except:
            logException()
            DEBUG(EXTCGI, "I'm still here! killing self")
            os.kill(os.getpid(), 9)

def _doCGI(conn, pid, stdin,
           stdout,
           stderr, stdindata):

    text = _handleParentSide(pid, stdin, stdout, stderr, stdindata)
    f = cStringIO.StringIO(text)
    respp = rfc822.Message(f)
    for k,v in respp.items():
        conn.responseHeaders[k] = v
    conn.write(f.read())
    
def _handleParentSide(pid, stdin, stdout, stderr, stdindata):
    stderrl = []
    stdoutl = []
    try:
        while 1:
            #DEBUG(EXTCGI, "in while")
            if stdindata:
                inlist = [stdin]
            else:
                inlist = []
            r, w, e = select.select([stdout, stderr], inlist, [], 1)
    
            #DEBUG(EXTCGI, "rwe= %s %s %s" % (r,w,e))
            #DEBUG(EXTCGI, "IOE= %s %s %s" % (stdin, stdout, stderr))
            if stdout in r:
                #DEBUG(EXTCGI, 'attempting to read 1024 bytes from stdout')
                rbytes = os.read(stdout, 1024)
                if not rbytes:
                    r.remove(stdout)
                stdoutl.append(rbytes)
                #DEBUG(EXTCGI, 'got %s bytes' % len(rbytes))
    
            if stderr in r:
                #DEBUG(EXTCGI, 'attempting to read 1024 bytes from stderr')
                rbytes = os.read(stderr, 1024)
                if not rbytes:
                    r.remove(stderr)
                stderrl.append(rbytes)
                #DEBUG(EXTCGI, 'got %s bytes -- %s' % (len(rbytes), rbytes))
    
            if stdin in w:
                if stdindata:
                    #DEBUG(EXTCGI, 'attempting to write %d bytes to stdin')
                    l = os.write(stdin, stdindata)
                    stdindata = stdindata[l:]
                    #DEBUG(EXTCGI, 'wrote %d bytes' % l)

            if not r and not w: #no pipes active, is child alive
                #check on process health
                status = os.waitpid(pid, os.WNOHANG)[1]
                DEBUG(EXTCGI, "status was %s" % repr(status))
                if os.WIFSIGNALED(status): # if process has died abnormally
                    raise "CGIError", "cgi died by signal"
                if os.WIFEXITED(status):
                    exitStatus = os.WEXITSTATUS(status)
                    if exitStatus:# or stderrl:
                        raise "CGIError", ''.join(stderrl)
                    DEBUG(EXTCGI, 'cgi exited ?normally? %d %d' % (status, exitStatus))
                    return ''.join(stdoutl)

    except:
        e, t, tb = sys.exc_info()
        try:
            os.kill(pid, 9) # we screwed up, kill kid
        except:
            pass
        raise e, t, tb
                
def __initHooks():
    import web.protocol
    import SkunkWeb.constants as co

    jobGlob=co.CGI_JOB
    web.protocol.HandleConnection[jobGlob]=_processRequest

__initHooks()
