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
The signal_plus.signal_plus module contains two functions:

blockTERM - blocks SIGTERM from hitting this process
unblockTERM - unblocks SIGTERM and if SIGTERM
was sent to this process while it was blocked, it should hit us now.

This is currently used by SkunkWeb to attempt to allow in-flight requests to
finish up in a server restart situation, since when the parent process gets
the restart signal (SIGHUP), it subsequently sends SIGTERM to all of it's
kids, which, if handled, would cause in-flight requests to get screwed up.
By using this module, we can put off the SIGTERM until we're done with the
current request.

If you are using the ProcessMgr, this module may be something to
think about.
"""
