# $Id$
# Time-stamp: <02/02/19 23:42:21 smulloni>

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
#   
########################################################################

import os
import re
import types 
import SkunkWeb.Configuration as Cfg
from SkunkWeb.LogObj import ERROR, logException
from SkunkExcept import SkunkStandardError
import static
import vfs
import manifest
from skunklib import normpath2

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

def product_directory():
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

class Product(static.static):
    
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

    def __getitem__(self, item):
        if self.manifest.has_key(item):
            return self.manifest[item]
        raise KeyError, item

    def static_findProduct(self, productname, fromFile=0):
        pdir=product_directory()
        d=os.path.join(pdir, productname)
        if fromFile or os.path.isdir(d):
            return self(d)
        for ps in product_suffixes:
            path=os.path.join(pdir, '%s%s' % (productname, ps))
            if os.path.exists(path):
                return self(path)

    def static_list(self):
        ptype=type(Cfg.products)
        productList=[]
        if ptype not in (types.ListType, types.TupleType):
            pdirs, pfiles=_directories_and_files(product_directory())
            for p in pdirs:
                newprod=Product.findProduct(p)
                if newprod:
                    productList.append(newprod)
            for p in pfiles:
                newprod=Product.findProduct(p, 1)
                if newprod and newprod not in productList:
                    productList.append(newprod)
        else:
            for p in Cfg.products:
                newprod=Product.findProduct(p)
                if newprod:
                    productList.append(newprod)
                else:
                    raise SkunkStandardError, "no such product: %s" % p
        return productList        

    def load(self, dependencystack=[]):
        if self.name in Product.loaded:
            # already loaded
            return
        if self.name in dependencystack:
            raise ProductDependencyError, "circular dependency: %s" % self.name
        for p in self.dependencies:
            if p not in Product.loaded:
                dprod=Product.findProduct(p)
                if not dprod:
                    raise ProductDependencyError, "product not found: %s" % p
                dependencystack.append(self.name)
                dprod.load(dependencystack)
                dependencystack.remove(self.name)
        self.__reallyload()
        Product.loaded.append(self.name)

    def __reallyload(self):
        docroot_mountpath=Cfg.productPaths.get(self.name)
        lib_mountpath=Cfg.productLibdirs.get(self.name, Cfg.defaultProductLibdir)
        havelocal=self.__fsclass==vfs.LocalFS
        if not docroot_mountpath:
            docroot_mountpath=os.path.join('%s/' % Cfg.documentRoot,
                                           os.path.join(Cfg.defaultProductPath, self.name))
        if havelocal:
            newfs=vfs.LocalFS(os.path.join(self.file, self.docroot))
            libfs=vfs.LocalFS(os.path.join(self.file, self.libs))
        else:
            newfs=self.__fsclass(self.file, root=self.docroot)
            libfs=self.__fsclass(self.file, root=self.libs)
        self.__targetfs.mount(newfs, docroot_mountpath)
        # if the libfs is empty, don't bother mounting it 
        if libfs.listdir('/'):
            self.__targetfs.mount(libfs, lib_mountpath)
            vfs.importer.install()
            sys.path.append(vfs.importer.VFSImporter(libfs, ['/']))
        # this will import services even if they are not contained in the product itself;
        # I'm unclear at this point whether that is good or not
        for service in self.services:
            __import__(service)




    
            
        
        
    
