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
This module defines one function (written in C) named uuid.  It
generates a 36 character globally unique identifier for times when you need
such things.

e.g.

Python 1.5.2 (#1, Jun  8 1999, 13:53:01)  [GCC egcs-2.91.66 19990314/Linux
(egcs- on linux2
Copyright 1991-1995 Stichting Mathematisch Centrum, Amsterdam
>>> import uuid
>>> uuid.uuid()
'426e07e4-1dd2-11b2-81de-c6ef67bdc5a0'
>>>

"""
from _uuid import uuid
