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
import string
#from xml.parsers import xmllib
import xmllib

ParsingError = 'Parsing.Error'

class Node:
    pass

class Section(Node):
    def __init__(self, tag, id, isAppendix):
        self.id = id
        self.sections = []
        self.contents = []
        self.secNo = -1
        self.isAppendix = isAppendix
        self.title = '--<BLINK>NO TITLE</BLINK>--'
        self.tag = tag
        
    def numberMe(self, n):
        self.secNo = n
        for i in range(len(self.sections)):
            self.sections[i].numberMe("%s.%s" % (n, i+1))

class Document(Node):
    def __init__(self):
        self.tag = 'skunkdoc'
        self.title = ''
        self.subtitle = ''
        self.author = ''
        self.sections = []

class Generic(Node):
    def __init__(self, tag, args):
        self.contents = []
        self.tag = tag
        self.args = args

prelims = ['title', 'subtitle', 'author']
structure = ['chapter', 'appendix', 'section', 'subsection', 'subsubsection']

class Parser(xmllib.XMLParser):
    def __init__(self):
        xmllib.XMLParser.__init__(self)
        self.STACK = [ ]
        #chapShit = (self.chapStart, self.genEnd)
        #miniShit = (self.miniStart, self.genEnd)
        self.elements = {
            'skunkdoc': (self.tlStart, None),
            }
        for i in prelims + structure:
            self.elements[i] = (None, None)

        self.entitydefs = xmllib.XMLParser.entitydefs
        self.entitydefs.update({
            'lt': '&#38;lt;',
            'gt': '&#38;gt;',
            'amp': '&#38;amp;',
            'nbsp': '&#38;nbsp;'
            })

    def tlStart(self, tag):
        self.STACK.append(Document())

    def chapStart(self, tag, args):
        if (not isinstance(self.STACK[-1], Section)
            and not isinstance(self.STACK[-1], Document)):
            raise ParsingError, '%s tag in wrong context %s' % (tag, self.STACK[-1])
        id = args.get('id')
        if tag == 'appendix':
            isAppendix = 1
        else:
            isAppendix = 0
            
        s = Section(tag, id, isAppendix)
        self.STACK[-1].sections.append(s)
        self.STACK.append(s)


    def miniStart(self, tag, args):
        if len(args):
            raise ParsingError, 'arguments not allowed for tag %s' % tag
        if (not isinstance(self.STACK[-1], Document)
            and not isinstance(self.STACK[-1], Section)):
            raise ParsingError, '%s tag in wrong context %s' % (tag, self.STACK[-1])
        m = Generic(tag, args)
        setattr(self.STACK[-1], tag, m)
        self.STACK.append(m)

    def unknown_starttag(self, tag, args):
        #print '<%s %s>' % (tag, args), len(self.STACK)
        if tag == 'skunkdoc':
            self.tlStart(tag, args)
            return
        if tag in prelims:
            self.miniStart(tag, args)
            return
        elif tag in structure:
            self.chapStart(tag, args)
            return
        item = Generic(tag, args)
        self.STACK[-1].contents.append(item)
        self.STACK.append(item)

    def unknown_endtag(self, tag, *args):
        #print 'tag', tag
        if tag != 'skunkdoc':
            t = self.STACK.pop()
            if t.tag != tag:
                print "****end tag doesn't match start s:%s, e:%s" % (
                tag, t.tag), self.lineno
                raise ParsingError, 'ACK!'

    def handle_data(self, data):
        #print 'stacklen->', len(self.STACK)
        if not isinstance(self.STACK[-1], Document):
            self.STACK[-1].contents.append(data)
            
def parseString(text):
    p = Parser()
    f = '<skunkdoc>' + text + '</skunkdoc>'
    
    p.feed(f)
    p.close()

    d = p.STACK[0]

    cntr = 1
    inAppendix = 0
    for s in d.sections:
        if s.isAppendix and not inAppendix:
            inAppendix = 1
            cntr = ord('A')
        if s.isAppendix:
            s.numberMe(chr(cntr))
        else:
            s.numberMe(str(cntr))
        cntr = cntr + 1

    return d
            

def parseFile(filename):
    return parseString(open(filename).read())

def test():
    return parseFile('/home/drew/devel/skunk/AED/docs/develop.xml')

#a = test()

