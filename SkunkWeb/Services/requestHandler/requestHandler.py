#  
#  Copyright (C) 2001 Jacob Smullyan <smulloni@smullyan.org>
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
# $Id: requestHandler.py,v 1.5 2002/06/18 20:09:59 drew_csillag Exp $
# Time-stamp: <01/05/09 17:48:12 smulloni>
########################################################################

from SkunkWeb import Configuration, ConfigAdditives, constants
from SkunkWeb.LogObj import DEBUG, LOG, DEBUGIT, ERROR, logException
from SkunkWeb.Hooks import KeyedHook
from SkunkWeb.ServiceRegistry import REQUESTHANDLER
from SkunkExcept import *
from protocol import PreemptiveResponse
import exceptions
import select
from signal_plus import signal_plus
import signal
import socket
import types
import SocketScience
from SkunkExcept import SkunkCriticalError

BeginSession=KeyedHook()
InitRequest=KeyedHook()
HandleRequest=KeyedHook()
PostRequest=KeyedHook()
CleanupRequest=KeyedHook()
EndSession=KeyedHook()

def _processRequest(sock, addr, protocolImpl):
    
    DEBUG(REQUESTHANDLER, "in _processRequest(%s, %s, %s)" % (sock,
                                                              addr,
                                                              protocolImpl))
    requestData, responseData, sessionDict=None, None, {}
    _beginSession(sock, sessionDict)
    
    DEBUG(REQUESTHANDLER, "starting job: %s" % Configuration.job)

    # loop until connection is closed
    while 1:
        try:
            signal_plus.blockTERM()
            signal.signal(signal.SIGALRM, SIGALRMHandler)
            signal.alarm(Configuration.DocumentTimeout)
            try:
                try:
                    DEBUG(REQUESTHANDLER, 'marshalling request')
                    requestData = protocolImpl.marshalRequest(sock, sessionDict)

                    DEBUG(REQUESTHANDLER, 'InitRequest hook')
                    InitRequest(Configuration.job, requestData, sessionDict)
                    
                except PreemptiveResponse, pr:
                    DEBUG(REQUESTHANDLER, 'got preemptive response')
                    responseData=protocolImpl.marshalResponse(pr.responseData,
                                                              sessionDict)
                    
                else:
                    DEBUG(REQUESTHANDLER, 'handling request')
                    rawResponse=HandleRequest(Configuration.job,
                                              requestData,
                                              sessionDict)

                    DEBUG(REQUESTHANDLER, 'response returned: %s' % str(rawResponse))
                    DEBUG(REQUESTHANDLER, 'marshalling response')
                    responseData=protocolImpl.marshalResponse(rawResponse,
                                                              sessionDict)
            except:
                try:
                    # the current exception is available anyway, so is not passed;
                    # perhaps nothing should be
                    DEBUG(REQUESTHANDLER, 'marshalling exception')
                    responseData=protocolImpl.marshalException(logException(),
                                                               sessionDict)
                except:
                    logException()
        finally:     
            DEBUG(REQUESTHANDLER, 'sending response')
            _sendResponse(sock,
                          responseData,
                          requestData,
                          sessionDict)
        
            signal.alarm(0)
            signal_plus.unblockTERM()

        # the protocol can close the connection by return a negative timeout;
        # sessionDict allows it to reference state that has been stored there.
        timeout=protocolImpl.keepAliveTimeout(sessionDict)
        if (timeout<0) or not _canRead(sock, timeout):
            _endSession(sessionDict)
            return

def _canRead(sock, timeout):
    sock.setblocking(1)
    input, output, exc=select.select([sock],
                                     [],
                                     [],
                                     timeout)
    DEBUG(REQUESTHANDLER, "input for _canRead select: %s" % input)
    # sanity check
    if input and not input[0].recv(1, socket.MSG_PEEK):
        return 0
    return len(input)

class DocumentTimeout(exceptions.Exception): pass                
        
def SIGALRMHandler(*args):
    Configuration.trim()
    ERROR('Throwing timeout exception')
    signal.alarm(1) # in case they catch this exception
    raise DocumentTimeout, "timeout reached"



def _beginSession(sock, sessionDict):
    # capture the ip & port (or path, for a unix socket)
    # on which the request came, for scoping of configuration
    # data on their basis
    ip, port, unixpath=None, None, None
    try:      
        addr=sock.getsockname()
        if type(addr)==types.TupleType:
            ip, port=addr
        else:
            unixpath=addr
    except:
        ERROR("failed to read addr off socket!")
        logException()
        raise

    if ip and port:
        sessionDict[constants.IP]=ip
        sessionDict[constants.PORT]=port
    else:
        sessionDict[constants.UNIXPATH]=unixpath
    
    # get configuration data for the job
    Configuration.scope(sessionDict)
    
    # job must be defined, or else die here
    if Configuration.job==None:
        message="No job specified for service on %s:%d, "\
                 "request cannot be processed!" % (ip, port)
        ERROR(message)
        raise SkunkCriticalError, message
    
    BeginSession(Configuration.job, sock, sessionDict)

    

def _sendResponse(sock,
                  responseData,                 
                  requestData,
                  sessionDict):
    try:
        SocketScience.send_it_all(sock, responseData)
    except:
        logException()

    # reset alarm
    signal.alarm(Configuration.PostResponseTimeout)
    
    try:
        DEBUG(REQUESTHANDLER, 'post request hook')
        PostRequest(Configuration.job, requestData, sessionDict)
    except:
        logException()                
    try:
        DEBUG(REQUESTHANDLER, "cleaning up")
        CleanupRequest(Configuration.job, requestData, sessionDict)
    except:
        logException()

        

