# $Id$
# Time-stamp: <03/02/07 17:16:06 smulloni>

######################################################################## 
#  Copyright (C) 2001-2003 Jacob Smullyan <smulloni@smullyan.org>
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

    def close(self):
        self.__sio.close()
        self.closed=1

    def flush(self):
        raise VFSException, "unsupported operation: flush"

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

    def __iter__(self):
        return self.readlines().__iter__()

########################################################################
# $Log$
# Revision 1.4  2003/02/08 03:23:44  smulloni
# XHTML compliance and Python 2.3a1 compatibility.
#
# Revision 1.3  2002/01/02 06:39:24  smulloni
# work on vfs
#
# Revision 1.2  2001/12/02 20:57:50  smulloni
# First fold of work done in September (!) on dev3_2 branch into trunk:
# vfs and PyDO enhancements (webdav still to come).  Also, small enhancement
# to templating's <:img:> tag.
#
# Revision 1.1.2.1  2001/09/27 03:36:07  smulloni
# new pylibs, work on PyDO, code cleanup.
#
########################################################################
