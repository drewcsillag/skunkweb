#  
#  Copyright (C) 2001 Jacob Smullyan <smulloni@smullyan.org>
#  
#      You may distribute under the terms of either the GNU General
#      Public License or the SkunkWeb License, as specified in the
#      README file.
#   
#! /usr/local/bin/python

# a test script for testing remote components

import socket
import cPickle
import SocketScience
import exceptions
import traceback
import AE.Component
import sys
import types

class RemoteException:
    def __init__(self, exceptionClass, exceptionInstance, args):
        if exceptionClass not in self.__class__.__bases__:
            self.__class__.__bases__+=(exceptionClass,)
        exceptionClass.__init__(self, args)
        self.remoteInstance=exceptionInstance
                
def runInteractive():
    import sys
    try:
        argLen=len(sys.argv)
        if argLen>2:
            host=sys.argv[1]
        else:
            host=raw_input("host: ")
        if argLen>=3:
            port=int(sys.argv[2])
        else:
            port=int(raw_input("port: "))
        if argLen>=4:
            path=sys.argv[3]
        else:
            path=raw_input("path: ")
        path=path.strip()
        if argLen>=5:
            argDict=eval(sys.argv[4])
        else:
            argDict=eval(raw_input("argDict: "))
        print "path is \"%s\"" % path
        if path.endswith('.comp') or path.endswith('.pycomp'):
            compType=AE.Component.DT_REGULAR
        else:
            compType=AE.Component.DT_DATA
        if compType==AE.Component.DT_REGULAR:
            print "regular component"
        else:
            print "data component"
        result=run(host, port, path, argDict, compType=compType)
        print
        print '*'*72
        print 
        print "returned from %s:%d%s: %s" % (host, port, path, str(result))
        print 
        print '*'*72
        print
    except:
        print
        print '!'*72
        print 
        traceback.print_exc()
        print
        print '!' * 72
        print

def run(host,
        port,
        path,
        argDict,
        cache=0,
        compType = AE.Component.DT_DATA,
        srcModTime = None):
    
    unPickled=None
    args = cPickle.dumps((path, argDict, cache, compType, srcModTime))
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
            raise RemoteException(unPickled[0], unPickled[1], unPickled[2])
    return unPickled

if __name__=='__main__':
    runInteractive()
    print "Done"


