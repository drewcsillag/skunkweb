#  
#  Copyright (C) 2001 Andrew T. Csillag <drew_csillag@geocities.com>
#  
#      You may distribute under the terms of either the GNU General
#      Public License or the SkunkWeb License, as specified in the
#      README file.
#   
"""
Assortment of HTML tags - description???
"""

from AE.CommonStuff import *
import SkunkExcept
import UrlBuilder

class UrlTag(DTTag):
    def __init__(self, func = '__h.UrlBuilder.url' ):
        self.func = func
        DTTag.__init__(self, 'url', isempty=1, modules = [UrlBuilder] )

    def genCode(self, indent, codeout, tagreg, tag):
        DTCompilerUtil.tagDebug(indent, codeout, tag)
        args=DTUtil.tagCall(tag,
                            [('path'), ('queryargs', {}),
                             ('text', 'None'),
                             ('noescape', 'None'),
                             ('abs', 'None')],
                            kwcol = 'kw')
        args=DTCompilerUtil.pyifyArgs(tag, args)
        kw = DTCompilerUtil.pyifyKWArgs(tag, args['kw'])

        # Ok, just call the templating url function
        codeout.write(indent,
                      '__h.OUTPUT.write('
                      '%s ( path = %s, queryargs = %s, text = %s, noescape = %s, '
                      'need_full=%s, kwargs = %s ) )' % (self.func,
                                                         args['path'],
                                                         args['queryargs'],
                                                         args['text'],
                                                         args['noescape'],
                                                         args['abs'],
                                                         kw ))


class ImageTag(DTTag):
    def __init__(self, func = '__h.UrlBuilder.image' ):
        self.func = func
        DTTag.__init__(self, 'img', isempty=1, modules = [UrlBuilder] )

    def genCode(self, indent, codeout, tagreg, tag):
        DTCompilerUtil.tagDebug(indent, codeout, tag)
        args=DTUtil.tagCall(tag, [
            ('path'), ('queryargs', {}),
	    ('noescape', 'None')], kwcol = 'kw' )
        kw=DTCompilerUtil.pyifyKWArgs(tag, args['kw'])
        args=DTCompilerUtil.pyifyArgs(tag, args)

        codeout.write ( indent, '__h.OUTPUT.write ( '
                '%s ( path = %s, queryargs = %s, noescape = %s, kwargs = %s ) )' % \
                        (self.func,
                         args['path'],
                         args['queryargs'],
                         args['noescape'],
                         kw) )

        # All done

class FormTag(DTTag):
    def __init__(self, func = '__h.UrlBuilder.form' ):
        self.func = func
        DTTag.__init__(self, 'form', isempty=1, modules = [UrlBuilder] )

    def genCode(self, indent, codeout, tagreg, tag):
        DTCompilerUtil.tagDebug(indent, codeout, tag)
        args=DTUtil.tagCall(tag, [ ('path', ), ('noescape', 'None') ], kwcol = 'kw' )
        kw=DTCompilerUtil.pyifyKWArgs(tag, args['kw'])
        args=DTCompilerUtil.pyifyArgs(tag, args)

        codeout.write ( indent, '__h.OUTPUT.write ( '
                '%s ( %s, noescape = %s, kwargs = %s ) )' % (self.func, args['path'], args['noescape'], kw) )
        
class HiddenTag(DTTag):
    """
    Retain variables which are passed between cgi's - hidden fields in 
    forms
    """
    def __init__(self):
        DTTag.__init__(self, 'hidden', isempty=1, modules = [UrlBuilder])

    def genCode(self, indent, codeout, tagreg, tag):
        DTCompilerUtil.tagDebug(indent, codeout, tag)
        args=DTUtil.tagCall(tag, [], kwcol='kw')
        kw=DTCompilerUtil.pyifyKWArgs(tag, args['kw'])
        codeout.write(indent, '__h.OUTPUT.write ( __h.UrlBuilder.hidden(%s))' 
                              % kw)

class RedirectTag(DTTag):
    def __init__(self, func = '__h.UrlBuilder.redirect' ):
        DTTag.__init__ ( self, 'redirect', isempty=1, modules = [ SkunkExcept,
                                                                  UrlBuilder])
        self.func = func

    def genCode(self, indent, codeout, tagreg, tag):
        DTCompilerUtil.tagDebug(indent, codeout, tag)
        args=DTUtil.tagCall(tag, [('path', 'None'),
                                  ('url', 'None'),
                                  ('queryargs', {}),
				  ('noescape', 'None')],
                                  )#kwcol = 'kw' )
        #kw=DTCompilerUtil.pyifyKWArgs(tag, args['kw'])
        args=DTCompilerUtil.pyifyArgs(tag, args)

	# here's the real function call
        codeout.write ( indent, '%s ( url = %s, path = %s, queryargs = %s, '
                                'noescape = %s)' % #, kwargs = %s)' % 
                      ( self.func, args['url'], args['path'], 
                        args['queryargs'], args['noescape']))#, kw) )
