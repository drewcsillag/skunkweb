# $Id: __init__.py,v 1.1 2002/02/20 04:54:14 smulloni Exp $
# Time-stamp: <02/02/20 11:15:24 smulloni>

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

"""
a service to support SkunkWeb products, which can be installed as
archive files (zip, tar, or tgz), or as directories in the SkunkWeb
product directory.  This service requires that the documentRootFS be a
MultiFS (at least prior to scoping); the assumption is that MultiFS
will become the default fs.

The product loader is configured to load by default all product
archives in the product directory, but can be configured to load any
arbitrary subset.

The loader opens the MANIFEST file in each archive, looks for
dependencies stated therein, and loads any products therein listed,
raising an error for circular or missing dependencies.  For each load,
it adds mount points to the MultiFS for the docroot and the python
libs, if any.  Services specified in the MANIFEST are then imported.

The MANIFEST is essentially an init file for the product which
integrates it into the SkunkWeb framework.  If it isn't present, the
docroot and libs will be mounted at <docroot>/products/<product-name>
and /products/lib/<product-name>, respectively; the latter will be
added to the path of the VFSImporter (which itself will be installed
if not present).

This service will also contain a utility for creating products, creating
the MANIFEST file, byte-compiling the python modules, and creating the
archive file.
"""

import SkunkWeb.Configuration as Cfg
from loader import *
from manifest import *
import os

Cfg.mergeDefaults(productDirectory='products',
                  products='*',
                  defaultProductPath='products',
                  productPaths={},
                  defaultProductLibdir='products',
                  productLibdirs={}
                  )

proddir=loader.product_directory()
if not os.path.isdir(proddir):
    try:
        os.makedirs(proddir)
    except:
        ERROR(("product service needs a product directory,"
               "currently configured as %s") % proddir)
        raise
del proddir

for p in loader.listProducts():
    p.load()


