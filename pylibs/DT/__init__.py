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
This package is the rendering library for the
STML templating langauge used by the SkunkWeb server.

This is the core of the STML templating library -- 
that is, we don't have all the tags, but we do have the 
basic ones.  (The rest of the tags are implemented in
the SkunkWeb services.) In here is where the STML->python
byte-code compiler and runtime environment is.

You would never really need to use this library directly.
If you find the need, however, contact the skunk.org team
(especially Drew) for pointers. If you just like
to explore, the DT submodule is the place to start.
"""

from DT import *
from DTExcept import DTRuntimeError, DTCompileError, DTLexicalError
