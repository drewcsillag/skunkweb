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
# $Id: fcgiprot.py,v 1.1 2001/09/06 19:16:33 drew_csillag Exp $
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
            body = r.recv(cl)
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
# $Log: fcgiprot.py,v $
#
########################################################################
