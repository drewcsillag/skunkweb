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
"""**do common stuff that's needed by the html renderers"""
import sys, string
from scanners import common, ParseSkunkDoc


markupDict = {
    'wbr': ( '<wbr>', '', 0),
    'nobr': ('<nobr>', '', 0),
    'hr': ( '<hr>', '', 0),
    'tt': ( '<code>', '</code>', 0),
    'pre': ( '<pre>', '</pre>', 0),
    'ul': ( '<ul>', '</ul>', 0 ),
    'ol': ( '<ol>', '</ol>', 0 ),
    'li' : ( '<li>', '</li>', 0 ),
    'i' : ( '<i>', '</i>', 0 ),
    'b' : ( '<b>', '</b>', 0 ),
    'code': ( '<code>', '</code>', 0),
    'codeblock': ('<pre><code>', '</code></pre>', 0 ),
    'table': ('<table%s>', '</table>', 1 ),
    'tr': ('<tr>', '</tr>', 0 ),
    'td': ('<td%s>', '</td>', 1 ),
    'th': ('<th%s>', '</th>', 1 ),
    'p': ('<P>', '', 0),
    'br': ('<BR>', '', 0),
    'img': ('<img%s>', '', 1),
    'a': ('<a%s>', '</a>', 1),
    'dd': ('<DD>', '</DD>', 0),
    'dl': ('<DL>', '</DL>', 0),
    'dt': ('<DT>', '</DT>', 0),
#    'font': ('<FONT%s>', '</FONT>', 1),
    'h1': ('<H1>', '</H1>', 0),
    'h2': ('<H2>', '</H2>', 0),
    'h3': ('<H3>', '</H3>', 0),
    }

def getMarkup( tagName, arguments ):
    """**given the tagname <code>tagName</code> and it's argument dict
    <code>arguments</code>, produce the HTML markup for the begin and end
    for it"""
    try:
        b, e, takesArguments = markupDict[ tagName ]
    except KeyError, val:
        raise 'NoSuchTagName', 'invalid tag name %s' % val
    
    if takesArguments:
        s = []
        for k, v in arguments.items():
            s.append('%s="%s"' % ( k, v ))
        b = b % (' ' + string.join( s ))
    return b, e

def renderDocString( text ):
    tree = ParseSkunkDoc.parseString(text)
    return _renderDocString(tree)

def _renderDocString( item ):
    '''**takes the parse node that represents the doc string and renders
    it into HTML'''
    s = []
    for subItem in item:
        if type( subItem ) == type( '' ): #'tis a string
            s.append( subItem )
        elif isinstance( subItem, ParseSkunkDoc.EntityContainer ):
            beginTag, endTag = getMarkup( subItem.tag, subItem.attributes )
            if subItem.tag == 'codeblock':
                s.append( '%s%s%s' % (
                    beginTag, common.plainEscape(subItem.getText())
                    , endTag))
            else:
                s.append( '%s%s%s' % (beginTag, _renderDocString( subItem ),
                          endTag ))

    #convert blank lines to <p>
    ns = string.join( s, '' )
    ns = string.replace(ns, '\r\n', '\n')
    return string.replace(ns, '\n\n', '\n<p>\n')

