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
"Takes some of the rocket science out of socket science."

Normally, calling the recv method on a socket 
object doesn't guarantee that you'll get as many bytes 
as you ask for.  Because of this fact (which is because UNIX 
works this way), this module makes it easy to say, "I want X
number of bytes in N seconds or bust."
"""

import signal 
import socket
import errno

from SkunkExcept import *

# Allow catching of timeout
class SocketTimeoutError ( SkunkRuntimeError ):
    pass

_got_alrm = 0

def _sigalrm_handler ( sig, frame ):
    """Reset the signal handler -- called if the read times out."""

    # XXX for some reason, this doesn't propagate to main thread - don't ask me
    global _got_arlm
    _got_alrm = 1

    signal.signal ( signal.SIGALRM, signal.SIG_DFL )

def read_this_many ( sock, length, timeout = 0 ):
    """
    Promises to read length bytes from sock, or bust
    (we timed out), where bust means 'raise SkunkTimeoutError', or,
    if we just get 0 bytes, we raise SkunkCriticalError instead since this
    usually indicates that the connection is toast.
    """
    global _got_alrm

    dat=''
    if timeout > 0:
        signal.signal ( signal.SIGALRM, _sigalrm_handler )
        signal.alarm ( timeout )

    while len(dat) < length:
        try:
            sock.setblocking(1)
            rd=sock.recv(length - len(dat))
        except socket.error, (err, errstr):
            if timeout > 0 and err == errno.EINTR:
                raise SocketTimeoutError, 'timed out reading from socket'
            
            # re-raise
            raise

        if len(rd) == 0:
            raise SkunkCriticalError, \
                      "socket: got 0 bytes this read, %s total, wanted %s" % \
                      (len(dat), length)

        dat=dat+rd

    # Clear alarm if was set
    if timeout > 0:
        signal.alarm ( 0 )
        signal.signal ( signal.SIGALRM, signal.SIG_DFL )

    return dat

def send_it_all(sock, s):
    """Promises to write all of s to the sock, or bust.  If we for some reason
    write 0 bytes at any time, we raise SkunkRuntimeError because this usually
    indicates that the connection has died."""
    sentlen=0
    len_s=len(s)
    while sentlen < len_s:
        thislen=sock.send(s[sentlen:])
        if thislen == 0:
            raise SkunkRuntimeError, \
                  "wrote 0 bytes this write, %s total, wanted %s" % \
                  (sentlen, len_s)
        sentlen=sentlen+thislen
    return sentlen

