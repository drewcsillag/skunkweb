#  
#  Copyright (C) 2001 Andrew T. Csillag <drew_csillag@geocities.com>
#  
#      You may distribute under the terms of either the GNU General
#      Public License or the SkunkWeb License, as specified in the
#      README file.
#   
import time

class Timer:
    def __init__(self):
        self.time=time.time()
        self.lasttime=self.time
        
    def __repr__(self):
        x=time.time()
        d=x-self.time
        dm=int(d/60)
        ds=d % 60

        ld=x-self.lasttime
        lm=int(ld/60)
        ls=ld % 60

        tstr="%02d:%02d.%s diff %02d:%02d.%s" % (dm, ds, str(d-int(d))[2:],
                                                 lm, ls, str(ld-int(ld))[2:])    
        self.lasttime=x
        return tstr
