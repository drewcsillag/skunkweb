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
"""
A bunch of routines to aid the dealing with nonblocking I/O
on sockets.

Reasons for doing non-blocking socket I/O:

* you want to reduce the time it takes for an operation to time out (normal
  TCP timeout is about 2 minutes).
* you want the most control possible over the timing of a network app.
* you want to minimize your exposure to tying up your app, waiting for
  something that might reasonably fail under normal circumstances
"""
import sys
from socket import *
import errno
import select
import fcntl
import random

def readWTimeout(sock, length, timeout):
    """
    Attempt to read length bytes from 
    socket sock within timeout seconds.

    If the desired amount of bytes cannot be read before
    the timeout, returns the bytes that were read up to that
    time (which could be none, an empty string "").
    """
    sock.setblocking(0)
    try:
        readfds=[sock]
        r,w,e=select.select(readfds, [], [], timeout)
        if not r:
            res=None
        else:
            res=sock.recv(length)
    finally:
        sock.setblocking(1)
    return res

def writeWTimeout(sock, data, timeout):
    """
    Attempts to write data to socket
    sock within timeout seconds.

    Returns the amount of bytes written, or if the
    socket could not even be obtained before the timeout,
    None is returned.
    """
    sock.setblocking(0)
    try:
        writefds=[sock]
        r,w,e=select.select([], writefds, [], timeout)
        if not w:
            res=None
        else:
            res=sock.send(data)
    finally:
        sock.setblocking(1)
    return res
        
    
def connectWFailover(timeout, hostportlist):
    """
    Connects to a random host and port in hostportlist,
    and if the connection fails to succeed within timeout
    seconds, the function randomly chooses another host and port
    from the list and repeats the process. As soon as the function 
    succeeds, it returns the resulting socket object.

    If the function runs out of hosts/ports before succeeding,
    it returns None. If it encounters any socket or I/O
    exceptions, it re-raises them.

    hostportlist is a list of tuples of (hostname, port)

    timeout is the number of seconds before we timeout.
    """
    lhp=hostportlist[:]
    while lhp:
        item=random.randint(0,len(lhp)-1)
        host, port=lhp[item]
        sock=None
        try:
            sock=connectWTimeout(host, port, timeout)
        except error, (err, errstr):
            if err != errno.ECONNREFUSED:
                raise 
        del lhp[item]
        if not sock:
            sys.stderr.write('connection to %s:%s failed!!\n' %(host,port))
            continue
        return sock, host, port
    else:
        return None
    
def connectWTimeout(host, port, timeout):
    """
    Connects to host on port, honoring
    a timeout of timeout seconds.

    Returns the socket if it succeeds, None if it times out.
    Any other socket exceptions the function encounters
    are re-raised.
    """
    sock=socket(AF_INET, SOCK_STREAM)
    sock.setblocking(0)
    try:
        sock.connect(host, port)
    except error, (err, errstr):
        if err not in (errno.EWOULDBLOCK, errno.EINPROGRESS):
            sock.close()
            raise
        l=[sock]
        r,w,e=select.select(l,l,l, timeout)
        if not r and not w:
            sock.close()
            return None
    try:
        sock.connect(host, port)
    except error, (err, errstr):
        if err not in (errno.EALREADY, errno.EISCONN):
            sock.close()
            raise
    sock.setblocking(1)
    return sock

if __name__=='__main__':    
    hostportlist=[#('127.0.0.1', 23),
        ('207.25.53.52', 2433),
        ('207.25.53.160', 80),
    #    ('209.67.42.240', 80),
    #    ('209.67.42.241', 80),
    #    ('209.67.42.242', 80),
    #    ('209.67.42.254',80),
        ]

    stuff=connectWFailover(10, hostportlist)
    if stuff is not None:
        sock, host, port=stuff
        print 'connected to %s:%s' %( host,port)
        sock.send('get / http/1.1\r\n\r\n')
        print sock.recv(100)
        sock.close()

class IOTOsocket:
    """
    A non-blocking socket object, which wraps
    a regular Python socket object and implements
    the same interface."""
    def __init__(self, timeout):
        """
	Constructs the IOTO socket that will 
	time out on any of its operations
        in timeout seconds.
	"""
        self.timeout=timeout

    def connect(self, host, port):
	"""
	Just like connect on a regular socket.
	Times out according to timeout attribute.
	Returns 1 on success, None on failure.
	"""
        self.sock=connectWTimeout(host, port, self.timeout)
        if self.sock==None:
            return None
        else:
            return 1

    def send(self, data):
	"""
	Sends data over socket, just as
	though we had used the writeWTimeout
	function.
	"""
        return writeWTimeout(self.sock, data, self.timeout)

    def recv(self, length):
	"""
	Receives up to length bytes over socket, 
	just as though we had used the readWTimeout
	function.
	"""
        return readWTimeout(self.sock, length, self.timeout)
    
