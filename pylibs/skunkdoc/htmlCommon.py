#  
#  Copyright (C) 2001 Andrew T. Csillag <drew_csillag@geocities.com>
#  
#      You may distribute under the terms of either the GNU General
#      Public License or the SkunkWeb License, as specified in the
#      README file.
#   
MAX_TOC_ENTRIES_BEFORE_SEPARATE = 30

def writer(fileobj):
    return lambda x, o=fileobj.write: o(x+'\n')
