#  
#  Copyright (C) 2001 Andrew T. Csillag <drew_csillag@geocities.com>
#  
#      You may distribute under the terms of either the GNU General
#      Public License or the SkunkWeb License, as specified in the
#      README file.
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
