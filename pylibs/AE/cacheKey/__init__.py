#  
#  Copyright (C) 2001 Andrew T. Csillag <drew_csillag@geocities.com>
#  
#      You may distribute under the terms of either the GNU General
#      Public License or the SkunkWeb License, as specified in the
#      README file.
#   
#
# Just get everything from the .so module
#
from cachekey import *

# Import md5, since it is used by the C module, to avoid it being cleared
# if UserModuleCleanup is on
import md5
