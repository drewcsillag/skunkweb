# $Id: importer.py,v 1.3 2002/02/21 07:20:17 smulloni Exp $
# Time-stamp: <02/02/21 10:47:35 smulloni>

######################################################################## 
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
This adds an import hook so that python modules can be imported from
the vfs.  It makes no attempt to load c modules or to check the
timestamps of pyc files.

Originally coded to use imputil.py; problems with that module necessitated
a port to use Gordon McMillan's iu.py, which actually works.
"""

import os
import marshal
import imp
import iu
import re
import types
import vfs

VFS_URL_PREFIX='vfs://'
_prefixlen=len(VFS_URL_PREFIX)

_vfskeyRE=re.compile(r'vfs://<(.*)>(.*)')

class VFSOwner(iu.Owner):
    def __init__(self, vfsUrl):
        m=_vfskeyRE.match(vfsUrl)
        if not m:
            raise ValueError, "not a vfs url: %s" % vfsUrl
        self.fskey=m.group(1)
        path=m.group(2)
        self.fs=vfs.VFSRegistry.get(self.fskey)
        if not self.fs:
            raise vfs.VFSException, "no fs registered by name %s" % self.fskey
        iu.Owner.__init__(self, path)

    def getmod(self,
               nm,
               getsuffixes=imp.get_suffixes,
               loadco=marshal.loads,
               newmod=imp.new_module):
        # this is taken almost verbatim from
        # Gordon McMillan's iu.DirOwner.getmod,
        # except that vfs methods are used
        pth =  os.path.join(self.path, nm)
        possibles = [(pth, 0, None)]
        if self.fs.isdir(pth):
            possibles.insert(0, (os.path.join(pth, '__init__'), 1, pth))
        py = pyc = None
        for pth, ispkg, pkgpth in possibles:
            for ext, mode, typ in getsuffixes():
                attempt = pth+ext
                try:
                    st = self.fs.ministat(attempt)
                except:
                    pass
                else:
                    if typ == imp.C_EXTENSION:
                        fp = self.fs.open(attempt)
                        mod = imp.load_module(nm, fp, attempt, (ext, mode, typ))
                        mod.__file__ = 'vfs://<%s>%s' % (self.fskey, attempt)
                        return mod
                    elif typ == imp.PY_SOURCE:
                        py = (attempt, st)
                    else:
                        pyc = (attempt, st)
            if py or pyc:
                break
        if py is None and pyc is None:
            return None
        while 1:
            if pyc is None or py and pyc[1][vfs.MST_MTIME] < py[1][vfs.MST_MTIME]:
                try:
                    co = compile(self.fs.open(py[0], 'r').read()+'\n', py[0], 'exec')
                    break
                except SyntaxError, e:
                    print "Invalid syntax in %s" % py[0]
                    print e.args
                    raise
            elif pyc:
                stuff = self.fs.open(pyc[0]).read()
                try:
                    co = loadco(stuff[8:])
                    break
                except (ValueError, EOFError):
                    pyc = None
            else:
                return None
        mod = newmod(nm)
        mod.__file__ = co.co_filename
        if ispkg:
            mod.__path__ = [pkgpth]
            subimporter = iu.PathImportDirector(mod.__path__)
            mod.__importsub__ = subimporter.getmod
        mod.__co__ = co
        return mod        



def install():
    import __builtin__
    if type(__builtin__.__import__)==types.BuiltinFunctionType:
        global __oldimport__
        __oldimport__=__builtin__.__import__
        iu._globalownertypes.insert(0, VFSOwner)
        global _manager
        _manager=iu.ImportManager()
        _manager.install()
        
def uninstall():
    import __builtin__
    if type(__builtin__.__import__)==types.MethodType:
        __builtin__.__import__=__oldimport__
        global _manager
        del _manager


def _test():
    # this only works for me, sorry
    vfsurl='vfs://<localtest>/home/smulloni/workdir/pycomposer/'
    import sys
    sys.path.append(vfsurl)
    vfs.VFSRegistry['localtest']=vfs.LocalFS()
    install()
    try:
        import series
        print "success!"
    except:
        print "failed!"

    uninstall()



                    
                    
    
                    
