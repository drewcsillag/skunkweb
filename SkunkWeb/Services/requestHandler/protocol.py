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
# $Id: protocol.py,v 1.8 2001/07/09 20:38:40 drew Exp $
# Time-stamp: <01/05/03 16:59:54 smulloni>
########################################################################

# abstract class for protocols used in handling request and response

class Protocol:
    """
    abstract class for protocols used in handling request and response
    """

    def marshalRequest(self, socket, sessionDict):
        '''
        should return the marshalled request data
        '''
        raise NotImplementedError

    def marshalResponse(self, response, sessionDict):
        '''
        should return response data
        '''
        raise NotImplementedError

    def marshalException(self, exc_text, sessionDict):
        '''
        should return response data appropriate for the current exception.
        '''
        raise NotImplementedError

    def keepAliveTimeout(self, sessionDict):
        '''
        how long to keep alive a session.  A negative number will terminate the
        session.
        '''
        return -1

        
class PreemptiveResponse(Exception):
    
    def __init__(self, marshalledResponse=None):
        self.responseData=marshalledResponse

########################################################################
# $Log: protocol.py,v $
# Revision 1.8  2001/07/09 20:38:40  drew
# added licence comments
#
# Revision 1.7  2001/05/04 18:38:50  smullyan
# architectural overhaul, possibly a reductio ad absurdum of the current
# config overlay technique.
#
# Revision 1.6  2001/04/25 20:18:45  smullyan
# moved the "experimental" services (web_experimental and
# templating_experimental) back to web and templating.
#
# Revision 1.5  2001/04/23 04:55:46  smullyan
# cleaned up some older code to use the requestHandler framework; modified
# all hooks and Protocol methods to take a session dictionary argument;
# added script to find long lines to util.
#
# Revision 1.4  2001/04/18 22:46:26  smullyan
# first gropings towards a web server.
#
# Revision 1.3  2001/04/02 00:02:52  smullyan
# integration of new hook framework (in requestHandler.hooks) into
# web_experimental and templating_experimental services.
#
# Revision 1.2  2001/03/29 21:54:24  smullyan
# removed dead method from Protocol.
#
