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
import time
import types
import sys
import string
import re

import DTTagRegistry
import DTTags
import DTCompilerUtil
import DTLexer
import DTParser
import DTExcept
import ErrorHandler
from SkunkExcept import *

def compileTemplate ( text, name, tagreg, meta ):
    try:
        taglist=DTLexer.doTag(text, name)
    except DTExcept.DTLexicalError, val:
        # Ok, force the name here - its a decent hack Drew
        val.name = name
        raise val

    node = DTParser.parseit(text, taglist, tagreg, name)

    indent=0
    codeout=DTCompilerUtil.Output()
    DTCompilerUtil.genCodeNode ( indent, codeout, tagreg, node.children,
                                 meta )
    return codeout.getText()
    
def compileText(text, name):
    # Only catch syntax errors in the text, all else will fall through
    try:
        cobj = compile(text, name, 'exec')
    except SyntaxError, val:
        raise SkunkSyntaxError ( name, text, val )

    return cobj
