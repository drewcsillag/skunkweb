#  
#  Copyright (C) 2001 Andrew T. Csillag <drew_csillag@geocities.com>
#  
#      You may distribute under the terms of either the GNU General
#      Public License or the SkunkWeb License, as specified in the
#      README file.
#   
import sys
import string
import ParseSkunkDoc

def doDocString(s):
    """**if <code>s</code> starts with '**', it contains xml markup, so don't
    do anything to it (except trim off the '**', otherwise, xml escape it and
    return it"""

    if s is None:
        return ""
    # Made ** able to occur after whitespace at start of docstring
    s = string.strip(s)

    if s[:2] == '**':
        s = s[2:]
        try:
            ParseSkunkDoc.parseString(s)
        except:
            sys.stderr.write('error parsing XML doc string %s, treating '
                             'as plaintext\n' % s)
            s = '<pre>%s</pre>' % string.replace(plainEscape(s), '&', '&amp;')
    else:
        s = '<pre>%s</pre>' % string.replace(plainEscape(s), '&', '&amp;')
    return '%s' % s

def plainEscape( s ):
    '''**xml escape the string <code>s</code>'''
    ns = []
    for c in s:
        if c == '&': ns.append('&amp;')
        elif c == '<': ns.append('&lt;')
        elif c == '>': ns.append('&gt;')
        elif c in ('\n', '\r', '\t'): ns.append(c)
        elif c == '"': ns.append('&quot;')
        elif ord(c) < 32 or c > 'z': ns.append('&#%d;' % ord(c))
        else: ns.append(c)
    return string.join(ns, '')

