#  
#  Copyright (C) 2001 Andrew T. Csillag <drew_csillag@geocities.com>
#  
#      You may distribute under the terms of either the GNU General
#      Public License or the SkunkWeb License, as specified in the
#      README file.
#   
import SocketMan
import sys
sys.stderr = sys.__stderr__
def handleconn(sock, addr):
    sock.send("foo! %s\n" % (sock.getsockname(),))
    raise "SHIT"
    
sm = SocketMan.SocketMan(numProcs=3, pidFile='pid')
#sm.addConnection(("UNIX", "foo", 0555), handleconn)
sm.addConnection(("TCP", "", 9991), handleconn)
sm.moduleSnapshot()
print "got here!", sm.mainloop
sm.mainloop()
