#  
#  Copyright (C) 2001 Andrew T. Csillag <drew_csillag@geocities.com>
#  
#      You may distribute under the terms of either the GNU General
#      Public License or the SkunkWeb License, as specified in the
#      README file.
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

