#  
#  Copyright (C) 2001 Andrew T. Csillag <drew_csillag@geocities.com>
#  
#      You may distribute under the terms of either the GNU General
#      Public License or the SkunkWeb License, as specified in the
#      README file.
#   

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
        err=[]
        if not (lineno and offset and line):
        #if not lineno and not offset and not line:            
            # This is a f#$#ed up syntax error
            srclines = self._text.split('\n')
            err=[ErrorHandler._error,
                 'Syntax error in file %s\n' % self._filename,
                 'Error: %s\n' % str ( self._exc ),
                 'Unfortunately, due to Python compiler limitations',
                 ' context is not available\n',
                 'Program text is\n%s' %
                 '\n'.join(["%04d: %s" % (i+1, srclines[i])
                            for i in range(len(srclines))]), 
                 ErrorHandler._close]

            return ''.join(err)

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
        err=[ErrorHandler._error]

        if self._desc:
            err.append('%s\n' % self._desc)

        err.append('Syntax error in file %s, line %d, context:\n' % \
                   (self._filename, lineno + 1))
        err.append(''.join(['%s\n' % x for x in before]))
        if line:
            err.append(line)

        err.append('-' * (offset - 1) + '^\n')
        err.append(''.join(['%s\n' % x for x in after])) 
        err.append(ErrorHandler._close)

        return ''.join(err)
