#  
#  Copyright (C) 2001 Andrew T. Csillag <drew_csillag@geocities.com>
#  
#      You may distribute under the terms of either the GNU General
#      Public License or the SkunkWeb License, as specified in the
#      README file.
#   
from socket import *
import marshal
import sys
a=socket(AF_INET, SOCK_STREAM)
a.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
a.bind('', 9997)
a.listen(5)

while 1:
    sock, addr=a.accept()
    length=int(sock.recv(10))
    data=sock.recv(length)

    open('dumpfile','w').write(data)
    d= marshal.loads(data)

    for k,v in d['environ'].items():
        print "%s: %s" % (`k`,`v`)


    if d['environ']['REQUEST_URI'] != '/blah/xxx':
        s="""Content-Type: text/html\r
\r
<B>this is a </B><I>test!</I> arg!!!!\r
<BR>%s""" % d['environ']['REQUEST_URI']
    else:
        s="""Location: http://localhost:8080/\r
Status: 302\r
\r
SHIT!\r
"""
    sock.send("%10d%s" % (len(s), s))
    sock.close()

    print 'stdin is:<', d['stdin'], '>', len(d['stdin'])
