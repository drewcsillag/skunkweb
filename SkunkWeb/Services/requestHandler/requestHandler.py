#  
#  Copyright (C) 2001 Jacob Smullyan <smulloni@smullyan.org>
#  
#      You may distribute under the terms of either the GNU General
#      Public License or the SkunkWeb License, as specified in the
#      README file.
#   
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
import errno

BeginSession=KeyedHook()
InitRequest=KeyedHook()
HandleRequest=KeyedHook()
PostRequest=KeyedHook()
CleanupRequest=KeyedHook()
EndSession=KeyedHook()

def _processRequest(sock, addr, protocolImpl):
    
#    DEBUG(REQUESTHANDLER, "in _processRequest(%s, %s, %s)" % (sock,
#                                                              addr,
#                                                              protocolImpl))
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
#                    DEBUG(REQUESTHANDLER, 'marshalling request')
                    requestData = protocolImpl.marshalRequest(sock, sessionDict)

#                    DEBUG(REQUESTHANDLER, 'InitRequest hook')
                    InitRequest(Configuration.job, requestData, sessionDict)
                    
                except PreemptiveResponse, pr:
#                    DEBUG(REQUESTHANDLER, 'got preemptive response')
                    responseData=protocolImpl.marshalResponse(pr.responseData,
                                                              sessionDict)
                    
                else:
#                    DEBUG(REQUESTHANDLER, 'handling request')
                    rawResponse=HandleRequest(Configuration.job,
                                              requestData,
                                              sessionDict)

#                    DEBUG(REQUESTHANDLER, 'response returned: %s' % str(rawResponse))
#                    DEBUG(REQUESTHANDLER, 'marshalling response')
                    responseData=protocolImpl.marshalResponse(rawResponse,
                                                              sessionDict)
            except:
                try:
                    # the current exception is available anyway, so is not passed;
                    # perhaps nothing should be
#                    DEBUG(REQUESTHANDLER, 'marshalling exception')
                    responseData=protocolImpl.marshalException(logException(),
                                                               sessionDict)
                except:
                    logException()
        finally:     
#            DEBUG(REQUESTHANDLER, 'sending response')
            _sendResponse(sock,
                          responseData,
                          requestData,
                          sessionDict)
        
            signal.alarm(0)
            signal_plus.unblockTERM()

        # the protocol can close the connection by return a negative timeout;
        # sessionDict allows it to reference state that has been stored there.
        timeout=protocolImpl.keepAliveTimeout(sessionDict)
        try:
            if (timeout<0) or not _canRead(sock, timeout):
                _endSession(sessionDict)
                return
        except socket.error, v:
            assert v.args
            if v.args[0] != errno.ECONNRESET: #ignore conn reset exceptions
                raise
            _endSession(sessionDict)
            return

def _canRead(sock, timeout):
    sock.setblocking(1)
    input, output, exc=select.select([sock],
                                     [],
                                     [],
                                     timeout)
#    DEBUG(REQUESTHANDLER, "input for _canRead select: %s" % input)
    # sanity check
    try:
        if input and not input[0].recv(1, socket.MSG_PEEK):
            return 0
    except socket.error:
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
    except IOError, en:  #ignore broken pipes
        if en != errno.EPIPE:
            logException()
    except:
        logException()

 
    # reset alarm
    signal.alarm(Configuration.PostResponseTimeout)
    
    try:
#        DEBUG(REQUESTHANDLER, 'post request hook')
        PostRequest(Configuration.job, requestData, sessionDict)
    except:
        logException()                
    try:
#        DEBUG(REQUESTHANDLER, "cleaning up")
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
#        DEBUG(REQUESTHANDLER, "calling RequestHandler %s" % self)    
        _processRequest(sock, addr, self.protocol)
 
########################################################################
            

def addRequestHandler(protocol, ports):
    RequestHandler(protocol, ports)

