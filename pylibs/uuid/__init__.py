#  
#  Copyright (C) 2001 Andrew T. Csillag <drew_csillag@geocities.com>
#  
#      You may distribute under the terms of either the GNU General
#      Public License or the SkunkWeb License, as specified in the
#      README file.
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
