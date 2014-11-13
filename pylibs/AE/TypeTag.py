#  
#  Copyright (C) 2001 Andrew T. Csillag <drew_csillag@geocities.com>
#  
#      You may distribute under the terms of either the GNU General
#      Public License or the SkunkWeb License, as specified in the
#      README file.
#   
"""
type tag - do run-time type checking
"""
from CommonStuff import *
from DT import DTExcept
import types

class TypeTag(DTTag):
    """The <:type:> tag"""

    def __init__(self):
        DTTag.__init__(self, 'type', isempty = 1, modules = [types])

    def genCode(self, indent, codeout, tagreg, tag):
        DTCompilerUtil.tagDebug(indent, codeout, tag)
        args = DTUtil.tagCall(tag, [], kwcol='kw')
        args = args['kw']
        args = DTCompilerUtil.pyifyArgs(tag, args)

        vargSpec = DTCompilerUtil.getTempName()
        iterator = DTCompilerUtil.getTempName()
        
        codeout.write(indent, '%s = None' % iterator)
        
        if not args.items():
            raise TypeError, 'must specify arguments to <:type:> tag'
        
        for argName, argTypeSpec in args.items():
            codeout.write(indent, '%s = (%s)' % (vargSpec, argTypeSpec))
            codeout.write(indent, 'if type(%s) == __h.types.TupleType:'
                          % vargSpec)
            codeout.write(indent+4, 'for %s in %s:' % (iterator, vargSpec))
            codeout.write(indent+8, 'if isinstance(%s, %s): break' % (
                argName, iterator))
            codeout.write(indent+4, (
                'else: raise TypeError, "the type '
                'of variable %s, value %%s does not match %%s" %% ('
                '%s, %s)' % (argName, argName, vargSpec)))
            codeout.write(indent, 'elif not isinstance(%s, %s):' % (
                argName, vargSpec))
            codeout.write(indent+4, (
                'raise TypeError, "the type of variable %s, value %%s does'
                ' not match %%s" %% (%s, %s)') % (
                    argName, argName, vargSpec))

        codeout.write(indent, 'del %s, %s' % (iterator, vargSpec))

            
                
