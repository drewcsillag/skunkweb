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
# $Id: remote_client.py,v 1.1.1.1 2001/08/05 14:59:55 drew_csillag Exp $
# Time-stamp: <01/05/09 14:36:02 smulloni>
########################################################################

import AE.Component
import exceptions
import socket
import SocketScience
import cPickle
import types
from SkunkWeb.LogObj import DEBUG, logException
from SkunkWeb import ServiceRegistry

ServiceRegistry.registerService('remote_client')
REMOTE_CLIENT=ServiceRegistry.REMOTE_CLIENT

SWRC_PROTOCOL="swrc"
DEFAULT_PORT=9887

class RemoteException: pass

def getRemoteException(realException):
    """
    dynamically creates a RemoteException mixin
    with the realException's class, and keeps
    a copy of the realException in the 'remoteInstance'
    field
    """
    remoteClassName=realException.__class__.__name__
    gns=globals()
    lns=locals()
    gns.update({'RemoteException' : RemoteException,
                remoteClassName : realException.__class__})
    classname='Remote%s' % remoteClassName
    if not gns.has_key(classname):
        exec 'global %s\n' \
             'class %s(RemoteException, %s): pass' % \
             (classname, classname, remoteClassName) \
             in gns, lns
    newclass=eval("%s()" % classname, gns, lns)
    newclass.remoteInstance=realException
    newclass.args=realException.args
    return newclass

    
class SkunkWebRemoteComponentHandler(AE.Component.ComponentHandler):

    def callComponent(self,
                      callProtocol,
                      name,
                      argDict,
                      cache,
                      compType,
                      srcModTime):
        """
        client-side handler for remote component calls
        """
        # we don't need the callProtocol argument in this case
        unPickled=None
        host, port, path=self.__parseComponentName(name)
        args = cPickle.dumps((path, argDict, cache,
                              compType, srcModTime))
        msg="%10d%s" %(len(args), args) 
        sock=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((host, port))
        data=sock.recv(1)
        if data=='\0':
            SocketScience.send_it_all(sock, msg)
            length=int(SocketScience.read_this_many(sock, 10))
            data=SocketScience.read_this_many(sock, length)
            unPickled=cPickle.loads(data)
            if (type(unPickled)==types.TupleType
            and len(unPickled)==3
                and type(unPickled[0])==types.ClassType
                and issubclass(unPickled[0], exceptions.Exception)
                and isinstance(unPickled[1], exceptions.Exception)):       
                raise getRemoteException(unPickled[1])
        return unPickled, 1, 1

    def __parseComponentName(self, name):
        """
        I expect a name of the following sort: host[:port]absolutePath,
        where absolutePath begins with a slash, and contains no colons,
        and port is an integer, and host contains neither a colon nor a slash.
        """
        DEBUG(REMOTE_CLIENT, "in __parseComponentName with name %s" % name)
        try:
            slashIndex=name.find('/')
            assert(slashIndex>0)
            path=name[1+slashIndex:]
            DEBUG(REMOTE_CLIENT, "path is %s" % path)
            colonIndex=name.find(':')
            assert(colonIndex<slashIndex)
            if colonIndex>-1:
                assert(colonIndex>0)
                host=name[:colonIndex]
                DEBUG(REMOTE_CLIENT, "host is %s" % host)
                port=int(name[1+colonIndex:slashIndex])
            else:
                host=name[:slashIndex]
                port=DEFAULT_PORT
        except:
            logException()
            raise ValueError, "component name could not be parsed"
        return host, port, path

################################ MAIN ##################################

AE.Component.componentHandlers[SWRC_PROTOCOL]=SkunkWebRemoteComponentHandler()

########################################################################
# $Log: remote_client.py,v $
# Revision 1.1.1.1  2001/08/05 14:59:55  drew_csillag
# take 2 of import
#
#
# Revision 1.7  2001/07/30 16:44:45  smulloni
# fixed remote services to work with changed API of AE.Component.
#
# Revision 1.6  2001/07/09 20:38:40  drew
# added licence comments
#
# Revision 1.5  2001/05/09 18:37:02  smullyan
# changes to RemoteException -- now it is an empty class, and getRemoteException
# dynamically creates a mixin appropriate for the given exception
#
# Revision 1.4  2001/05/04 18:38:47  smullyan
# architectural overhaul, possibly a reductio ad absurdum of the current
# config overlay technique.
#
# Revision 1.3  2001/04/16 17:52:58  smullyan
# some long lines split; bug in Server.py fixed (reference to deleted
# Configuration module on reload); logging of multiline messages can now
# configurably have or not have a log stamp on every line.
#
# Revision 1.2  2001/04/13 04:21:23  smullyan
# removed "file://" protocol for component calls, which made no sense.
#
# Revision 1.1  2001/04/12 22:06:36  smullyan
# adding remote_client service, which adds remote call capability to STML
# component tags.
#
########################################################################
