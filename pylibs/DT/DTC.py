#  
#  Copyright (C) 2001 Andrew T. Csillag <drew_csillag@geocities.com>
#  
#      You may distribute under the terms of either the GNU General
#      Public License or the SkunkWeb License, as specified in the
#      README file.
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
