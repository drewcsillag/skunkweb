# $Id$
# Time-stamp: <02/02/21 13:38:32 smulloni>

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
try:
    # optimized version
    from skunklib import normpath
except ImportError:
    # for losers
    normpath=os.path.normpath

# constants for "ministat"
MST_SIZE=0
MST_ATIME=1
MST_MTIME=2
MST_CTIME=3

VFSRegistry={}

_keyRE=re.compile(r'.*(\d+)$')

def registerFS(fs, key='default'):
    for k, f in VFSRegistry.items():
        if fs is f:
            return k
    while key in VFSRegistry.keys():
        m=_keyRE.search(key)
        if not m:
            d=1
        else:
            # I dare you to overflow this int
            d=int(m.group(1))+1
        key='%s%d' % (key, d)
    VFSRegistry[key]=fs
    return key

class VFSException(exceptions.Exception): pass
class FileNotFoundException(VFSException): pass
class NotWriteableException(VFSException): pass

def move(fs, path, newpath, newfs=None):
    if not newfs:
        fs.rename(path, newpath)
    else:
        if not fs.exists(path):
            raise FileNotFoundException, path
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
    def isWriteable(self):
        """
        returns whether the fs supports write operations;
        says nothing about whether a write is permitted
        for a particular path
        """
        
        if hasattr(self.__class__, 'writeable'):
            return self.__class__.writeable
        else:
            return None

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

class ACQ_RAISE: pass

class PathPropertyStore:
    """
    an interface for storing properties
    associated with paths
    """
    
    def properties(self, path):
        """
        returns dictionary of properties
        for the path
        """
        raise NotImplementedError

    def hasproperty(self, path, property):
        """
        returns whether the path has the given property
        """
        raise NotImplementedError
    
    def getproperty(self, path, property):
        """
        returns the given property
        for the path
        """
        raise NotImplementedError

    def setproperty(self, path, property, value):
        """
        associates given property with given value
        for the given path
        """
        raise NotImplementedError

    def delproperty(self, path, property):
        """
        removes a property from the store
        if it exists for the path; otherwise,
        does nothing
        """
        raise NotImplementedError

    def acquireWithAncestor(self,
                            path,
                            property,
                            default=ACQ_RAISE,
                            root='/'):
        """
        looks for specified property up the directory tree starting at
        path and ending at root.  If the property is found, return a
        tuple consisting ofthe path where it was found and the value
        of the property; otherwise, if the value of default is
        ACQ_RAISE, raise a KeyError, and if not,return
        (None, default)
        """
        if not path.startswith(root):
            raise ValueError, "root must be a subpath of path: path: %s, root: %s" % (path, root)
        if self.hasproperty(path, property):
            return (path, self.getproperty(path, property))
        else:
            if path==root:
                if default is ACQ_RAISE:
                    raise KeyError, "property not found: %s" % property
                return (None, default)
            path=os.path.dirname(os.path.normpath(path))
            return self.acquireWithAncestor(path,
                                            property,
                                            default,
                                            root)
    def acquire(self,
                path,
                property,
                default=ACQ_RAISE,
                root='/'):
        """
        like acquireWithAncestor, but doesn't
        return the path where the property was found
        """
        return self.acquireWithAncestor(path,
                                        property,
                                        default,
                                        root)[1]

    
class LocalFS(FS):

    writeable=1

    def __init__(self, root='/', followSymlinks=0):
        self.root=root
        self.followSymlinks=followSymlinks

    def _resolvepath(self, path):
        return normpath('%s/%s' % (self.root, path))

    def ministat(self, path):
        realpath=self._resolvepath(path)
        try:
            if self.followSymlinks:
                return os.stat(realpath)[6:10]
            else:
                return os.lstat(realpath)[6:10]
        except os.error, oyVeh:
            if oyVeh.errno==2:
                raise FileNotFoundException, path
            raise VFSException, "[Errno %d] %s: %s" % (oyVeh.errno,
                                                       oyVeh.strerror,
                                                       oyVeh.filename)
    def mkdir(self, dir):
        os.mkdir(self._resolvepath(dir))

    def mkdirs(self, dir):
        os.makedirs(self._resolvepath(dir))
    
    def remove(self, path):
        realpath=self._resolvepath(path)
        if self.isdir(realpath):
            shutil.rmtree(realpath)
        else:
            os.remove(realpath)
    
    def open(self, path, mode='r'):
        """
        returns a file object, corresponding to the builtin function open, not to os.open
        """
        return open(self._resolvepath(path), mode)
    
    def listdir(self, dir):
        return os.listdir(self._resolvepath(dir))

    def copy(self, path, newpath):
        # based on shutil.copytree, but always copies symlinks, and doesn't
        # catch exceptions
        realpath=self._resolvepath(path)
        realnew=self._resolvepath(newpath)
        if self.isdir(realpath):
            names = os.listdir(realpath)
            os.mkdir(realnew)
            for name in names:
                srcname = os.path.join(realpath, name)
                dstname = os.path.join(realnew, name)
                if os.path.islink(srcname):
                    linkto = os.readlink(srcname)
                    os.symlink(linkto, dstname)
                elif os.path.isdir(srcname):
                    self.copy(srcname, dstname)
                else:
                    shutil.copy2(srcname, dstname)        
        else:
            shutil.copy(realpath, realnew)

    def rename(self, path, newpath):
        os.rename(self._resolvepath(path), self._resolvepath(newpath))
    
    def isdir(self, path):
        return os.path.isdir(self._resolvepath(path))

    def isfile(self, path):
        return os.path.isfile(self._resolvepath(path))

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
        # print "found: %s" % found
        translatedPath=os.path.join('/', path[len(found):])
        # print "translated path: %s" % translatedPath
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
            raise FileNotFoundException, path
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
            raise FileNotFoundException, path
        # append or write mode; find a suitable fs
        for tmp in self.mounts[found]:
            try:
                return tmp.open(path, mode)
            except:
                continue
        raise NotWriteableException, "cannot open file: %s with mode: %s" % (path, mode)


########################################################################
# $Log$
# Revision 1.10  2002/02/21 18:47:16  smulloni
# bug fix: had forgotten to compile a regex.
#
# Revision 1.9  2002/02/21 07:20:17  smulloni
# numerous changes for product service and vfs, to support importing from the
# latter.
#
# Revision 1.8  2002/02/19 17:17:49  smulloni
# vfs improvements; documentation typo fix.
#
# Revision 1.7  2002/02/06 07:04:20  smulloni
# added PathPropertyStore.acquireWithAncestor().
#
# Revision 1.6  2002/02/05 03:18:17  smulloni
# fixed ShelfPathPropertyStore, added a ZODB-based implementation, and added two methods to PathPropertyStore itself, one of them not virtual.
#
# Revision 1.5  2002/01/27 03:10:44  smulloni
# moving in the direction of getting rid of Configuration.DocumentRoot!
#
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
