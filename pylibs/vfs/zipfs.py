# $Id$
# Time-stamp: <01/09/22 18:16:10 smulloni>

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

import zipfile
from vfs import FS, VFSException
from rosio import RO_StringIO
import time

class ZipFS(FS):
    
    def __init__(self, zippath, mode='r'):
        if not zipfile.is_zipfile(zippath):
            raise zipfile.BadZipfile, "not a zip file: %s" % zippath
        self.zpath=zippath
        self.__zfile=zipfile.ZipFile(zippath, mode=mode)

    def ministat(self, path):
        info=self.__zfile.getinfo(path)
        modtime=time.asctime(info.date_time + (0, 0, 0))
        return info.file_size, -1, modtime, modtime

    def open(self, path, mode='r'):
        if mode<>'r':
            raise VFSException, "unsupported file open mode"
        return RO_StringIO(path, self.__zfile.read(path))

    def listdir(self, dir):
        names=self.__zfile.namelist()
        if not dir.endswith('/'):
            dir+='/'
        if dir not in names:
            raise VFSException, "directory %s not found" % dir        
        return filter(lambda x, y=dir: x.startswith(y) \
                      and y!=x \
                      and '/' not in x[len(y):-1],
                      names)
        
    def exists(self, path):
        return path in self.__zfile.namelist()

    def isdir(self, path):
        # this won't handle archives created on Windows ;=>(
        return self.exists(path) and \
               path.endswith('/') and \
               self.__zfile.getinfo(path).filesize==0

    def isfile(self, path):
        return self.exists(path) and \
               not path.endswith('/')


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

    

    

    


            
        
