#  
#  Copyright (C) 2001 Andrew T. Csillag <drew_csillag@geocities.com>
#  
#      You may distribute under the terms of either the GNU General
#      Public License or the SkunkWeb License, as specified in the
#      README file.
#   
import string
import xmllib
#from xml.parsers import xmllib

textContainers = ('docstring', 'signature', 'ul', 'ol', 'b', 'i', 'li',
                  'code', 'codeblock', 'a', 'table', 'tr', 'td', 'th',
                  'p', 'br',
                  'base', 'import', 'source', 'pre', 'tt', 'xref', 'title',
                  'author', 'subtitle', 'dd', 'dt', 'dl', 'font',
                  'h1', 'h2', 'h3', 'chapter', 'section', 'subsection',
                  'subsubsection', 'appendix', 'index', 'img')

#tags that are invalid in docstrings
regularDocumentationOnly = ('h1', 'h2', 'h3', 'chapter', 'section',
                            'subsection', 'subsubsection', 'appendix',
                            'index', 'img')
                        
nonTextContainers = ('PYDOC', 'class', 'bases', 'function', 'module',
                     'component', 'datacomp', 'template', 'caches', 'cache',
                     'includes', 'componentcalls', 'datacompcalls', 'imports'
                     )

# the parser uses these elements to keep track of 
# where it is during parsing, so that if a docstring
# does not parse, the resulting error can say
# exactly where it is. The order is hierarchical...
trackingContainers = ('module', 'class', 'function',
                      'component', 'datacomp', 'template')

class EntityContainer:
    """**generic container for xml entities and data
    produced by the xml parser"""
    def __init__(self, tag, attributes):
        '''**initialize the entity container with the tag name
        <code>tag</code> and the xml attribute dictionary
        <code>attributes</code>.  This is called by the <code>XMLParser</code>
        to build the parse tree of the xml document'''
        self.tag = tag
        self.attributes = attributes
        self.children = []
        self.kindCache = {}
        
    def append(self, thing):
        """**attach subordinate entities to me"""
        self.children.append( thing )

    def addData(self, data):
        """**add cdata to me if appropriate"""
        if self.tag not in textContainers: return
        self.children.append( data )

    def getText(self):
        """**get text of children, only use if all children should be
        text"""
        return string.join(self.children,'')

    def getKind(self, kind):
        if self.kindCache.get( kind ) is None:
            bits = []
            for i in self:
                if type(i) != type('') and i.tag == kind:
                    bits.append(i)
            self.kindCache[kind] = bits
        return self.kindCache[kind]

    def templates(self):
        if self._modules is None:
            self._modules = filter(lambda x:x.tag == 'module', self)
        return self._modules

    def __repr__(self):
        return '<%s %s>%s' % (self.tag, self.attributes, self.children)

    def __getitem__(self, item):
        return self.children[item]

    def __len__(self):
        return len(self.children)

class XMLParser(xmllib.XMLParser):
    """**xml parser sublcass to parse skdml"""
    def __init__(self):
        """**Hmmm, I take no arguments... Figure that..."""
        xmllib.XMLParser.__init__(self)
        self.STACK = [ [] ]
        noneTup = (None, None)
        self.elements = {}
        for i in textContainers:
            self.elements[i] = noneTup

        self.entitydefs = xmllib.XMLParser.entitydefs
        self.entitydefs.update({
            'lt': '&#38;lt;',
            'gt': '&#38;gt;',
            'amp': '&#38;amp;',
            'nbsp': '&#38;nbsp;'
            })
        
#        self.entitydefs.update({
#            'lt': '<',
#            'gt': '>',
#            'amp': '&',
#            'nbsp': ' '
#            })
        self.tracking = {}

    def unknown_starttag(self, tag, attributes):
        """**handle start tags"""
        item = EntityContainer(tag, attributes)
        self.STACK[-1].append(item)
        self.STACK.append(item)
	if tag in trackingContainers:
	    self._add_track(tag, attributes)

    def unknown_endtag(self, tag):
        """**handle end tags"""
        self.STACK.pop()
	if tag in trackingContainers:
	    self._remove_track(tag)

    def _add_track(self, tag, attributes):
	if not self.tracking.has_key(tag):
	    self.tracking[tag] = []
        self.tracking[tag].append(attributes)

    def _remove_track(self, tag):
	if not self.tracking.has_key(tag):
	    raise AssertionError, "tracking has no value for %s" % tag
	l = self.tracking[tag]
        if not l:
	    raise AssertionError, "tracking list for %s is empty" % tag
        self.tracking[tag] = l[:-1]
        # if list is now empty, remove the entry
        if not self.tracking[tag]: del self.tracking[tag]

    def handle_data(self, data):
        """**handle textual data between open/close tags"""
        self.STACK[-1].addData(data)

    def syntax_error(self, message):
        if not self.tracking: 
            raise 'ParsingError', "error at line %d: %s" % (self.lineno, message)
        msg = 'in docstring '
        for k in trackingContainers:
            if self.tracking.get(k, None):
                msg = msg + "for %s %s: " % \
               (k, self.tracking[k][-1].get('name', 'unknown'))
        msg = msg + message
        raise 'ParsingError', msg

def parseString(text):
    '''**parse the contents of <code>text</code> and return the parse tree
    <p/>
    <b>NOTE:</b>you <b>can</b> concatenate the xml dumps of more than one run
    of <code>skdoc</code> and parse it.'''
    p = XMLParser()
    f = '<PYDOC>'+text+'</PYDOC>'
    try:
        p.feed(f)
    except RuntimeError, v:
        p.syntax_error(v)
    p.close()
    return p.STACK[0][0]


