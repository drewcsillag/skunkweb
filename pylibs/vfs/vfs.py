# $Id$
# Time-stamp: <01/12/21 00:20:54 smulloni>

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
import re
import shutil
import stat

import pathutil

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

frontslashRE=re.compile(r'^/')
endslashRE=re.compile(r'/$')

class MultiFS(FS):
    """
    an FS implementation that permits other FS's to be
    mounted within it
    """
    def __init__(self,  mountdict=None):
        """
        mountdict should be a dict of the form:
        { '/desired/mount/point/' : [FSImplementation(), FSImplementation(), ...], ... }
        i.e., the keys are mount points, and the values are lists of fs implementations.
        see MultiFS.mount, below

        strange bug: I had defined the default value for mountdict as {},
        but after creating one instance with mounted directories, creating another instance
        without specifying a value for mountdict caused the *first* print statement below to
        print the value of the previous instance's mounts attribute!  Changing the default value
        to None removed that behavior.
        """
        # print mountdict
        if mountdict!=None:
            self.mounts=mountdict
        else:
            self.mounts={}
        # print self.mounts
        self.__sortMountPoints()
        # print self.mounts

    def __sortMountPoints(self):
        """
        keeps mount points sorted longest first (and otherwise in alphabetical order,
        which doesn't actually matter)
        """
        self.__mountpoints=self.mounts.keys()
        def lencmp(x, y):
            return cmp(len(y), len(x)) or cmp(x, y)
        self.__mountpoints.sort(lencmp)
        
    def mount(self, fs, mountPoint='/'):
        if self.mounts.has_key(mountPoint):
            self.mounts[mountPoint].append(fs)
        else:
            self.mounts[mountPoint]=[fs]
        self.__sortMountPoints()

    def find_mount(self, path, strict=0):
        found=None
        # these are kept sorted longest first
        for p in self.__mountpoints:
            if path.startswith(p):
                found=p
                break
        if not found:
            raise VFSException, "no mount point found for path %s" % path
        # for each fs mounted at that point, try to locate the file; if
        # an exception occurs, try the next, and so on.
        #print "found: %s" % found
        translatedPath=os.path.join('/', path[len(found):])
        #print "translated path: %s" % translatedPath
        ministatinfo=None
        fs=None 
        for tmp in self.mounts[found]:
            try:
                ministatinfo=tmp.ministat(translatedPath)
                fs=tmp
                break
            except:
                continue
        # file not found; fs and ministatinfo should both be None
        if None==ministatinfo and strict:
            raise VFSException, "file or directory not found: %s" % path
        else:
            return found, fs, translatedPath, ministatinfo
    
    def ministat(self, path):
        found, fs, translated, ministat=self.find_mount(path, 1)
        return ministat

    def listdir(self, dir):
        if not dir.endswith('/'):
            dir='%s/' % dir
        found, fs, translated, ministat=self.find_mount(dir, 1)
        listing=fs.listdir(translated)
        #print listing
        mounts=map(lambda x, y=dir: x[len(y):],
                   pathutil.containedPaths(self.__mountpoints, dir))
        #print mounts
        def cleanpath(path):
            path=frontslashRE.sub('', path)
            path=endslashRE.sub('', path)
            return path
        listing.extend(map(cleanpath, mounts))
        listing.sort()
        return listing

    def isdir(self, path):
        if not path.endswith('/'):
            path='%s/' % path
        found, fs, translated, ministat=self.find_mount(path, 1)
        return fs.isdir(translated)

    def isfile(self, path):
        found, fs, translated, ministat=self.find_mount(path, 1)
        return fs.isfile(translated)        

    def remove(self, path):
        found, fs, translated, ministat=self.find_mount(path, 1)
        fs.remove(translated)

    def open(self, path, mode='r'):
        """
        returns a file object.  
        """
        found, fs, translated, ministat=self.find_mount(path, 0)
        # if file was found
        if ministat!=None and fs !=None:
            return fs.open(translated, mode)
        # file was not found
        if mode=='r':
            # file should have existed, raise
            raise VFSException, "file not found: %s" % path
        # append or write mode; find a suitable fs
        for tmp in self.mounts[found]:
            try:
                return tmp.open(path, mode)
            except:
                continue
        raise VFSException, "cannot open file: %s with mode: %s" % (path, mode)


########################################################################
# $Log$
# Revision 1.4  2002/01/02 06:39:24  smulloni
# work on vfs
#
# Revision 1.3  2001/12/18 06:31:50  smulloni
# added preliminary version of vfs.MultiFS.
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
# Revision 1.1.2.1  2001/09/19 05:24:58  smulloni
# adding vfs
#
########################################################################
