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
# $Id: SkunkExcept.py,v 1.1.1.1 2001/08/05 15:00:23 drew_csillag Exp $

"""
This module provides a set of exception classes for use in
scripts, programs and servers which want a way to raise
"warnings", "severe errors", "critical errors", and the like.

The SkunkWeb server, and several skunk.org "pylibs"
modules, use these exception classes. You can use them in 
your own programs if you need escalating levels of errors.
If you only need regular exceptions, use Python's built-in
exceptions or make your own.

This module and its exception classes work with the
ErrorHandler module to generate logging info
and do some graceful exception handling.

Generally, we recommend the following guidelines when
using these exceptions:

If it's likely to be a programming error on your part 
or on part of someone using your code, raise either a standard 
python exception or a SkunkCriticalError.

If it's a misconfiguration, or a resource is not available, 
or any general OS problem, raise a SkunkRuntimeError or
SkunkStandardError with enough info in the error string
for whoever runs the system to be able to look at the log 
and fix whatever is broken.
"""

# Get the standard exceptions
import exceptions
import types
import string

import ErrorHandler

# XXX These will have to be moved to error handler when (if?) I ever
# write one
_NO_ERROR = 0           # Just the message with no mention of error
_NO_TRACE = 1           # Just the message 
_LOW_TRACE = 2          # Some file / line / function info
_FULL_TRACE = 3         # Do the whole thing
_USE_FORMAT = 4         # Use the format function

class SkunkException ( exceptions.Exception ):
    """
    Just like a regular Python exception, 
    only with trace level set to show info 
    for error handling and logging.
    This is a base class, and must be subclassed
    and the format method implemented
    in order to be usable.
    """
    def __init__ ( self, trace_level, *args ):
        
        # Init the higher level class
        apply ( exceptions.Exception.__init__, ( self, ) + args )

        # Set the default trace level
        self.tlevel = trace_level

    def trace_level ( self ):
        "Return our trace level"
        return self.tlevel

    def format ( self ):
        raise NotImplementedError

    def __str__ ( self ):
        """
        Return a representation of self, useful in default python 
        traceback module
        """
        try:
            ret = '\n' + self.format()
        except NotImplementedError:
            # Fall back
            ret = exceptions.Exception.__str__ ( self )
        except:
            # re-raise
            raise

        return ret

#
# These are more general purpose errors, written with AED in mind
#
class SkunkCriticalError ( SkunkException ):
    "Should be thrown when we're in deep sh$t."
    def __init__(self, *args ):
        apply ( SkunkException.__init__,  ( self, _FULL_TRACE) + args )

class SkunkRuntimeError ( SkunkException ):
    "Should be thrown when a little debug info is needed."
    def __init__(self, *args ):
        apply ( SkunkException.__init__,  ( self, _LOW_TRACE) + args )

class SkunkStandardError ( SkunkException ):
    """
    Just throw this instead of sys.exit() when your 
    program wants to bail out.
    """
    def __init__(self, *args ):
        apply ( SkunkException.__init__, ( self, _NO_TRACE) + args )

class SkunkBailout ( SkunkException ):
    """
    Throw this for conditions that warrant exiting, 
    but are not erroneous, but should still be logged.
    """
    def __init__(self, *args ):
        apply ( SkunkException.__init__, ( self, _NO_ERROR) + args )
    
class SkunkCustomError ( SkunkException ):
    """
    General purpose exception. You can subclass from it to 
    have custom exceptions which define the format method 
    to be used in conjunction with the ErrorHandler module to 
    generate errors."""
    def __init__(self, *args ):
        apply ( SkunkException.__init__, ( self, _USE_FORMAT) + args )

    def format ( self ):
        """
        This should be overloaded
        """
        raise NotImplementedError

class SkunkSyntaxError ( SkunkCustomError ):
    """
    This is a wrapper exception to generate nice syntax errors. 
    If you find a syntax error in something the user has done,
    pass the original syntax error to SkunkSyntaxError().
    
    """

    def __init__ ( self, filename, text, syntax_exc, description = '', 
                         context = 5 ):

        if description:
            SkunkCustomError.__init__ ( self, description )
        else:
            SkunkCustomError.__init__ ( self, syntax_exc )

        self._filename, self._text = filename, text

        if type(syntax_exc) != types.InstanceType and \
                      not issubclass ( SyntaxError, syntax_exc.__class__ ):
            raise SkunkRuntimeError, 'invalid argument, SyntaxError ' \
                                     'instance expected'
        self._exc = syntax_exc
        self._context = context
        self._desc = description

    def format ( self ):
        """
        Format self nicely
        """

        lineno, offset, line = self._exc.lineno, self._exc.offset, \
                               self._exc.text

        if not lineno and not offset and not line:
            # This is a f#$#ed up syntax error
            err = ErrorHandler._error
            err = err + 'Syntax error in file %s\n' % self._filename
            err = err + 'Error: %s\n' % str ( self._exc )
            err = err + 'Unfortunately, due to Python compiler limitations' \
                        ' context is not available\n' 
            err = err + ErrorHandler._close

            return err

        lineno = lineno - 1

        lines = string.split ( self._text, '\n' )

        begin = lineno - self._context
        if begin < 0:
            begin = 0

        end = lineno + self._context
        if end > len(lines):
            end = len(lines)

        before = lines[begin:lineno]
        after = lines[lineno+1:end + 1]

        # Generate the error
        err = ErrorHandler._error

        if self._desc:
            err = err + self._desc + '\n'

        err = err + 'Syntax error in file %s, line %d, context:\n' % \
                 (self._filename, lineno + 1)
        err = err + string.join ( before, '\n' ) + '\n'
        err = err + line
        err = err + '-' * (offset - 1) + '^\n'
        err = err + string.join ( after, '\n' ) + '\n'
        err = err + ErrorHandler._close

        return err
