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
import os
import time
import signal



def handler(*args):
    print args
    for i in dir(signal):
        if i[:3] == 'SIG' and i[3] != '_':
            if getattr(signal, i) == args[0]:
                print i

print 'pid =', os.getpid()
for i in dir(signal):
    if i[:3] == 'SIG' and i[3] != '_':
        #print i
        signal.signal(getattr(signal, i), handler)

while 1:
    time.sleep(20)
