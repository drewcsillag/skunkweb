# $Id$
# Time-stamp: <01/12/31 13:13:52 smulloni>

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

from vfs import FS, VFSException
from parfile import ParFile
from rosio import RO_StringIO
import pathutil

class ParFS(FS):

    def __init__(self, parpath, prefix='/'):
        self.parpath=parpath
        self.__pfile=ParFile(parpath)
        self.__archive=pathutil.Archive(prefix)
        self.prefix=prefix
        self.__archive.savePaths(self.__pfile.names())

    def ministat(self, path):
        adjusted=pathutil._adjust_user_path(path)
        if not self.__archive.paths.has_key(adjusted):
            raise VFSException, "no such file or directory: %s" % path
        realname=self.__archive.paths[adjusted]
        if realname==None:
            # fictitious directory
            arcstat=os.stat(self.parpath)[7:]
            return (0,) + arcstat
        return self.__pfile.stat(path)[6:]

    def open(self, path, mode="r"):
        adjusted=pathutil._adjust_user_path(path)
        if not self.__archive.paths.has_key(adjusted):
            raise VFSException, "no such file: %s" % path
        if mode<>'r':
            raise VFSException, "unsupported file open mode"
        realname=self.__archive.paths[adjusted]
        if realname!=None:            
            return RO_StringIO(adjusted, self.__pfile.read(realname))
        else:
            raise VFSException, "cannot open directory as file: %s" % path

    def listdir(self, path):
        self.__archive.listdir(path)

    def exists(self, path):
        self.__archive.exists(path)

    def isfile(self, path):
        return not self.__pfile.isdir(path)

    def isdir(self, path):
        return self.__pfile.isdir(path)

########################################################################
# $Log$
# Revision 1.3  2002/01/02 06:39:24  smulloni
# work on vfs
#
# Revision 1.2  2001/12/02 20:57:50  smulloni
# First fold of work done in September (!) on dev3_2 branch into trunk:
# vfs and PyDO enhancements (webdav still to come).  Also, small enhancement
# to templating's <:img:> tag.
#
# Revision 1.1.2.2  2001/10/16 03:27:15  smulloni
# merged HEAD (basically 3.1.1) into dev3_2
#
# Revision 1.1.2.1  2001/09/27 03:36:07  smulloni
# new pylibs, work on PyDO, code cleanup.
#
########################################################################
