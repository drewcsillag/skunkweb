#  
#  Copyright (C) 2001 Andrew T. Csillag <drew_csillag@geocities.com>
#  
#      You may distribute under the terms of either the GNU General
#      Public License or the SkunkWeb License, as specified in the
#      README file.
#   
from CommonStuff import *
from Executables import _SIG_REQUIRED, _SIG_HAS_DEFAULT, _SIG_SPILLOVER, \
     _SIG_META

class CompArgsTag(DTTag):
    def __init__(self):
        DTTag.__init__( self, 'compargs', isempty = 1, modules = [])

    def genMeta ( self, tag, meta ):
        """
        Generate meta-data component argument signature. Creates a dictionary
        where key is one of _SIG_REQUIRED, _SIG_HAS_DEFAULT, or _SIG_SPILLOVER,
        and the value is a tuple containing the variables in each of the 3 types
        """
        args = DTUtil.tagCall(tag, [], 'plainArgs', 'kwArgs')
        kwargs = DTCompilerUtil.pyifyArgs(tag, args['kwArgs'])
        args = DTCompilerUtil.pyifyArgs(tag, args)

        # Check that this is first occurence of the tag
        if meta.has_key ( _SIG_META ):
            raise DT.DTExcept.DTCompileError ( tag,
                  'only one <:compargs:> tag per component is allowed' )

        meta[_SIG_META] = d = {}

        plain, spillover = [], None

        # Munge plainArgs - see if it has a spillover variable
        for v in args['plainArgs']:
            if v[:2] == '**':
                if spillover:
                    raise DT.DTExcept.DTCompileError ( tag,
                          'can specify only 1 spillover (**) variable!' )

                spillover = v[2:]

                if not spillover:
                    raise DT.DTExcept.DTCompileError ( tag,
                          'syntax error: invalid spillover variable' )
            else:
                plain.append(v)

        # Add variables to the dictionary
        d[_SIG_REQUIRED] = plain
        d[_SIG_HAS_DEFAULT] = kwargs.keys()
        d[_SIG_SPILLOVER] = spillover

    def genCode(self, indent, codeout, tagreg, tag):
        args = DTUtil.tagCall(tag, [], 'plainArgs', 'kwArgs')
        kwargs = DTCompilerUtil.pyifyArgs(tag, args['kwArgs'])
        args = DTCompilerUtil.pyifyArgs(tag, args)

        # The only thing we need to do here is assign defaults to variables
        # which were not initiated explicitly. Everything else is already
        # taken care of
        for k, v in kwargs.items():
            codeout.write ( indent, "if not locals().has_key ( '%s' ):" % k )
            codeout.write ( indent+4, "%s = %s" % (k, v) )
