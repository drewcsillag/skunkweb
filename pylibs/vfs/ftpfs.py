# $Id: ftpfs.py,v 1.4 2002/10/06 03:54:42 smulloni Exp $
# Time-stamp: <02/10/09 16:44:29 smulloni>

########################################################################
#  
#  Copyright (C) 2002 Jacob Smullyan <smulloni@smullyan.org>
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
The ftp vfs requires that Doobee R. Tzeck's python wrapper to Dan
Bernstein's ftpparse, available at http://c0re.jp/c0de/ftpparsemodule/,
be installed; Fredrik Lundh's similarly named module is not the
same one and won't work.

More information about ftpparse itself is available on Dan
Bernstein's website at http://cr.yp.to/ftpparse.html.
"""

import sys
import os
import cStringIO
import ftplib

try:
    import ftpparse
except ImportError:
    import sys
    print >> sys.stderr, __doc__
    print >> sys.stderr, "\n\nThis module will self-destruct in five seconds.\n"
    import time
    time.sleep(5)
    raise

import vfs

_have22=(2, 2)<=sys.version_info[:2]
if not _have22:
    # 2.1
    from UserList import UserList as list_
    _isstring=lambda x: isinstance(x, (str, unicode))
else:
    list_=list
    _isstring=lambda x: type(x) in (types.StringType, types.UnicodeType)

try:
    from skunklib import normpath2 as normpath
except ImportError:
    from os.path import normpath
    
    
class FtpListResult(list_):

    def __init__(self, thing=None):
        self._fname_dict={}
        if thing:
            for t in thing:
                self.append(t)
        
    def append(self, item):
        res=ftpparse.ftpparse([item])[0]
        if res:
            list_.append(self, res)
            self._fname_dict[res[ftpparse.NAME]]=res

    def __getitem__(self, key):
        if _isstring(key):
            if self._fname_dict.has_key(key):
                return self._fname_dict[key]
            raise KeyError, key
        return list_.__getitem__(self, key)

    def keys(self):
        return self._fname_dict.keys()

    def get(self, key, default=None):
        return self._fname_dict.get(key, default)


class FTPFile:
    def __init__(self, ftpconn, name, mode='r'):
        self.mode=mode
        self.name=name
        self.closed=0
        self._conn=ftpconn
        self._buff=cStringIO.StringIO()
        self.__initmode()

    def __readall(self, binary=0):
        sio=cStringIO.StringIO()
        if binary:
            self._conn.retrbinary('RETR %s' % self.name,
                                  sio.write)
        else:
            self._conn.retrlines('RETR %s' %self.name,
                                 lambda x: sio.write("%s\n" % x))
        self._buff.truncate()
        self._buff.write(sio.getvalue())
        self._buff.reset()


    def write(self, bytes):
        if self.closed:
            raise ValueError, "file closed"
        if self.mode not in ('w', 'wb'):
            raise vfs.NotWriteableException, self.name
        self._buff.write(bytes)

    def read(self, size=-99):
        if size and size >-1:
            return self._buff.read(size)
        return self._buff.read()

    def seek(self, offset, whence=0):
        self._buff.seek(offset, whence)

    def tell(self):
        return self._buff.tell()

    def flush(self):
        if self.closed:
            raise ValueError, "file closed"        
        if self.mode=='w':
            self._buff.reset()
            self._conn.storlines('STOR %s' % self.name,
                                 self._buff)
        elif self.mode=='wb':
            self._buff.reset()
            self._conn.storbinary('STOR %s' % self.name,
                                  self._buff)
        else:
            raise vfs.NotWriteableException, self.name

    def close(self):
        if not self.closed:
            self.flush()
            self._buff.truncate()
            self.closed=1

    def __initmode(self):
        if self.mode.startswith('r'):
            self.__readall('b' in self.mode)

if _have22:
    class _robustmeta(type):
        def __new__(self, classname, bases, classdict):
            robustlist=classdict.get('robust')
            robustify=classdict.get('robustify')
            
            if robustlist and robustify:
                for mname in robustlist:
                    m=classdict.get(mname)
                    if m and isinstance(m, types.FunctionType):
                        classdict[m]=robustify(m)
            return type.__new__(self, classname, bases, classdict)

    class FtpConnection(ftplib.FTP, object):
        """
        a wrapper around ftplib.FTP
        that provides error recovery
        in case the connection goes south due to
        timeout
        """
        __metaclass__=_robustmeta

        def connect(self, host='', port=ftplib.FTP_PORT):
            self.host=host
            self.port=port
            ftplib.FTP.connect(self, host, port)
        
        def login(self, user='', passwd='', acct=''):
            self.user=user
            self.passwd=passwd
            self.acct=acct
            ftplib.FTP.login(self, user, passwd, acct)

        def robustify(func):
            def robuster(*args, **kwargs):
                try:
                    func(*args, **kwargs)
                except ftplib.error_temp:
                    self=args[0]
                    try:
                        self.login(self.user,
                                   self.passwd,
                                   self.acct)
                    except (socket.error, IOError):
                        self.connect(self.host, self.port)
                        self.login(self.user,
                                   self.passwd,
                                   self.acct)
                return func(*args, **kwargs)
            return robuster

        robustify=staticmethod(robustify)

        robust=['retrbinary',
                'retrlines',
                'storbinary',
                'storlines',
                'delete',
                'rename',
                'mkd',
                'rmd',
                'dir']
else:
    # I haven't implemented any error-recovery for Python 2.1.
    # Sorry.  Anyone want to do it?
    FtpConnection=ftplib.FTP
        
class FtpFS(vfs.FS):
    writeable=1
    def __init__(self,
                 host,
                 username='',
                 password='',
                 acct='',
                 passive=1,
                 port=ftplib.FTP_PORT):
        self._host=host
        self._port=port
        self._username=username
        self._password=password
        self._acct=acct
        self._passive=passive
        self._conn=FtpConnection()
        self._initconn()

    def _initconn(self):
        self._conn.connect(self._host, self._port)
        self._conn.login(self._username,
                         self._password,
                         self._acct)
        self._conn.set_pasv(self._passive)

    def _get_parsed_record(self, path, all=0):
        path=normpath(path)
        fname=os.path.basename(path)
        res=FtpListResult()
        self._conn.dir(path, res.append)
        if all:
            return res
        record=res.get(os.path.basename(path), res.get(path))
        if not record:
            # in the case of a directory, try again with the parent directory
            parent=os.path.dirname(path)
            res=FtpListResult()
            self._conn.dir(parent, res.append)
            record=res.get(os.path.basename(path), res.get(path))
        return record

    def ministat(self, path):
        # we don't try to get anything for '/'
        if path=='/':
            return [-1]*4
        record=self._get_parsed_record(path)
        if record:
            return [record[ftpparse.SIZE]] +[record[ftpparse.MTIME]]*3            
        raise vfs.FileNotFoundException, path

    def mkdir(self, dirname):
        self._conn.mkd(dirname)

    mkdirs=mkdir

    def isdir(self, path):
        if path=='/':
            return 1
        record=self._get_parsed_record(path)
        if record:
            return record[ftpparse.CWD]
        

    def isfile(self, path):
        if path=='/':
            return 0
        record=self._get_parsed_record(path)
        if record:
            return record[ftpparse.RETR]
        return 0

    def remove(self, path):
        record=self._get_parsed_record(path)
        if not record:
            raise vfs.FileNotFoundException, path
        if record[ftpparse.RETR]:
            self._conn.delete(path)
        elif record[ftpparse.CWD]:
            self._conn.rmd(path)

    def rename(self, path, newpath):
        self._conn.rename(path, newpath)
        
    def listdir(self, path):
        record=self._get_parsed_record(path, 1)
        if record:
            return [x[ftpparse.NAME] for x in record]

    def open(self, path, mode='r'):
        return FTPFile(self._conn, path, mode)

