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
Here the message catalog tags are implemented
"""
# $Id: MsgCatalogTags.py,v 1.3 2001/07/09 20:38:41 drew Exp $

import string

from CommonStuff import *
import MsgCatalog, Cache
from SkunkExcept import *
import SkunkExcept
from Logs import DEBUG, WEIRD

class CatalogTag ( DTTag ):
    """
    General purpose catalog tag - supports both multi-language and basic 
    catalogs
    """

    def __init__ ( self ):
        DTTag.__init__ ( self, 'catalog', isempty = 1,
                         modules = [ MsgCatalog, Cache ])

    def checkCatName(self, catname):
        DEBUG(WEIRD, "in checkCatName, stub version")
        return catname

    def genCode ( self, indent, codeout, tagreg, tag ):
        """
        Generate our code
        """

        DTCompilerUtil.tagDebug ( indent, codeout, tag )

        pargs = args = DTUtil.tagCall ( tag, [ 'catname', 'name' ] )

        args = DTCompilerUtil.pyifyArgs ( tag, args )

        name = DTCompilerUtil.checkName(tag, 'name', args['name'],
                                        pargs['name'])

        # this hook is to accomodate the aed-compat module
        catname=self.checkCatName(args['catname'])
        
        # Call the create catalog function and assign the result to variable
        codeout.write ( indent, '%s = __h.Cache.getMessageCatalog '
                        '( %s )' % ( name, catname ))

        # All done

class MessageTag ( DTTag ):

    def __init__ ( self ):
        DTTag.__init__ ( self, 'msg', isempty = 1, 
                         modules = ( MsgCatalog, SkunkExcept, string ) )

    def genCode ( self, indent, codeout, tagreg, tag ):
        """
        Generate our code
        """
        DTCompilerUtil.tagDebug ( indent, codeout, tag )

        # Message name is in msgObject.msgName format
        args = DTUtil.tagCall ( tag, [ 'catname', 'msgname', 
                                     ( 'lang', 'None' ), 
				     ('fmt', 'None') ],
                                 kwcol = 'kw' )

        pargs = DTCompilerUtil.pyifyArgs ( tag, args )
        kw = DTCompilerUtil.pyifyKWArgs ( tag, pargs['kw'] )

        # Cool, now let's check if the message catalog exists
        text = DTCompilerUtil.getTempName()
        fmt = DTCompilerUtil.getTempName()
        catname = args['catname']

        codeout.write ( indent, 'try:' )
        codeout.write ( indent+4, 'if %s:' % pargs['fmt'] )
        codeout.write ( indent+8, '%s = __h.VALFMTRGY[%s]' % ( fmt, 
                                                               pargs['fmt'] ))
        codeout.write ( indent+4, 'else:' )
        codeout.write ( indent+8, '%s = lambda x:x' % fmt )
        codeout.write ( indent, 'except:' )
        codeout.write ( indent+4, 'raise __h.SkunkExcept.SkunkStandardError, '
              '"unknown formatting: %s, use one of (%%s)" %% '
              '__h.string.join ( __h.VALFMTRGY.keys(), "," )' % pargs['fmt'] )

        codeout.write ( indent, '%s = __h.MsgCatalog.getMessage ( %s, %s, '
                        'lang = %s, fmt = %s, bindvars = %s) ' % 
                        ( text, catname, pargs['msgname'], 
                          pargs['lang'], fmt, kw ) )
                                            
        codeout.write ( indent, '__h.OUTPUT.write ( %s )' % text )

        codeout.write ( indent, 'del %s, %s' % (text, fmt))

#
# Create the tag list
#
CatalogTags = [ CatalogTag(), MessageTag() ]
