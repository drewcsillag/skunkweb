# $Id$
# Time-stamp: <02/02/19 11:42:05 smulloni>

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
from vfs import FS, VFSException, FileNotFoundException, NotWriteableException
from rosio import RO_StringIO
import time
import os
import pathutil

class ZipFS(FS):

    writeable=0
    
    def __init__(self, zippath, root='/', prefix='/'):
        if not zipfile.is_zipfile(zippath):
            raise zipfile.BadZipfile, "not a zip file: %s" % zippath
        self.zpath=os.path.abspath(zippath)
        self.__zfile=zipfile.ZipFile(zippath, mode='r')
        self.__archive=pathutil.Archive(root, prefix)
        self.prefix=prefix
        self.root=root
        self.__archive.savePaths(self.__zfile.namelist())

    def ministat(self, path):
        adjusted=pathutil._adjust_user_path(path)
        if not self.__archive.paths.has_key(adjusted): 
            raise FileNotFoundException, path
        realname=self.__archive.paths[adjusted]
        if realname==None:
            arcstat=os.stat(self.zpath)[7:]
            return (0,) + arcstat
        info=self.__zfile.getinfo(realname)
        modtime=int(time.mktime(info.date_time + (0, 0, 0)))
        return info.file_size, -1, modtime, modtime

    def open(self, path, mode='r'):
        adjusted=pathutil._adjust_user_path(path)
        if mode<>'r':
            raise NotWriteableException, "unsupported file open mode: %s" % mode
        if not self.__archive.paths.has_key(adjusted):
            raise FileNotFoundException, path
        realname=self.__archive.paths[adjusted]
        if realname!=None:
            return RO_StringIO(adjusted,
                               self.__zfile.read(realname))
        else:
            raise VFSException, "cannot open directory as file: %s" % path

    def listdir(self, path):
        return self.__archive.listdir(path)
        
    def exists(self, path):
        return self.__archive.exists(path)

    def isdir(self, path):
        adjusted=pathutil._adjust_user_path(path)
        if not self.__archive.paths.has_key(adjusted):
            raise FileNotFoundException, path
        realname=self.__archive.paths[adjusted]
        if realname==None:
            return 1
        else:
            # on UNIX, I'd hope to get this from file attributes;
            # Per Boethner's implementation of java.util.zip.ZipEntry
            # for GNU Classpath only tests the final slash
            return realname.endswith('/') and \
                   self.__zfile.getinfo(realname).file_size==0

    def isfile(self, path):
        adjusted=pathutil._adjust_user_path(path)
        if not self.__archive.paths.has_key(adjusted):
            raise FileNotFoundException, path
        realname=self.__archive.paths[adjusted]
        if realname==None:
            return 0
        else:
            return not adjusted.endswith('/')


########################################################################
# $Log$
# Revision 1.5  2002/02/19 17:17:49  smulloni
# vfs improvements; documentation typo fix.
#
# Revision 1.4  2002/01/10 02:34:18  smulloni
# vfs tweaks
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

    

    

    


            
        
