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
Assortment of HTML tags - description???
"""
# $Id: HTMLTags.py,v 1.2 2001/08/10 17:35:32 drew_csillag Exp $

from AE.CommonStuff import *
import SkunkExcept
import UrlBuilder

# curl is now url; get used to it
class UrlTag(DTTag):
    def __init__(self, func = '__h.UrlBuilder.url' ):
        self.func = func
        DTTag.__init__(self, 'url', isempty=1, modules = [UrlBuilder] )

    def genCode(self, indent, codeout, tagreg, tag):
        DTCompilerUtil.tagDebug(indent, codeout, tag)
        args=DTUtil.tagCall(tag, [
            ('path'), ('queryargs', {}),
            ('text', 'None'), ('noescape', 'None')], kwcol = 'kw'  )
        args=DTCompilerUtil.pyifyArgs(tag, args)
        kw = DTCompilerUtil.pyifyKWArgs(tag, args['kw'])

        # Ok, just call the templating curl function
        codeout.write ( indent, '__h.OUTPUT.write ( '
                '%s ( path = %s, queryargs = %s, text = %s, noescape = %s, '
                'kwargs = %s ) )' % (self.func, args['path'],
                args['queryargs'], args['text'], args['noescape'], kw ))

        # Cool, huh?


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
