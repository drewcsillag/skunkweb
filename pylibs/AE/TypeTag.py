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
type tag - do run-time type checking
"""
# $Id: TypeTag.py,v 1.2 2001/07/09 20:38:41 drew Exp $
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
        
        didanything = 0
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

            
                
