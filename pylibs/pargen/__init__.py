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
This module implements a parser generator, 
similar, but not identical to well-known tools such as Yacc or
Bison. 
So unless you are writing a parser for some kind of 
computer language (that isn't HTML or XML), you probably can 
pass this module by.  If you are writing a parser, 
pargen should
be able to help.

The input file to pargen is a file 
of the following format that is somewhat similar:

#comments begin with a #
:methodToCall:  ruleName : rightHandSideItem1 [ rightHandSideItem2 ...]

You then run pargen on this file and produce (hopefully) a parsing
table for your grammar either in marshalled form, or a Python modular form 
(the default).

The Parser module has the rest of the details.
"""

