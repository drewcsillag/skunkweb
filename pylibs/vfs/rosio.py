# $Id$
# Time-stamp: <01/09/21 22:23:33 smulloni>

######################################################################## 
#  Copyright (C) 2001 Jocob Smullyan <smulloni@smullyan.org>
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
########################################################################

from cStringIO import StringIO
from xreadlines import xreadlines
from vfs import VFSException

class RO_StringIO:
    def __init__(self, name, str=''):
        self.__sio=StringIO(str)
        self.closed=0
        self.mode='r'
        self.name=name

    def read(self, n=-1):
        return self.__sio.read(n)

    def readline(self, length=None):
        return self.__sio.readline(length)

    def readlines(self, sizehint=0):
        return self.__sio.readlines(sizehint)

    def xreadlines(self):
        return xreadlines(self.__sio)

    def close(self):
        self.__sio.close()
        self.closed=1

    def flush(self):
        raise VFSException, "unsupported operation: truncate"

    def isatty(self):
        return self.__sio.isatty()

    def seek(self, pos, mode=0):
        self.__sio.seek(pos, mode)

    def tell(self):
        return self.__sio.tell()

    def truncate(self, size=None):
        raise VFSException, "unsupported operation: truncate"

    def write(self, s):
        raise VFSException, "unsupported operation: write"

    def writelines(self, list):
        raise VFSException, "unsupported operation: writelines"

########################################################################
# $Log$
# Revision 1.2  2001/12/02 20:57:50  smulloni
# First fold of work done in September (!) on dev3_2 branch into trunk:
# vfs and PyDO enhancements (webdav still to come).  Also, small enhancement
# to templating's <:img:> tag.
#
# Revision 1.1.2.1  2001/09/27 03:36:07  smulloni
# new pylibs, work on PyDO, code cleanup.
#
########################################################################
