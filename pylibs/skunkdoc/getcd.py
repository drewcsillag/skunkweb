#  
#  Copyright (C) 2001 Andrew T. Csillag <drew_csillag@geocities.com>
#  
#      You may distribute under the terms of either the GNU General
#      Public License or the SkunkWeb License, as specified in the
#      README file.
#   
#!/usr/local/bin/python

import sys, os

def getcd():
    cwd = os.getcwd()

    if os.path.islink(sys.argv[0]):
        bn = os.path.basename(sys.argv[0])
        sc = os.readlink(bn)
    else:
        sc = sys.argv[0]

    os.chdir(os.path.dirname(sc) or '.')

    inst = os.getcwd()
    os.chdir(cwd)
    return inst
