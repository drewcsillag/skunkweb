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
# $Id: ErrorHandler.py,v 1.14 2001/07/27 16:25:09 drew Exp $
# 
"""
This module implements some pretty error handling 
features, and is used with the exceptions in
 the SkunkExcept module.
"""

import traceback
import sys
import cStringIO
StringIO = cStringIO
import types
import string

# Local includes
import SkunkExcept 

#
# This variable can be changed to indicate that debugging is on
#
_debug = 0

#
# Some helper strings
#
_unh_exc =    '!!!!!! Skunk Unhandled Exception !!!!!!!\n'
_error =      '====== Skunk Error Encountered =========\n'
_close =      '----------------------------------------\n'

def handle ( do_exit = 1 ):
    """This function should be called on the top level, inside the main 
    try...except block. It does complete error handling and exits."""

    if sys.exc_info()[0] == SystemExit:
        """Just re-raise it then"""
        raise

    # Show the exception
    logError()

    # Exit
    if do_exit:
        sys.exit ( 1 )

def logError ( file = None ):
    """This function can be used to just log the error to whatever logging 
    facility is currently used. Uses standard python traceback module to 
    generate errors. 
    
    Should be called within an exception - uses sys.exc_info() to obtain 
    info"""

    # XXX assignment of tb causes circular reference - let's live with 
    # it though
    tp, val, tb = sys.exc_info()

    # basically, just print the exception
    try:
        _showException ( tp, val, tb, file )
    finally:
        del tb

def debugError():
    """This function could be called to have a place where traceback / error
    logging needs to be printed in case debugging is turned on, like before 
    re-throwing an exception. If debugging is turned off, the function does
    nothing"""

    if ( _debug ):
        logError()

def readError():
    """
    Return the formatted exception as a string
    """
    import cStringIO
    f = cStringIO.StringIO()
    logError ( f )
    data = f.getvalue()
    f.close()

    return data

def _format_list ( extracted_list ):
    """
    Own implementation of format_list, to handle line continuations 
    properly
    """
    import linecache

    list = []
    for filename, lineno, name, line in extracted_list:
        item = '  File "%s", line %d, in %s\n' % (filename,lineno,name)
        while line:
            line = string.strip ( line )
            item = item + '    %s\n' % line
            if line[-1] == '\\':
                 # Print the next line
                 lineno = lineno + 1
                 line = linecache.getline ( filename, lineno )
            else:
                 break

        list.append(item)

    return list

def _showException ( tp, value, tb, outf = None ):
    """This is used to actually print the exception. Here we handle our 
    implementaion specific exceptions
    
    The function is responsible for formatting the exception and printing the 
    traceback if required"""

    try:
        if not outf:
            outf = sys.stderr

        if type(tp) == types.ClassType and issubclass ( tp, 
                                SkunkExcept.SkunkException ):

            trace_level = value.trace_level()

            #
            # I hate stupid additional debug, so I disabled it. Roman
            #
            #if _debug and trace_level != SkunkExcept._USE_FORMAT:
            #    trace_level = SkunkExcept._FULL_TRACE

            # This is our error, handle it
            if trace_level == SkunkExcept._NO_ERROR:
                #just print the message
                outf.write ( '%s\n' % str(value) )
            elif trace_level == SkunkExcept._USE_FORMAT:
                try:
                    outf.write ( value.format() )
                except:
                    # We can't fail inside this module!
                    outf.write ( 'CUSTOM ERROR FORMAT FAILED\n' )
                    outf.write ( 'Original exception: %s\n' % str(value) )
                    outf.write ( 'Error during format: %s: %s\n' % 
                                 (sys.exc_info()[0], sys.exc_info()[1] ) )

            elif trace_level == SkunkExcept._NO_TRACE:
                # Just print the error
                outf.write ( 'Skunk error encountered: %s\n' % str(value) )

            elif trace_level == SkunkExcept._LOW_TRACE:
                # Print the error and some file / line information
                outf.write ( _error )
                
                # Extrace single entry
                vals = traceback.extract_tb ( tb )[-1]

                outf.write ( '==> File %s, line %d, in %s():\n' % vals[:3] )
                outf.write ( '==> Skunk error: %s\n' % str(value) )

                outf.write ( _close )

            elif trace_level == SkunkExcept._FULL_TRACE:
                # Show full debugging info 
                outf.write ( _error )

                # Extract first entry 
                trace = traceback.extract_tb ( tb )
                vals = trace[-1]

                # Print full traceback
                outf.write ( '==> Traceback:\n' )

                map ( lambda x, f=outf: f.write ( x ), 
                      _format_list ( trace[1:] ) )

                outf.write ( '==> File %s, line %d, in %s():\n' % vals[:3] )
                outf.write ( '==> Skunk error: %s: %s\n' % ( tp, str(value)) )

                outf.write ( _close )

            else:
                # Hope someone catches it :-)
                raise SkunkExcept.CriticalError, 'unknown trace level: %d' % \
                                                 trace_level
        elif tp == KeyboardInterrupt:
            # Handle keyboard interrupt gracefully
            vals = traceback.extract_tb ( tb )[-1]

            outf.write ( '==> File %s, line %d, in %s():\n' % vals[:3] )
            outf.write ( '==> KeyboardInterrupt caught!\n' )
        else:
            # Do a nice attention catching wrap
            outf.write ( _unh_exc )

            # Do the standard exception handling, not forgetting about a full 
            # traceback
            traceback.print_exception(tp, value, tb, limit = None, file = outf )

            # Close the wrap
            outf.write ( _close )
    finally:
        # Clean up circular reference
        del tb
