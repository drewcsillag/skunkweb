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
# $Id: aecgi.py,v 1.5 2001/07/09 20:38:40 drew Exp $
# Time-stamp: <01/05/04 17:32:39 smulloni>
########################################################################

from SkunkWeb import Configuration, ServiceRegistry, Hooks
from SkunkWeb.LogObj import DEBUG
import requestHandler.protocol
import requestHandler.requestHandler
import SocketScience

import marshal

ServiceRegistry.registerService('aecgi')
AECGI=ServiceRegistry.AECGI

RequestFailed=Hooks.KeyedHook()

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

    

Configuration.mergeDefaults(AecgiListenPorts=['TCP:localhost:9888'])
if Configuration.AecgiListenPorts:
    requestHandler.requestHandler.addRequestHandler(AecgiProtocol(),
                                                    Configuration.AecgiListenPorts)

########################################################################
# $Log: aecgi.py,v $
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
