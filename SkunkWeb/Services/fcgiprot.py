#  
#  Copyright (C) 2001 Andrew T. Csillag <drew_csillag@geocities.com>
#  
#      You may distribute under the terms of either the GNU General
#      Public License or the SkunkWeb License, as specified in the
#      README file.
#   
# Time-stamp: <01/05/04 17:32:39 smulloni>
########################################################################

from SkunkWeb import Configuration, ServiceRegistry, Hooks
from SkunkWeb.LogObj import DEBUG, ERROR
import requestHandler.protocol
import requestHandler.requestHandler
import SocketScience
import skunklib
import fcgi

ServiceRegistry.registerService('fcgiprot')
FCGIPROT=ServiceRegistry.FCGIPROT

RequestFailed=Hooks.KeyedHook()

class sockfile:
    def __init__(self):
        self.contents=[]

    def send(self, c):
        DEBUG(FCGIPROT, 'sending %s' % c)
        self.contents.append(c)

    def value(self):
        return ''.join(self.contents)

    def close(self):
        pass
    
class FCGIProtocol(requestHandler.protocol.Protocol):
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

        f = self.fcgi = fcgi.FCGI(sock)
        ret =  {'stdin': f.inp.getvalue(),
             'environ': f.env,
             'headers': self.makeHeaders(f.env)}
        DEBUG(FCGIPROT, 'reqdata is %s' % ret)
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
        s = self.fcgi.conn
        self.fcgi.conn = sockfile()
        self.fcgi.out.write(data)
        self.fcgi.Finish()
        DEBUG(FCGIPROT, "response is %s" % self.fcgi.conn.value())
        return self.fcgi.conn.value()

    

Configuration.mergeDefaults(FCGIListenPorts=['TCP:localhost:9999'])
if Configuration.FCGIListenPorts:
    requestHandler.requestHandler.addRequestHandler(
        FCGIProtocol(), Configuration.FCGIListenPorts)

########################################################################
# $Log: fcgiprot.py,v $
# Revision 1.2  2003/05/01 20:45:53  drew_csillag
# Changed license text
#
# Revision 1.1  2001/09/06 19:16:33  drew_csillag
# added
#
########################################################################
