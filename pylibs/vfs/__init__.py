# $Id$
# Time-stamp: <02/05/25 15:05:54 smulloni>

########################################################################
#  
#  Copyright (C) 2001 Jacob Smullyan <smulloni@smullyan.org>
#  
#      You may distribute under the terms of either the GNU General
#      Public License or the SkunkWeb License, as specified in the
#      README file.
########################################################################

from rosio import RO_StringIO
from vfs import MST_SIZE, MST_ATIME, MST_MTIME, MST_CTIME, \
     VFSException, FS, LocalFS, PathPropertyStore, MultiFS, \
     VFSRegistry, registerFS, FileNotFoundException, NotWriteableException
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
