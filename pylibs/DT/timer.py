#  
#  Copyright (C) 2001 Andrew T. Csillag <drew_csillag@geocities.com>
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
