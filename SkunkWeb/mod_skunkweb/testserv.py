#  
#  Copyright (C) 2001 Andrew T. Csillag <drew_csillag@geocities.com>
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
