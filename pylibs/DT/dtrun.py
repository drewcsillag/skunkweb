#  
#  Copyright (C) 2001 Andrew T. Csillag <drew_csillag@geocities.com>
#  
#      You may distribute under the terms of either the GNU General
#      Public License or the SkunkWeb License, as specified in the
#      README file.
#   
import os
import DT
import sys
import time
import marshal
import stat
    

def phfunc(name, obj):
    marshal.dump(obj, open(name,'w'))
    
if __name__=='__main__':
    bt = time.time()
    fname=sys.argv[1]
    mtime=os.stat(fname)[stat.ST_MTIME]
    cform=sys.argv[1]+'.dtcc'
    try:
        cmtime=os.stat(cform)[stat.ST_MTIME]
        comp_form=marshal.load(open(cform))
    except:
        comp_form=None
        cmtime=-1
    d=DT.DT(open(fname).read(), fname, comp_form, mtime, cmtime,
            lambda x, y=cform: phfunc(y, x))
    class dumb: pass
    ns=dumb()
    text = d(ns)
    et = time.time()
    print text
    print 'elapsed time:', et - bt
    
    
