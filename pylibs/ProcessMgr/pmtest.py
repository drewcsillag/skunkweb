#  
#  Copyright (C) 2001 Andrew T. Csillag <drew_csillag@geocities.com>
#  
#      You may distribute under the terms of either the GNU General
#      Public License or the SkunkWeb License, as specified in the
#      README file.
#   
"""
A brief script which tests a ProcessMgr
on the current machine. Only use this script
when debugging bad problems with ProcessMgr.
"""
import time
from ProcessMgr import ProcessMgr
import signal

class Foo(ProcessMgr):
    def run(self):
        #signal.signal(signal.SIGTERM, signal.SIG_IGN)
        while 1:
            time.sleep(1)

    def reload(self):
        self.numProcs = self.numProcs + 1
        ProcessMgr.reload(self)

f = Foo(3, 5, 'pmtest.pid')
f.moduleSnapshot()
f.mainloop()
