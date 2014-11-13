#  
#  Copyright (C) 2001 Jacob Smullyan <smulloni@smullyan.org>
#  
#      You may distribute under the terms of either the GNU General
#      Public License or the SkunkWeb License, as specified in the
#      README file.
#   
# Time-stamp: <01/05/04 14:28:18 smulloni>

from requestHandler.protocol import Protocol
from SkunkWeb.LogObj import DEBUG
from SkunkWeb.ServiceRegistry import REMOTE
import SocketScience
import cPickle
import sys

class SkunkWebRemoteProtocol(Protocol):

    def marshalRequest(self, socket, sessionDict):
        SocketScience.send_it_all(socket, '\0')
        DEBUG(REMOTE, 'sent sentinel')
        lenDataStr = SocketScience.read_this_many(socket, 10)
        DEBUG(REMOTE, 'read length')
        lenData = int(lenDataStr)
        data = SocketScience.read_this_many(socket, lenData)
        DEBUG(REMOTE, 'read request data: %s' % str(data))
        unpickled=cPickle.loads(data)
        DEBUG(REMOTE, 'unpickled data: %s' % str(unpickled))
        # as a teenager pretends to be, returning to his parents....
        return unpickled

    def marshalResponse(self, response, sessionDict):
        return self._marshalData(cPickle.dumps((0, response)))
    
    def marshalException(self, exc_text, sessionDict):
        excClass, excInstance=sys.exc_info()[:2]
        return self._marshalData(cPickle.dumps((1, excClass,
                                                excInstance,
                                                exc_text)))

    def _marshalData(self, data):
        return "%10d%s" %(len(data), data)


##############################################################
# $Log: protocol.py,v $
# Revision 1.3  2003/05/01 20:45:53  drew_csillag
# Changed license text
#
# Revision 1.2  2001/10/30 15:41:17  drew_csillag
# now returns the rendered and expired flags properly
#
# Revision 1.1.1.1  2001/08/05 15:00:05  drew_csillag
# take 2 of import
#
#
# Revision 1.10  2001/07/09 20:38:40  drew
# added licence comments
#
# Revision 1.9  2001/05/04 18:38:49  smullyan
# architectural overhaul, possibly a reductio ad absurdum of the current
# config overlay technique.
#
# Revision 1.8  2001/04/23 04:55:46  smullyan
# cleaned up some older code to use the requestHandler framework; modified
# all hooks and Protocol methods to take a session dictionary argument;
# added script to find long lines to util.
#
# Revision 1.7  2001/04/19 21:44:56  smullyan
# added some detail to sw.conf.in; added SKUNKWEB_SERVER_VERSION variable to
# SkunkWeb package; more preliminary work on httpd service.
#
# Revision 1.6  2001/04/16 17:52:59  smullyan
# some long lines split; bug in Server.py fixed (reference to deleted
# Configuration module on reload); logging of multiline messages can now
# configurably have or not have a log stamp on every line.
#
# Revision 1.5  2001/04/04 16:28:02  smullyan
# CodeSources.py wasn't calling the installIntoTraceback function; fixed.
# Remote service now handles exceptions better.  Code equivalent to that in
# test.py will need to become part of the templating_experimental service.
#
# Revision 1.4  2001/04/02 22:31:40  smullyan
# bug fixes.
#
# Revision 1.3  2001/04/02 15:06:37  smullyan
# fixed some typos.
#
# Revision 1.2  2001/04/02 00:54:17  smullyan
# modifications to use new requestHandler hook mechanism.
#
# Revision 1.1  2001/03/29 20:17:07  smullyan
# experimental, non-working code for requestHandler and derived services.
#
