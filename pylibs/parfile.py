# $Id: parfile.py,v 1.1.2.1 2001/09/27 03:36:07 smulloni Exp $
# Time-stamp: <01/09/22 18:04:10 smulloni>

######################################################################## 
#  Copyright (C) 2001 Drew Csillag <drew_csillag@geocities.com>,
#                     Jocob Smullyan <smulloni@smullyan.org>
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

"""
a python archive format, invented by Drew C.
"""

import sys
import stat
import os
import marshal
import time
import errno

def _ftime(t):
    return time.strftime("%b %02d %02H:%02M", time.localtime(t))

def _permdisplay(p):
    x = list('rwxrwxrwx')
    x.reverse()
    
    d = []
    for bn, mask in [(i, 2**i) for i in range(8,-1,-1)]:
        if p & mask:
            d.append(x[bn])
        else:
            d.append('-')
    if stat.S_ISDIR(p):
        d.insert(0, 'd')
    else:
        d.insert(0, '-')
    return ''.join(d)

# a way to avoid unnecessary string appends
class _ParBuffer:
    
    def __init__(self, content=''):
        self.__content=[content]
        self.__length=len(content)
        
    def append(self, item):
        self.__content.append(item)
        self.__length+=len(item)

    def __getslice__(self, i, j):
        # optimize this someday!
        return str(self)[i:j]

    def __len__(self):
        return self.__length
            
    def __str__(self):
        return ''.join(self.__content)

class ParFile:
    def __init__(self, parpath, mode='r'):
        if mode not in "war":
            raise ValueError, "unrecognized mode"
        self.parpath=parpath
        self.mode=mode

        if mode in 'ar':
            f = open(parpath, 'r')
            self.__parDir = marshal.load(f)
            self.__parContents=_ParBuffer(f.read())
        else:
            self.__parDir={}
            self.__parContents=_ParBuffer()

    def names(self):
        return self.__parDir.keys()

    def stat(self, path):
        return self.__parDir[path][1]

    def isdir(self, path):
        return self.__parDir[path][0]==-1

    def printdir(self):
        ks=self.__parDir.keys()
        ks.sort()
        curtime = time.time()

        for k in ks:
            v = self.__parDir[k]
            print '%s %10d  %s  %s' % (_permdisplay(v[1][stat.ST_MODE]),
                                       v[1][stat.ST_SIZE],
                                       _ftime(v[1][stat.ST_MTIME]),k)
    def read(self, name):
        if self.__parDir.has_key(name):
            offset, statinfo=self.__parDir[name]
            endOffset=offset+statinfo[stat.ST_SIZE]
            if endOffset>len(self.__parContents):
                raise RuntimeError, "bad offset"
            return self.__parContents[offset:offset+statinfo[stat.ST_SIZE]]
        raise ValueError, "no such file"

    def write(self, filename, arcname=None):
        if not self.mode in "aw":
            raise ValueError, "unsupported operation for mode"
        stats=os.stat(filename)
        if stat.S_ISDIR(stats[stat.ST_MODE]):
            self.__addDir(filename, stats, arcname)
        else:
            self.__addFile(filename, stats, arcname)
                        
    def __addFile(self, name, statinfo, arcname=None):
        if not arcname:
            arcname=name
        self.__parDir[arcname] = (len(self.__parContents), statinfo)
        text = open(name).read()
        self.__parContents.append(text)

    def __addDir(self, name, statinfo, arcname=None):
        if not arcname:
            arcname=name
        self.__parDir[arcname] = (-1, statinfo)
        files = ['%s/%s' % (name, i) for i in os.listdir(name)]
        for i in files:
            new_stats = os.stat(i)
            if stat.S_ISDIR(new_stats[stat.ST_MODE]):
                self.__addDir(i, new_stats)
            else:
                self.__addFile(i, new_stats)
                
    def writestr(self, name, bytes, stats=None, createDir=0):
        if not stats:
            # generate appropriate statinfo
            stats=[-1] * 10
            # get umask, requires set/restore workaround
            um=os.umask(002)
            os.umask(um)
            # end workaround
            stats[stat.ST_MODE]=(createDir and stat.S_IFDIR or stat.S_IFREG) \
                                 + 0777 & ~um
            stats[stat.ST_SIZE]=(not createDir) and  len(bytes) or 0
            stats[stat.ST_UID]=os.getuid()
            stats[stat.ST_GID]=os.getgid()
            now=time.time()
            stats[stat.ST_ATIME]=now
            stats[stat.ST_CTIME]=now
            stats[stat.ST_MTIME]=now
            stats=tuple(stats)
        self.__parDir[name]=(len(self.__parContents), stats)
        if not createDir:
            self.__parContents.append(bytes)
                 
    def flush(self):
        if self.mode in "aw":
            f=open(self.parpath, 'w')
            marshal.dump(self.__parDir, f)
            f.write(str(self.__parContents))
            f.close()
            
    close=flush

    def extract(self, dir, *filenames):
        if not filenames:
            filenames=self.__parDir.keys()
        filenames.sort()
        for fn in filenames:
            off, st=parDir[fn]
            if off==-1:
                try:
                    os.makedirs(fn)
                except OSError, val:
                    if val.error != errno.EEXIST:
                        raise
            else:
                f=open(fn, 'w')
                f.write(self.__parContents[off:off+statinfo[stat.ST_SIZE]])
                f.close()
            os.chmod(fn, st[stat.ST_MODE])
            os.utime(fn, (st[stat.ST_ATIME], st[stat.ST_MTIME]))


_usagetext="""Usage:
  Extraction
    par x parfile [files_to_extract]
  Listing
    par t parfile
  Creation
    par c parfile files_to_add
"""

def _usage():
    print >> sys.stderr, _usagetext
    sys.exit()
    
if __name__=='__main__':
    if len(sys.argv)<3:
        print >> sys.stderr, "not enough arguments"
        _usage()
    if sys.argv[1] not in 'xct':
        print >> sys.stderr, "invalid option %s" % sys.argv[1]
        _usage()
    if sys.argv[1] == 'c' and len(sys.argv)< 4:
        print >> sys.stderr, "not enough arguments"
        _usage()
    if sys.argv[1] == 'x':
        p=ParFile(sys.argv[2])
        p.extract(os.getcwd(), *sys.argv[3:])
    elif sys.argv[1] == 'c':
        p=ParFile(sys.argv[2], mode='w')
        for fn in sys.argv[3:]:
            p.write(fn)
        p.close()
    elif sys.argv[1] == 't':
        p=ParFile(sys.argv[2])
        p.printdir()
    else:
        # not reachable
        1 / 0
        
    
########################################################################
# $Log: parfile.py,v $
# Revision 1.1.2.1  2001/09/27 03:36:07  smulloni
# new pylibs, work on PyDO, code cleanup.
#
########################################################################
