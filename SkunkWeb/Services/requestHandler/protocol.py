#  
#  Copyright (C) 2001 Jacob Smullyan <smulloni@smullyan.org>
#  
#      You may distribute under the terms of either the GNU General
#      Public License or the SkunkWeb License, as specified in the
#      README file.
#   
# Time-stamp: <01/05/03 16:59:54 smulloni>
########################################################################

# not used here, but used by convention
# by other services in Protocol.marshalException
# so they need not depend on one another
import hooks
RequestFailed=hooks.KeyedHook()


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

