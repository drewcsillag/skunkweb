# $Id$
# Time-stamp: <01/10/07 14:14:31 smulloni>

########################################################################
#  
#  Copyright (C) 2001 Jacob Smullyan <smulloni@smullyan.org>
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

import exceptions
import os
import shutil
import stat

# constants for "ministat"
MST_SIZE=0
MST_ATIME=1
MST_MTIME=2
MST_CTIME=3

class VFSException(exceptions.Exception): pass

def move(fs, path, newpath, newfs=None):
    if not newfs:
        fs.rename(path, newpath)
    else:
        if not fs.exists(path):
            raise VFSException, "no such file or directory: %s" % path
        if fs.isdir(path):
            _movedir(fs, path, newpath, newfs)
        else:
            _movefile(fs, path, newpath, newfs)

def _movedir(fs, path, newpath, newfs):
    def walker(arg, d, files, path=path, newpath=newpath, fs=fs, newfs=newfs):
        targetDir=os.path.join(newpath, d[len(path):])
        if newfs.exists(targetDir) and not newfs.isdir(targetDir):
            raise VFSException, "file %s already exists" % targetDir
        newfs.mkdir(targetDir)
        for f in files:
            _movefile(fs, os.join(d, file), os.join(targetDir, file), newfs)
    fs.walk(path, walker, 0)            

def _movefile(fs, path, newpath, newfs):
    try:
        f=fs.open(path)
        n=newfs.open(newpath, 'w')
        for l in f.xreadlines():
            n.write(l)
        f.close()
        n.close()
        fs.remove(path)
    except:
        e=sys.exc_info()[0]
        if newfs.exists(newpath):
            try:
                newfs.remove(newpath)
            except: pass
        raise e
                        

class FS:
    """
    abstraction layer (common file model) for file systems, with those features
    needed by SkunkWeb in particular.
    """

    def ministat(self, path):
        raise NotImplementedError

    def mkdir(self, dir):
        raise NotImplementedError

    def mkdirs(self, dir):
        raise NotImplementedError
    
    def remove(self, path):
        raise NotImplementedError

    def open(self, path, mode='r'):
        """
        returns a file object
        """
        raise NotImplementedError
    
    def listdir(self, dir):
        raise NotImplementedError

    def walk(self, dir, visitfunc, arg):
        try:
            names = self.listdir(dir)
        except:
            return
        visitfunc(arg, dir, names)
        for name in names:
            name = os.path.join(dir, name)
            if self.exists(name) and self.isdir(name):
                self.walk(name, func, arg)
            
    def rename(self, path, newpath):
        raise NotImplementedError

    def copy(self, path, newpath):
        raise NotImplementedError
    
    def exists(self, path):
        try:
            self.ministat(path)
            return 1
        except:
            return 0
    
    def isdir(self, path):
        raise NotImplementedError

    def isfile(self, path):
        raise NotImplementedError
    
    def getatime(self,path):
        st=self.ministat(path)
        return st[MST_ATIME]
    
    def getmtime(self, path):
        st=self.ministat(path)
        return st[MST_MTIME]

    def getctime(self, path):
        st=self.ministat(path)
        return st[MST_CTIME]
    
    def getsize(self, path):
        st=self.ministat(path)
        return st[MST_SIZE]

class PathPropertyStore:

    def properties(self, path):
        raise NotImplementedError

    def hasproperty(self, path, property):
        raise NotImplementedError
    
    def getproperty(self, path, property):
        raise NotImplementedError

    def setproperty(self, path, property, value):
        raise NotImplementedError
    

class LocalFS(FS):

    def __init__(self, followSymlinks=0):
        self.followSymlinks=followSymlinks

    def ministat(self, path):
        try:
            if self.followSymlinks:
                return os.stat(path)[6:10]
            else:
                return os.lstat(path)[6:10]
        except os.error, oyVeh:
            raise VFSException, "[Errno %d] %s: %s" % (oyVeh.errno,
                                                       oyVeh.strerror,
                                                       oyVeh.filename)
    def mkdir(self, dir):
        os.mkdir(dir)

    def mkdirs(self, dir):
        os.makedirs(dir)
    
    def remove(self, path):
        if self.isdir(path):
            shutil.rmtree(path)
        else:
            os.remove(path)
    
    def open(self, path, mode='r'):
        """
        returns a file object, corresponding to the builtin function open, not to os.open
        """
        return open(path, mode)
    
    def listdir(self, dir):
        return os.listdir(dir)

    def copy(self, path, newpath):
        # based on shutil.copytree, but always copies symlinks, and doesn't
        # catch exceptions
        if self.isdir(path):
            names = os.listdir(path)
            os.mkdir(newpath)
            for name in names:
                srcname = os.path.join(path, name)
                dstname = os.path.join(newpath, name)
                if os.path.islink(srcname):
                    linkto = os.readlink(srcname)
                    os.symlink(linkto, dstname)
                elif os.path.isdir(srcname):
                    self.copy(srcname, dstname)
                else:
                    shutil.copy2(srcname, dstname)        
        else:
            shutil.copy(path, newpath)

    def rename(self, path, newpath):
        os.rename(path, newpath)
    
    def isdir(self, path):
        return os.path.isdir(path)

    def isfile(self, path):
        return os.path.isfile(path)

########################################################################
# $Log$
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
# Revision 1.1.2.1  2001/09/19 05:24:58  smulloni
# adding vfs
#
########################################################################
