# $Id$
# Time-stamp: <02/10/01 17:27:47 smulloni>

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
Bernstein's ftpparse, available at http://c0re.jp/c0de/ftpparse/,
be installed; Fredrik Lundh's similarly named module is not the
same one and won't work.

More information about ftpparse itself is available on Dan
Bernstein's website at http://cr.yp.to/ftpparse.html.
"""


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
import ftplib
import types
if type(list)==types.BuiltinFunctionType:
    # 2.1
    from UserList import UserList as list_
    _isstring=lambda x: isinstance(x, str)
else:
    list_=list
    _isstring=lambda x: type(x) in (types.StringType, types.UnicodeType)
    
class FtpListResult(list_):

    def __init__(self, thing=None):
        self._fname_dict={}
        if thing:
            for t in thing:
                self.append(t)
        
    def append(self, item):
        print item
        res=ftpparse.ftpparse([item])
        print res
        if res:
            list_.append(self, res)
            self._fname_dict[res[ftpparse.NAME]]=res

    def __getitem__(self, key):
        if _isstring(key):
            if self._fname_dict.has_key(key):
                return self._fname_dict[key]
            raise KeyError, key
        return list_.__getitem__(self, key)
    

class FtpFS(vfs.FS):
    writeable=1
    
    def __init__(self, host, username='', password='', acct='', passive=1, port=0):
        self._host=host
        self._port=port
        self._username=username
        self._password=password
        self._acct=acct
        self._passive=passive
        self._conn=ftplib.FTP()
        self._initconn()

    def _initconn(self):
        try:
            self._conn.login(self._username,
                             self._password,
                             self._acct)
        except:
            self._conn.connect(self._host, self._port)
            self._conn.login(self._username,
                             self._password,
                             self._acct)
        self._conn.set_pasv(self._passive)

    def ministat(self, path):
        res=FtpListResult()
        self._conn.dir(path, res.append)

    
        
