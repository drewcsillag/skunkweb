# Time-stamp: <03/02/11 00:56:19 smulloni>

######################################################################## 
#  Copyright (C) 2002 Jacob Smullyan <smulloni@smullyan.org>
#  
#      You may distribute under the terms of either the GNU General
#      Public License or the SkunkWeb License, as specified in the
#      README file.
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

def makeVFSUrl(fskey, path):
    return "%s<%s>%s" % (VFS_URL_PREFIX, fskey, path)

def parseVFSUrl(vfsUrl):
    m=_vfskeyRE.match(vfsUrl)
    if not m:
        raise ValueError, "not a vfs url: %s" % vfsUrl
    return m.groups()

class VFSOwner(iu.Owner):
    def __init__(self, vfsUrl):
        self.fskey, self.fspath=parseVFSUrl(vfsUrl)
        self.fs=vfs.VFSRegistry.get(self.fskey)
        if not self.fs:
            raise vfs.VFSException, "no fs registered by name %s" % self.fskey
        iu.Owner.__init__(self, vfsUrl)

    def getmod(self,
               nm,
               getsuffixes=imp.get_suffixes,
               loadco=marshal.loads,
               newmod=imp.new_module):
        #print "nm: %s" % nm
        pth =  os.path.join(self.fspath, nm)
        # this is not, I think, what I am *supposed* to do;
        # but it seems to work.
        pth=pth.replace('.', '/')
        possibles = [(pth, 0, None)]
        if self.fs.isdir(pth):
            possibles.insert(0, (os.path.join(pth, '__init__'), 1, pth))
        #print "possibles: %s" % str(possibles)
        py = pyc = None
        for pth, ispkg, pkgpth in possibles:
            for ext, mode, typ in getsuffixes():
                attempt = pth+ext
                try:
                    st = self.fs.ministat(attempt)
                except:
                    #print "not found: %s" % attempt
                    pass
                else:
                    if typ == imp.C_EXTENSION:
                        # I don't believe this will work; I could, however,
                        # copy the file to /tmp ....
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
            #print "***a package may be involved"
            localpath=iu._os_path_dirname(self.fspath)
            #print "localpath: %s" % localpath
            vfspath="vfs://<%s>%s" % (self.fskey, localpath)
            mod.__path__ = [self.path, pkgpth, iu._os_path_dirname(mod.__file__)]
            subimporter = iu.PathImportDirector(mod.__path__,
                                                {self.path:PkgInVFSImporter(nm, self),
                                                 vfspath:ExtInPkgImporter(vfspath, nm)},
                                                [VFSOwner])
            mod.__importsub__ = subimporter.getmod
        mod.__co__ = co
        #print "returning: %s" % mod
        return mod        

class PkgInVFSImporter:
    def __init__(self, name, owner):
        self.name = name
        self.owner = owner
    def getmod(self, nm):
        #print "PkgInVFSImporter.getmod %s -> %s" % (nm, self.name+'.'+nm)
        return self.owner.getmod(self.name+'.'+nm)
    
class ExtInPkgImporter(VFSOwner):
    def __init__(self, path, prefix):
        VFSOwner.__init__(self, path)
        self.prefix = prefix
    def getmod(self, nm):
        return VFSOwner.getmod(self, self.prefix+'.'+nm)

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



                    
                    
    
                    