def _endSession(sessionDict):
    try:
        EndSession(Configuration.job, sessionDict)
    except:
        logException()
    Configuration.trim()

    

class RequestHandler:
    """
    an object, the creation of which adds a service
    to the server on the specified ports with the specified
    protocol.
    """
    def __init__(self, protocol, ports):
        self.protocol=protocol
        self.ports=ports
        self.__initPorts()

    def __initPorts(self):
        from SkunkWeb import Server
        LOG('initializing ports')
        for port in self.ports:
            bits = port.split(':')
            if bits[0] == 'TCP':
                bits[2] = int(bits[2])
            elif bits[0] == 'UNIX':
                if len(bits)>=3:
                    bits[2] = int(bits[2], 8)
            else: raise "unrecognized socket specifier: %s" % port
            DEBUG(REQUESTHANDLER, 'adding Service: %s, %s' %((tuple(bits)),
                                                             self))
            Server.addService(tuple(bits), self)
            
    def __call__(self, sock, addr):
        DEBUG(REQUESTHANDLER, "calling RequestHandler %s" % self)    
        _processRequest(sock, addr, self.protocol)
 
########################################################################
            

def addRequestHandler(protocol, ports):
    RequestHandler(protocol, ports)

########################################################################
# $Log: requestHandler.py,v $
# Revision 1.5  2002/06/18 20:09:59  drew_csillag
# SkunkExcept
# 	wasn't imported so could cause problems in certain cases, fixed.
#
# Revision 1.4  2002/06/12 18:00:41  drew_csillag
# Now will reraise the timeout exception every second after a timeout occurs
# in the hopes that if they ignore the first one, subsequent throws won't be
# caught.  Also lets the template try to deal with timeouts a bit better should
# they choose to do so.
#
# Revision 1.3  2001/10/30 15:40:11  drew_csillag
# fixed a debug message so it won't barf on a tuple
#
# Revision 1.2  2001/10/02 00:06:35  smulloni
# fixes for unix sockets, which were broken due to profound cognitive
# impairment.
#
# Revision 1.1.1.1  2001/08/05 15:00:05  drew_csillag
# take 2 of import
#
#
# Revision 1.22  2001/07/09 20:38:40  drew
# added licence comments
#
# Revision 1.21  2001/05/09 21:47:05  smullyan
# added sanity check after select, peeking one byte ahead on the socket, in
# _canRead.
#
# Revision 1.20  2001/05/09 19:42:25  smullyan
# added two new hooks, BeginSession and EndSession.
#
# Revision 1.19  2001/05/04 18:38:50  smullyan
# architectural overhaul, possibly a reductio ad absurdum of the current
# config overlay technique.
#
# Revision 1.18  2001/05/03 17:26:11  smullyan
# added an IP pseudo-directive to SkunkWeb.ConfigAdditives; Host now matches
# strictly (perhaps it should be a glob); port and ip are now put in
# sessionDict by requestHandler; HTTPConnection's "host" field is now the host
# header, if any, with the port removed.
#
# Revision 1.17  2001/05/03 16:14:58  smullyan
# modifications for scoping.
#
# Revision 1.16  2001/04/25 20:18:46  smullyan
# moved the "experimental" services (web_experimental and
# templating_experimental) back to web and templating.
#
# Revision 1.15  2001/04/23 22:53:55  smullyan
# added support for keep-alive.  Fixed server name (I had left out "SkunkWeb"
# and only included the version).
#
# Revision 1.14  2001/04/23 17:30:08  smullyan
# basic fixes to basic auth and httpd; added KeepAliveTimeout to requestHandler,
# using select().
#
# Revision 1.13  2001/04/23 04:55:47  smullyan
# cleaned up some older code to use the requestHandler framework; modified
# all hooks and Protocol methods to take a session dictionary argument;
# added script to find long lines to util.
#
# Revision 1.12  2001/04/18 22:46:26  smullyan
# first gropings towards a web server.
#
# Revision 1.11  2001/04/16 17:52:59  smullyan
# some long lines split; bug in Server.py fixed (reference to deleted
# Configuration module on reload); logging of multiline messages can now
# configurably have or not have a log stamp on every line.
#
# Revision 1.10  2001/04/04 20:00:18  smullyan
# The configuration setting, DocumentTimeout, was being used in requestHandler
# while its default was being set in templating_experimental -- fixed.  The
# alarm is now reset after the response is set, and a PostResponseTimeout
# takes over for the remaining two hooks.
#
# Revision 1.9  2001/04/04 16:28:02  smullyan
# CodeSources.py wasn't calling the installIntoTraceback function; fixed.
# Remote service now handles exceptions better.  Code equivalent to that in
# test.py will need to become part of the templating_experimental service.
#
# Revision 1.8  2001/04/04 14:46:29  smullyan
# moved KeyedHook into SkunkWeb.Hooks, and modified services to use it.
#
# Revision 1.7  2001/04/02 22:31:41  smullyan
# bug fixes.
#
# Revision 1.6  2001/04/01 07:27:34  smullyan
# after various wacky experiments, moved a prototype of a new hook
# implementation into requestHandler.hooks.py.
#
# Revision 1.5  2001/03/31 06:13:37  smullyan
# more reworking of keyed hooks.
#
# Revision 1.4  2001/03/29 23:02:25  smullyan
# annotated job.py with indications of grandiose plans.  Job integration.
#
# Revision 1.3  2001/03/29 21:54:24  smullyan
# removed dead method from Protocol.
#
# Revision 1.2  2001/03/29 21:47:52  smullyan
# first integration of jobs into requestHandler.
#
# Revision 1.1  2001/03/29 20:17:10  smullyan
# experimental, non-working code for requestHandler and derived services.
#
