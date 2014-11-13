# Time-stamp: <03/02/08 19:16:23 smulloni>

########################################################################
#  
#  Copyright (C) 2002 Jacob Smullyan <smulloni@smullyan.org>
#  
#      You may distribute under the terms of either the GNU General
#      Public License or the SkunkWeb License, as specified in the
#      README file.
#   
########################################################################

import os
import re
import sys
import types 
import SkunkWeb.Configuration as Cfg
from SkunkWeb.LogObj import ERROR, logException
from SkunkExcept import SkunkStandardError
import vfs
import manifest
from skunklib import normpath2
from strnatcmp import strnatcmp

__all__=['product_suffixes',
         'product_directory',
         'ProductDependencyError',
         'Product',
         ]

product_suffixes=('.zip', '.tar', '.tar.gz', '.tgz')
_pRE=re.compile(r'(.*)(\.zip|\.tar|\.tar.gz|\.tgz)$')
DIRECTORY_FORMAT='directory'

_fsmap={'.zip'           : vfs.ZipFS,
        '.tar'           : vfs.TarFS,
        '.tar.gz'        : vfs.TarFS,
        '.tgz'           : vfs.TarFS,
        DIRECTORY_FORMAT : vfs.LocalFS }

def get_product_path(name):
    """
    Returns the URL path of the product of the given name.
    """
    path=Cfg.productPaths.get(name)
    if not path:
        path=os.path.join(Cfg.defaultProductPath, name)
    return path

def product_directory():
    """
    Returns the location of the directory where products are installed.
    """
    # if Cfg.productDirectory is a relative path,
    # it is taken as relative to Cfg.SkunkRoot
    return os.path.join(Cfg.SkunkRoot,
                        Cfg.productDirectory)

def _directories_and_files(directory):
    """
    return a tuple of two lists, the directories
    and files contained in the directory argument.
    """
    allfiles=[os.path.join(directory, f) for f in os.listdir(directory)]
    df=([], [])
    for p in allfiles:
        df[os.path.isdir(p)].append(p)
    return df[1], df[0]

class ProductDependencyError(Exception): pass

class ProductMountPoint:
    def __init__(self, mount):
        self.mount=mount

    def __str__(self):
        return os.path.join(Cfg.documentRoot, self.mount)

class Product:
    
    loaded=[]
    
    def __init__(self, product_file, targetfs=Cfg.documentRootFS):
        isdir=os.path.isdir(product_file)
        if not isdir:
            m=_pRE.match(product_file)
            if not m:
                raise ValueError, "not a product file: %s" % product_file
            self.format=m.group(2)
            self.name=os.path.basename(m.group(1))
        else:
            self.format=DIRECTORY_FORMAT
            self.name=os.path.basename(product_file)
        self.file=product_file
        
        self.__fsclass=_fsmap[self.format]
        self.__targetfs=targetfs
        self.__fsname=vfs.registerFS(targetfs, 'documentRootFS')
        self.__readManifest()

    def __readManifest(self):
        try:
            data=self.__fsclass(self.file).open(os.path.join('/', manifest.MANIFEST_FILE)).read()
        except vfs.VFSException:
            ERROR("error in reading product manifest: %s" % self.file)
            logException()
            raise
        self.manifest=manifest.read_manifest(data)

    def __getattr__(self, attr):
        if self.manifest.has_key(attr):
            return self.manifest[attr]
        raise AttributeError, attr

    def load(self, dependencystack=[]):
        if self.name in Product.loaded:
            # already loaded
            return
        if self.name in dependencystack:
            raise ProductDependencyError, "circular dependency: %s" % self.name
        for p in self.dependencies:
            if type(p)==types.TupleType:
                pr, vr=p
            else:
                pr=p; vr=None
            if pr not in Product.loaded:
                dprod=findProduct(p)
                if not dprod:
                    raise ProductDependencyError, "product not found: %s" % p
                if vr!=None and strnatcmp(dprod.version, vr)==-1:
                    raise ProductDependencyError, ("need at least version %s of product %s, "
                                                   "found version %s") % (vr,
                                                                          pr,
                                                                          dprod.version)
                dependencystack.append(self.name)
                dprod.load(dependencystack)
                dependencystack.remove(self.name)
        self.__reallyload()
        Product.loaded.append(self.name)

    def __reallyload(self):
        havelocal=self.__fsclass==vfs.LocalFS
        docmount=get_product_path(self.name)
        if havelocal:
            newfs=vfs.LocalFS(os.path.join('%s/' % self.file, self.docroot))
            libdir=normpath2('%s/%s' % (self.file, self.libs))
            if os.path.exists(libdir) and libdir not in sys.path:
                sys.path.append(libdir)
        # if using Python 2.3 or better, using zipimport
        elif self.format=='.zip' and sys.version_info >=(2,3):
            libdir='%s/%s' % (self.file, self.libs)
            sys.path.append(libdir)
            newfs=self.__fsclass(self.file, root=self.docroot)
        else:
            newfs=self.__fsclass(self.file, root=self.docroot)
            libfs=self.__fsclass(self.file, root=self.libs)
            # if the libfs is empty, don't bother installing it
            if libfs.listdir('/'):
                k=vfs.registerFS(libfs, self.name)
                vfs.importer.install()
                sys.path.append('vfs://<%s>/' % k)
        self.__targetfs.mount(newfs, ProductMountPoint(docmount))


        # this will import services even if they are not contained in
        # the product itself; I'm unclear at this point whether that is
        # good or not
        for service in self.services:
            __import__(service)
        

def findProduct(productname, fromFile=0):
    pdir=product_directory()
    d=os.path.join(pdir, productname)
    if fromFile or os.path.isdir(d):
        return Product(d)
    for ps in product_suffixes:
        path=os.path.join(pdir, '%s%s' % (productname, ps))
        if os.path.exists(path):
            return Product(path)

def listProducts():
    ptype=type(Cfg.products)
    productList=[]
    if ptype not in (types.ListType, types.TupleType):
        pdirs, pfiles=_directories_and_files(product_directory())
        for p in pdirs:
            newprod=findProduct(p)
            if newprod:
                productList.append(newprod)
        for p in pfiles:
            newprod=findProduct(p, 1)
            if newprod and newprod not in productList:
                productList.append(newprod)
            else:
                for p in Cfg.products:
                    newprod=findProduct(p)
                    if newprod:
                        productList.append(newprod)
                    else:
                        raise SkunkStandardError, "no such product: %s" % p
    return productList        

    
            
        
        
    
