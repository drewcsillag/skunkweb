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
Class implementing DT exceptions. All exceptions raised inside templates 
SHOULD inherit from these exceptions
"""
# $Id: DTExcept.py,v 1.9 2001/07/09 20:38:41 drew Exp $

import string

import SkunkExcept
import ErrorHandler
import string

class DTCompileError ( SkunkExcept.SkunkCustomError ):
    """
    This is a general purpose error, to be raised during compilation stage of
    a template
    """
    def __init__ ( self, tag, desc ):
        SkunkExcept.SkunkCustomError.__init__(self, desc)
        self._tag = tag
        self._desc = desc

    def format ( self ):
        """
        Print self nicely
        """
        ret = ErrorHandler._error

        ret = ret + 'Cannot compile template %s\n' % self._tag.filename()
        ret = ret + 'Template: %s, line %d\n' % (self._tag.filename(), 
                                                 self._tag.lineno())
        ret = ret + 'Tag: %s\n' % self._tag
        ret = ret + 'Error: %s\n' % self._desc 
        ret = ret + ErrorHandler._close

        return ret

class DTLexicalError ( SkunkExcept.SkunkCustomError ):
    # XXX Now, doesn't always pass in 'name' - Drew, please fix if you can
    def __init__(self, lineno, msg, name = None, tagtext=''):
        SkunkExcept.SkunkCustomError.__init__ ( self, msg )
        self.msg=msg
        self.tagtext=tagtext
        self.startoff=-1
        self.lineno=lineno
        self.name=name

    def format(self):
        ret = ErrorHandler._error

        ret = ret + 'Cannot compile template %s\n' % self.name

        # XXX Should *always* supply name and line number
        ret = ret + 'Template: %s, line %d\n' % (self.name, self.lineno)
        if self.tagtext:
            ret = ret + 'Tag: <:%s:>\n' % self.tagtext
        ret = ret + 'Error: %s\n' % self.msg
        ret = ret + ErrorHandler._close

        return ret

    def __repr__(self):
        return self.format()

    def __str__(self):
        return repr(self)
    

class DTRuntimeError ( SkunkExcept.SkunkCustomError ):
    """
    This exception should be raised if an error happens during an evaluation of
    a tag. 
    """
    def __init__ ( self, tag, fileline, *args ):
        apply ( SkunkExcept.SkunkCustomError.__init__, 
                (self,) + args ) 

        # Tag is the string represenation of the tag, lineno is the
        # component:line string
        self._filename, self._lineno = tuple ( string.split ( fileline, ':' ))
        self._tag = tag

    def format ( self ):
        """
        This is the actual function which will be used to generate the error
        message
        """
        ret = ErrorHandler._error
        ret = ret + 'Template: %s, line %d\n' % ( self._filename, self._lineno )
        ret = ret + 'Tag: %s\n' % self._tag
        ret = ret + 'Error: %s\n' % str(self.args[0])
        ret = ret + ErrorHandler._close

        return ret

#
# This is a special case exception
#
class DTHaltError ( DTRuntimeError ):

    def __init__ ( self, tag, fileline, *args ):
        apply ( DTRuntimeError.__init__, (self, tag, fileline) + args )

    def format ( self ):
        ret = ErrorHandler._error
        ret = ret + 'Halt exception uncatched! This is an AED internal error\n'
        ret = ret + 'Template: %s, line %d\n' % ( self._filename, self._lineno )
        ret = ret + 'Tag: %s\n' % self._tag
        ret = ret + 'Text: %s\n' % str(self.args[0])
        
        return ret

#
# This is a helper function to generate exception raising code during runtime
# of a template 
#
def raiseRuntime ( output, indent, msg ):
     """
     Generate a code which raises a runtime exception. DTExcept should be 
     preloaded in __h
     """
     output.write ( indent, 'raise __h.DTExcept.DTRuntimeError ( '
                            '__d.CURRENT_TAG, __d.CURRENT_LINENO, "%s")' % msg )

def raiseHalt ( output, indent, msg = 'generic halt' ):
     """
     Helper function to do halt
     """
     output.write ( indent, 'raise __h.DTExcept.DTHaltError ( '
                            '__d.CURRENT_TAG, __d.CURRENT_LINENO, "%s")' % msg )
