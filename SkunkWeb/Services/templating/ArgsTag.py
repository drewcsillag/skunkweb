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
#$Id: ArgsTag.py,v 1.4 2001/07/09 20:38:40 drew Exp $
"""
args tag - suck stuff from REQUEST.args
"""

import string
import types
import DT.DTExcept
from AE.CommonStuff import *

class ArgsTag(DTTag):
    def __init__(self):
        DTTag.__init__( self, 'args', isempty = 1,
                        modules = [ types ])

    def genCode(self, indent, codeout, tagreg, tag):
        DTCompilerUtil.tagDebug(indent, codeout, tag)
        args = DTUtil.tagCall(tag, [], 'plainArgs', 'kwArgs')
        kwargs = DTCompilerUtil.pyifyArgs(tag, args['kwArgs'])
        args = DTCompilerUtil.pyifyArgs(tag, args)
        
        for i in args['plainArgs']:
            codeout.write(indent, '%s = CONNECTION.args.get("%s")' % (
                i, i))

        for k, v in kwargs.items():
            tval = DTCompilerUtil.getTempName()
            valType = DTCompilerUtil.getTempName()
            codeout.write(indent, '%s = (%s)' % (tval, v))
            codeout.write(indent, '%s = type(%s)' % (valType, tval))
            #if it's a tuple, it's a tuple of func, defaultval
            codeout.write(indent, ('if %s in (__h.types.TupleType, '
                                   '__h.types.ListType):') % valType )
            codeout.write(indent + 4, 'try: %s = %s[0](CONNECTION.args["%s"])' % (
                k, tval, k))
            codeout.write(indent + 4, 'except:')
            codeout.write(indent + 8, 'if len(%s) == 1: %s = None' % (tval, k))
            codeout.write(indent + 8, 'else: %s = %s[1]' % (k, tval))

            #otherwise it's a singleton, is it a function?
            codeout.write(indent, 'elif callable(%s):' % tval)
            codeout.write(indent + 4, 'try: %s = %s(CONNECTION.args["%s"])' % (
                k, tval, k))
            codeout.write(indent + 4, 'except: %s = None' % k)

            #else it's just a default value
            codeout.write(indent, 'else: %s = CONNECTION.args.get("%s", %s)' % (
                k, k, tval))

            codeout.write(indent, 'del %s, %s' % (tval, valType))

