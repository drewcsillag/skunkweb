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

