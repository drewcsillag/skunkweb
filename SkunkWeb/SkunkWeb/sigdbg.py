#  
#  Copyright (C) 2001 Andrew T. Csillag <drew_csillag@geocities.com>
#  
#      You may distribute under the terms of either the GNU General
#      Public License or the SkunkWeb License, as specified in the
#      README file.
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
