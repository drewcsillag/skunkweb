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
