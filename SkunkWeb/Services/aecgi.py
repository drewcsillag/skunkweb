#  
#  Copyright (C) 2001 Jacob Smullyan <smulloni@smullyan.org>
#  
#      You may distribute under the terms of either the GNU General
#      Public License or the SkunkWeb License, as specified in the
#      README file.
#   
# Time-stamp: <01/05/04 17:32:39 smulloni>
########################################################################

from SkunkWeb import Configuration, ServiceRegistry, Hooks
from SkunkWeb.LogObj import DEBUG
import requestHandler.protocol
import requestHandler.requestHandler
from requestHandler.protocol import RequestFailed
import SocketScience

import marshal

ServiceRegistry.registerService('aecgi')
AECGI=ServiceRegistry.AECGI

class AecgiProtocol(requestHandler.protocol.Protocol):
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
        SocketScience.send_it_all(sock, '\0')
        DEBUG(AECGI, 'sent sentinel')
        lenDataStr = SocketScience.read_this_many(sock, 10)
        DEBUG(AECGI, 'read length')
        lenData = int(lenDataStr)
        data = SocketScience.read_this_many(sock, lenData)
        DEBUG(AECGI, 'read request data')
        marcia=marshal.loads(data)
        return marcia

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
        return "%10d%s" %(len(data), data)

def _serverStartHook(*args, **kw):
    requestHandler.requestHandler.addRequestHandler(AecgiProtocol(),
                                                    Configuration.AecgiListenPorts)    

Configuration.mergeDefaults(AecgiListenPorts=['TCP:localhost:9888'])
if Configuration.AecgiListenPorts:
    Hooks.ServerStart.append(_serverStartHook)


########################################################################
# $Log: aecgi.py,v $
# Revision 1.4  2003/05/01 20:45:53  drew_csillag
# Changed license text
#
# Revision 1.3  2002/07/19 16:21:02  smulloni
# removed spurious dependencies on aecgi from httpd and templating by
# moving the RequestFailed hook into requestHandler.
#
# Revision 1.2  2002/05/24 20:56:20  smulloni
# now add request handlers in ServerStart hook
#
# Revision 1.1.1.1  2001/08/05 14:59:55  drew_csillag
# take 2 of import
#
#
# Revision 1.5  2001/07/09 20:38:40  drew
# added licence comments
#
# Revision 1.4  2001/05/04 21:30:40  smullyan
# a little too fast there ...
#
# Revision 1.3  2001/05/04 21:29:09  smullyan
# another typo!
#
# Revision 1.2  2001/05/04 21:26:56  smullyan
# correcting typo.
#
# Revision 1.1  2001/05/04 18:38:47  smullyan
# architectural overhaul, possibly a reductio ad absurdum of the current
# config overlay technique.
#
########################################################################
