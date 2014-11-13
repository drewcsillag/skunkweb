#  
#  Copyright (C) 2001 Andrew T. Csillag <drew_csillag@geocities.com>
#  
#      You may distribute under the terms of either the GNU General
#      Public License or the SkunkWeb License, as specified in the
#      README file.
#   
"""
args tag - suck stuff from CONNECTION.args
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

