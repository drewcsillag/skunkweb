# $Id$
# Time-stamp: <02/02/21 01:32:29 smulloni>

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

from rosio import RO_StringIO
from vfs import MST_SIZE, MST_ATIME, MST_MTIME, MST_CTIME, \
     VFSException, FS, LocalFS, PathPropertyStore, MultiFS, \
     VFSRegistry, registerFS
from zipfs import ZipFS
from shelfProps import ShelfPathPropertyStore
import importer




# and now, try to import stuff with optional dependencies
try:
    from tarfs import TarFS
except ImportError:
    pass
try:
    from zodbProps import ZODBPathPropertyStore
except ImportError:
    pass

# I'd like to do this, but it leads to a circular dependency with AE:

##try:
##    from aeProps import AEPathPropertyStore
##except ImportError:
##    pass
    
# SkunkWeb would die on startup with an AttributeError (AE has no
# attribute "Cache") were I to uncomment the above.
