# $Id$
# Time-stamp: <03/02/07 17:16:06 smulloni>

######################################################################## 
#  Copyright (C) 2001-2003 Jacob Smullyan <smulloni@smullyan.org>
#  
#      You may distribute under the terms of either the GNU General
#      Public License or the SkunkWeb License, as specified in the
#      README file.
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
# Revision 1.5  2003/05/01 20:46:02  drew_csillag
# Changed license text
#
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
