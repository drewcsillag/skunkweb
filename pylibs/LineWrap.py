#  
#  Copyright (C) 2001 Andrew T. Csillag <drew_csillag@geocities.com>
#  
#      You may distribute under the terms of either the GNU General
#      Public License or the SkunkWeb License, as specified in the
#      README file.
#   
"""
A module to do configurable text wrapping, 
useful for formatting text where
you want to wrap lines at a particular column, but
to do it gracefully without chopping words apart.
"""
import StringIO
import string

from types import IntType, FunctionType

def _breakline(line, maxlen, indent, breakpoint):
    rlines = []
    curmaxlen = maxlen
    while line:
        curmaxlen = maxlen
        
        #chop off maxlen chars
        chunk = line[:maxlen]

        # do indentation stuff
        if type(indent) == IntType and rlines:
            spaces, chunk = indent * ' ', chunk[:-indent]
        elif type(indent) == FunctionType:
            spaces, chunk, curmaxlen = indent(chunk, rlines, curmaxlen)
        else:
            spaces = ''
            
        #if line is ok, just append and stop
        if len(line) <= curmaxlen: 
            rlines.append(spaces + string.lstrip(line))
            break
        
        #break a point spec'd by user-defined function
        if breakpoint:
            ind = breakpoint(chunk)
        else: #else, try to break on space, then tab
            ind = string.rfind(chunk, ' ')
            if ind == -1:
                ind = string.rfind(chunk, '\t')

        # no breakpoint, break on maxlen
        if ind < 1:
            ind = curmaxlen

        rlines.append(spaces + string.lstrip(chunk[:ind]))
        line = line[ind:]

    return rlines

def wraplines(text, maxlinelen = 80, indent = None, breakpoint = None):
    """
    Given a string, returns a string with lines wrapped to  
    maxlinelen, with "\n" characters separating the lines.

    Parameters:
    
    text - text that you want to wrap
    maxlinelen - maximum line length
    indent - either a number indicating that subsequent
             lines should be indented by this much, or a function that is
             called with the unprocessed text so far, the current list of
             broken lines and the maximum legth of a line and returns
             a string to be prepended to the current line, the text of
             the line, and the new maximum length
    breakpoint - a function that given a line returns an
                 integer index representing a good place to break the line
    """
    f=StringIO.StringIO(text)
    outl = []
    for i in f.readlines():
        i = string.rstrip(i)
        if len(i) <= maxlinelen:
            outl.append(i)
            continue
        nlines = _breakline(i, maxlinelen, indent, breakpoint)
        map(outl.append, nlines)
    return string.join(outl, '\n')    

if __name__=='__main__':
    ll="""thi si a really long line for breakline to try to split in a decent way if it can, perhaps it can, but maybe it can't"""
    print wraplines(ll, 30)

    print
    print wraplines(ll, 30, 4)
