#  
#  Copyright (C) 2001 Andrew T. Csillag <drew_csillag@geocities.com>
#  
#      You may distribute under the terms of either the GNU General
#      Public License or the SkunkWeb License, as specified in the
#      README file.
#   
"""
This module implements the component family of tags
"""

import Component
from CommonStuff import *
from DT import DT_REGULAR, DT_INCLUDE, DT_DATA

class ComponentTag(DTTag):
    """
    The component tag is used to render non-cacheable components which 
    inherit the namespace of their parent
    """
    def __init__(self):
        DTTag.__init__ ( self, 'component', isempty = 1, 
                         modules = [Component] )

    def genCode(self, indent, codeout, tagreg, tag):
        DTCompilerUtil.tagDebug(indent, codeout, tag)
        #args=DTUtil.tagCall(tag, ['name', ('cache', 'no'),
        #                          ('defer', -1), ('__args__', None)],
        #                    kwcol='kw')
        args=DTUtil.tagCall(tag, ['name', ('cache', 'no'),
                                  ('__args__', None)],
                            kwcol='kw')
        kw = DTCompilerUtil.pyifyKWArgs(tag, args['kw'])
        args = DTCompilerUtil.pyifyArgs(tag, args)

        # Create the temp variables
        text = DTCompilerUtil.getTempName()

        if args['__args__']:
            argsarg = DTCompilerUtil.getTempName()
            codeout.write(indent, '%s = %s' % (argsarg, args['__args__']))
            codeout.write(indent, 'if type(%s) != __h.types.DictType:' % argsarg)
            codeout.write(indent+4, 'raise TypeError, "__args__ argument must'
                          ' be a dictionary"')
            codeout.write(indent, '%s.update(%s)' % (argsarg, kw))
            # Render the component
            #codeout.write ( indent, '%s = __h.Component.callComponent ( '
            #            '%s, (%s), cache = __h.Component.strBool(%s)'
            #                ', defer = __h.Component.strBool(%s))' % 
            #            ( text, args['name'], argsarg, args['cache'],
            #              args['defer'] ) )
            codeout.write ( indent, '%s = __h.Component.callComponent ( '
                        '%s, (%s), cache = __h.Component.strCache(%s)'
                            ')' % 
                        ( text, args['name'], argsarg, args['cache'],
                           ) )
                                      
        else:
            # Render the component
            #codeout.write ( indent, '%s = __h.Component.callComponent ( '
            #                '%s, (%s), cache = __h.Component.strBool(%s)'
            #                ', defer = __h.Component.strBool(%s))' % 
            #                ( text, args['name'], kw, args['cache'],
            #                  args['defer'] ) )
            codeout.write ( indent, '%s = __h.Component.callComponent ( '
                            '%s, (%s), cache = __h.Component.strCache(%s)'
                            ')' % 
                            ( text, args['name'], kw, args['cache'],
                              ) )

        # Write the result
        codeout.write ( indent, '__h.OUTPUT.write ( %s )' % text )

        # Delete the temporary variable
        codeout.write ( indent, 'del %s' % text )
        if args['__args__']:
            codeout.write(indent, 'del %s' % argsarg)

class DataComponentTag(DTTag):
    """
    This tag is used to render components which return a pickleable 
    value
    """
    def __init__(self):
        DTTag.__init__ ( self, 'datacomp', isempty=1, 
                         modules = [ Component ] )

    def genCode(self, indent, codeout, tagreg, tag):
        DTCompilerUtil.tagDebug(indent, codeout, tag)
        #pargs=args=DTUtil.tagCall(tag, [ 'var', 'name', 
        #                                 ( 'cache', 'no'), ('defer', -1),
        #                                 ('__args__', None)],
        #                          kwcol='kw')
        pargs=args=DTUtil.tagCall(tag, [ 'var', 'name', 
                                         ( 'cache', 'no'), 
                                         ('__args__', None)],
                                  kwcol='kw')
        kw=DTCompilerUtil.pyifyKWArgs(tag, args['kw'])
        args=DTCompilerUtil.pyifyArgs(tag, args)

        varname = DTCompilerUtil.checkName(tag, 'var', args['var'],
                                           pargs['var'])
        if args['__args__']:
            argsarg = DTCompilerUtil.getTempName()
            codeout.write(indent, '%s = %s' % (argsarg, args['__args__']))
            codeout.write(indent, 'if type(%s) != __h.types.DictType:' % argsarg)
            codeout.write(indent+4, 'raise TypeError, "__args__ argument must'
                          ' be a dictionary"')
            codeout.write(indent, '%s.update(%s)' % (argsarg, kw))
            # Render the component
            #codeout.write (
            #    indent, '%s = __h.Component.callComponent ( '
            #    '%s, (%s), cache = __h.Component.strBool(%s)'
            #    ', defer = __h.Component.strBool(%s), '
            #    'compType = __h.Component.DT_DATA )' % 
            #    ( varname, args['name'], argsarg,
            #      args['cache'],
            #      args['defer']) )
            codeout.write (
                indent, '%s = __h.Component.callComponent ( '
                '%s, (%s), cache = __h.Component.strCache(%s)'
                ', compType = __h.Component.DT_DATA )' % 
                ( varname, args['name'], argsarg,
                  args['cache'],
                  ) )
            codeout.write( indent, 'del %s' % argsarg)
        else:
            # Render the component
            #codeout.write (
            #    indent, '%s = __h.Component.callComponent ( '
            #    '%s, (%s), cache = __h.Component.strBool(%s)'
            #    ', defer = __h.Component.strBool(%s), '
            #    'compType = __h.Component.DT_DATA )' % 
            #    ( varname, args['name'], kw, args['cache'],
            #      args['defer']) )
            codeout.write (
                indent, '%s = __h.Component.callComponent ( '
                '%s, (%s), cache = __h.Component.strCache(%s)'
                ', compType = __h.Component.DT_DATA )' % 
                ( varname, args['name'], kw, args['cache'] ))#,
            #args['defer']) )

class IncludeTag(DTTag):
    """
    This tag is used to run a component in parent namespace
    """
    def __init__(self):
        DTTag.__init__ ( self, 'include', isempty=1, 
                         modules = [ Component ] )

    def genCode(self, indent, codeout, tagreg, tag):
        DTCompilerUtil.tagDebug(indent, codeout, tag)
        args=DTUtil.tagCall(tag, [ 'name', ] )

        args=DTCompilerUtil.pyifyArgs(tag, args)

        text = DTCompilerUtil.getTempName()
        
        codeout.write(indent, '%s = __h.Component.callComponent ('
                              '%s, {}, '
                              'compType = __h.Component.DT_INCLUDE )' % 
                                            (text, args['name']) )

        codeout.write(indent, '__h.OUTPUT.write(%s)' % text)

        codeout.write(indent, 'del %s' % (text))
