#  
#  Copyright (C) 2001 Andrew T. Csillag <drew_csillag@geocities.com>
#  
#      You may distribute under the terms of either the GNU General
#      Public License or the SkunkWeb License, as specified in the
#      README file.
#   
import os
import signal
import signal_plus
import time

signal_plus.blockTERM()
print "killing self with term"
os.kill(os.getpid(), signal.SIGTERM)
print "sleeping"
time.sleep(4)
print "done sleeping, unblocking term"
signal_plus.unblockTERM()
print "sleeping again"
time.sleep(4)
