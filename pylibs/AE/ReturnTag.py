#  
#  Copyright (C) 2001 Andrew T. Csillag <drew_csillag@geocities.com>
#  
#      You may distribute under the terms of either the GNU General
#      Public License or the SkunkWeb License, as specified in the
#      README file.
#   
"""
The <:return:> tag for the data component.

Usage:

<:return <value>:> - returns the value, which is cached if necessary. Raises
an exception if encountered not inside a data component
"""

from CommonStuff import *
import SkunkExcept
from DT import DTExcept

class ReturnTag(DTTag):
    #
    # We depend on a special variable, __h._return, to be present if we are a 
    # data component
    #
    def __init__(self):
        DTTag.__init__ ( self, 'return', isempty=1,
                         modules = [ SkunkExcept, DTExcept ] )

    def genCode(self, indent, codeout, tagreg, tag):
        DTCompilerUtil.tagDebug(indent, codeout, tag)
        args=DTUtil.tagCall(tag, ['value'])
        nargs=DTCompilerUtil.pyifyArgs(tag, args)

        # Make sure this is a data component
        codeout.write ( indent, "if not locals().has_key('__return'):" )
        codeout.write ( indent + 4, "raise __h.SkunkExcept.SkunkStandardError, '<:return:> tag encountered not inside of a data component'" )

        # Ok, set the return value
        codeout.write ( indent, '__return = (%s)' % (nargs['value']) )
        codeout.write ( indent, '__return_set = 1' )

        # We need to exit now
        DTExcept.raiseHalt ( codeout, indent, 'return tag halt' )
