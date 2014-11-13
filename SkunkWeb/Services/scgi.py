#  
#  Copyright (C) 2001 Andrew T. Csillag <drew_csillag@geocities.com>
#  
#      You may distribute under the terms of either the GNU General
#      Public License or the SkunkWeb License, as specified in the
#      README file.
#   
# Time-stamp: <01/05/04 17:32:39 smulloni>
########################################################################
#http://www.mems-exchange.org/software/scgi/

from SkunkWeb import Configuration, ServiceRegistry, Hooks
from SkunkWeb.LogObj import DEBUG, ERROR
import requestHandler.protocol
import requestHandler.requestHandler
import SocketScience
import skunklib

ServiceRegistry.registerService('scgi')
SCGI=ServiceRegistry.SCGI

RequestFailed=Hooks.KeyedHook()

def recvstr(sock):
    l=sock.recv(2)
    #print 'ini l', l
    while l[-1] != ':':
        ll = len(l)
        l += sock.recv(1)
        if len(l) == ll:
            raise "socketbroke"

    leng = int(l[:-1])
    ret = ''
    while leng:
        val = sock.recv(leng)
        if not val:
            raise "socketbroke"
        leng-=len(val)
        ret += val

    sock.recv(1)
    return ret

def parseHeaders(h):
    nh = h.split('\0')
    #print 'lennh', len(nh), nh
    hd = {}
    for i in range(0,len(nh)-1,2):
        hd[nh[i]] = nh[i+1]
    return hd

class SCGIProtocol(requestHandler.protocol.Protocol):
    """
    protocol used to communicate with Apache via mod_skunkweb
    """
    
    def marshalRequest(self, sock, sessionDict):
        """
        Sends a handshake byte, obtains the content length from
        the value of the first ten bytes read, and then reads no
        more than that amount, which it marshals with the 'marshal'
        module. Finally, returns the marshalled request data
        """

        headers = parseHeaders(recvstr(sock))
        cl = int(headers.get('CONTENT_LENGTH', '0'))
        if cl:
            body = sock.recv(cl)
        else:
            body = ''

        ret =  {'stdin': body,
                'environ': headers,
                'headers': self.makeHeaders(headers)}
        DEBUG(SCGI, 'reqdata is %s' % ret)
        return ret

    def makeHeaders(self, env):
        h = {}
        for k,v in env.items():
            if k[:5] == 'HTTP_':
                h[skunklib.normheader(k[5:].replace('_','-'))] = v
        return h
    
    def marshalResponse(self, response, sessionDict):
        '''
        return response data, with the first ten bytes indicating
        the content length.
        '''
        return self._marshalData(response)
    
    def marshalException(self, exc_text, sessionDict):
        '''
        should return response data appropriate for the current exception.
        '''
        res=RequestFailed(Configuration.job,
                          exc_text,
                          sessionDict)
        if res:
            return self._marshalData(res)
        else:
            return self._marshalData(exc_text)

    def _marshalData(self, data):
        return data

Configuration.mergeDefaults(SCGIListenPorts=['TCP:localhost:9999'])
if Configuration.SCGIListenPorts:
    requestHandler.requestHandler.addRequestHandler(
        SCGIProtocol(), Configuration.SCGIListenPorts)

########################################################################
# $Log: scgi.py,v $
# Revision 1.3  2003/05/01 20:45:53  drew_csillag
# Changed license text
#
# Revision 1.2  2002/06/18 20:09:38  drew_csillag
# fixed typo that caused problems on POSTs
#
# Revision 1.1  2002/06/17 19:29:52  drew_csillag
# added
#
#
########################################################################
