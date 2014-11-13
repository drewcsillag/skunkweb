#  
#  Copyright (C) 2002 Andrew Csillag <drew_csillag@yahoo.com>
#  
#      You may distribute under the terms of either the GNU General
#      Public License or the SkunkWeb License, as specified in the
#      README file.
#   
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
                            CGIProgramBase = '')

def _fix(dict): #fixup the environment variables
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
        
        if pb and pb[-1] == '/':
            nd["SCRIPT_NAME"] = pb[:-1]
        else:
            nd["SCRIPT_NAME"] = pb
    nd["PATH_TRANSLATED"] = Configuration.CGIProgram#os.path.split(Configuration.CGIProgram)[0]
    return nd

def _dispenv(env):
    s = []
    for i in env.keys():
        s.append('%s: %s' % (i,env[i]))
    return '\n'.join(s)

def _processRequest(conn, sessionDict):
    DEBUG(EXTCGI, 'extcgi Processing Request')
    #dict of environ, headers, stdin
    kid_stdin, parent_to_kid_stdin = os.pipe()
    parent_to_kid_stdout, kid_stdout = os.pipe()
    parent_to_kid_stderr, kid_stderr = os.pipe()
    pid = os.fork()
    try:
        if pid: #ok I'm the parent
            DEBUG(EXTCGI, 'child pid is %d' % pid)
            #close kid sides
            os.close(kid_stdin)
            os.close(kid_stdout)
            os.close(kid_stderr)

            stdin = conn._stdin

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
            DEBUG(EXTCGI, 'args is %s' % repr(args))
            oldpwd = os.getcwd()
            try:
                os.chdir(os.path.split(env["PATH_TRANSLATED"])[0])
                os.execle(*args)

            finally:
                os.chdir(oldpwd)
    except:
        if pid == 0: #I'm the kid
            logException()
            #give the parent some info as to why I died
            os.write(kid_stderr, "exception executing CGI : %s %s" % (
                sys.exc_info()[0], sys.exc_info()[1]))
            DEBUG(EXTCGI, "I'm still here! killing self");
            os.kill(os.getpid(), 9)

        else: #I'm the parent
            e, t, tb = sys.exc_info()
            try:
                os.kill(pid, 9) # we screwed up, kill kid
            except: #in event that it's already dead, that's ok too
                pass
            raise e, t, tb

def _doCGI(conn, pid, stdin, stdout, stderr, stdindata):
    text = _handleParentSide(pid, stdin, stdout, stderr, stdindata)
    f = cStringIO.StringIO(text)
    respp = rfc822.Message(f)
    for k,v in respp.items():
        conn.responseHeaders[k] = v
    conn.write(f.read())
    
def _handleParentSide(pid, stdin, stdout, stderr, stdindata):
    stderrl = []
    stdoutl = []
    while 1:
        if stdindata: #if anything left to write to the CGI
            inlist = [stdin]
        else:
            inlist = []
        r, w, e = select.select([stdout, stderr], inlist, [], 1)

        if stdout in r:
            rbytes = os.read(stdout, 1024)
            if not rbytes:
                r.remove(stdout)
            stdoutl.append(rbytes)

        if stderr in r:
            rbytes = os.read(stderr, 1024)
            if not rbytes:
                r.remove(stderr)
            stderrl.append(rbytes)

        if stdin in w:
            if stdindata:
                l = os.write(stdin, stdindata)
                stdindata = stdindata[l:]

        if not r and not w: #no pipes active, is child alive
            #check on process health
            status = os.waitpid(pid, os.WNOHANG)[1]
            #DEBUG(EXTCGI, "status was %s" % repr(status))

            if os.WIFSIGNALED(status): # if process has died abnormally
                raise "CGIError", (
                    "cgi died by signal %s: %s" % (os.WTERMSIG(status),
                                                   ''.join(stderrl)))

            if os.WIFEXITED(status): # if exited via exit()
                exitStatus = os.WEXITSTATUS(status)
                if exitStatus:# or stderrl:
                    raise "CGIError", ''.join(stderrl)
                DEBUG(EXTCGI, 'cgi exited normally %d %d' % (
                    status, exitStatus))
                return ''.join(stdoutl)
                
def __initHooks():
    import web.protocol
    import SkunkWeb.constants as co

    jobGlob=co.CGI_JOB
    web.protocol.HandleConnection[jobGlob]=_processRequest

__initHooks()
