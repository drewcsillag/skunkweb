#  
#  Copyright (C) 2001 Andrew T. Csillag <drew_csillag@geocities.com>
#  
#      You may distribute under the terms of either the GNU General
#      Public License or the SkunkWeb License, as specified in the
#      README file.
#   
"""
The C implementation of some commonly used functions
"""

# Import quote and encode functions
from _urllib import *
from _translate import *
#import header case normalizer
from _normheader import *
#import C version of the posix os.path.normpath
from _normpath import *

def normpath2(path):
    """
    a variant of skunklib's normpath
    that always removes final slashes
    (skunklib.normpath leaves them on).
    Still faster than os.path.normpath
    by a long shot.
    """
    p=normpath(path)
    if len(p)>1 and p[-1]=='/':
        return p[:-1]
    return p


