# Time-stamp: <03/08/11 13:12:06 smulloni>

######################################################################## 
#  Copyright (C) 2002 Andrew Csillag <drew_csillag@yahoo.com>
#  
#      You may distribute under the terms of either the GNU General
#      Public License or the SkunkWeb License, as specified in the
#      README file.
########################################################################

import tarlib
from vfs import FS, VFSException
from rosio import RO_StringIO
import pathutil
import os


def bslog(msg):
#    try:
#        open('/tmp/bullshit','a').write('%s\n' % msg)
#    except:
        pass
    
class TarFS(FS):
    def __init__(self, path, root='', prefix='/'):
        self.path=os.path.abspath(path)
        self._contents={} #filled by _readTar
        self._filelist=[] #filled by _readTar
        self._readTar()
        self.__archive=pathutil.Archive(root, prefix)
	self.root=root
        self.prefix=prefix
        self.__archive.savePaths(self._filelist)
        bslog(str(self._filelist))
        
    def ministat(self, path):
        bslog('ministat %s' % path)
        adjusted=pathutil._adjust_user_path(path)
        if not self.__archive.paths.has_key(adjusted): 
            raise VFSException, "no such file or directory: %s" % path
        realname=self.__archive.paths[adjusted]
        if realname==None:
            arcstat=os.stat(self.zpath)[7:]
            return (0,) + arcstat
        item = self._contents[realname]
        return item[1], -1, item[2], item[2]
    
    def _readTar(self):
        if self.path[-2:] == 'gz':
            import gzip
            tarlib.readTar(gzip.GzipFile(self.path), self._readTarEater)
        else:
            tarlib.readTar(open(self.path), self._readTarEater)

    def _readTarEater(self, name, contents, size, mode, uid, gid, mtime, 
                      typeflag, linkname, uname, gname, devmaj, devmin):
        self._contents[name] = (contents, size, mtime)
        self._filelist.append(name)

    def open(self, path, mode='r'):
        bslog('getting %s' % path)
        adjusted=pathutil._adjust_user_path(path)
        if mode!='r':
            raise VFSException, "unsupported file open mode"
        if not self.__archive.paths.has_key(adjusted):
            raise VFSException, "no such file or directory: %s" % path
        realname=self.__archive.paths[adjusted]
        if realname!=None:
            return RO_StringIO(adjusted,
                               self._contents[realname][0])
        else:
            raise VFSException, "cannot open directory as file: %s" % path

    def listdir(self, path):
        bslog('listdir %s' % path)
        return self.__archive.listdir(path)
        
    def isdir(self, path):
        bslog('isdir %s' % path)
        adjusted=pathutil._adjust_user_path(path)
        if not self.__archive.paths.has_key(adjusted):
            #raise VFSException, "no such file or directory: %s" % path
	    return 0
        realname=self.__archive.paths[adjusted]
        if realname==None:
            return 1
        else:
            return realname.endswith('/') and \
                   self._contents[realname][1]==0

    def isfile(self, path):
        bslog('isfile %s' % path)
        adjusted=pathutil._adjust_user_path(path)
        if not self.__archive.paths.has_key(adjusted):
            #raise VFSException, "no such file or directory: %s" % path
	    return 0
        realname=self.__archive.paths[adjusted]
        if realname==None:
            return 0
        else:
            return not adjusted.endswith('/')
