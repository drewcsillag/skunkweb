# Time-stamp: <2003-12-27 23:18:32 smulloni>

######################################################################## 
#  Copyright (C) 2002 Jacob Smullyan <smulloni@smullyan.org>
#  
#      You may distribute under the terms of either the GNU General
#      Public License or the SkunkWeb License, as specified in the
#      README file.
########################################################################


# a library similar in intent to HTMLGen or Java's ECS, but quite minimal.
# Should generate valid XHTML.

import xmlutils
import new

class Element(xmlutils.XMLElement):
    """
    abstract base class for xhtml elements.
    """
    
    name=None
    empty=None

    def __init__(self, attributes=None):
        xmlutils.XMLElement.__init__(self,
                                     self.name,
                                     html_compat=1,
                                     empty=self.empty)
        if attributes:
            for k, v in attributes.items():
                self.setAttribute(k, v)          

                                  
    def getElementById(self, id):
        """
        equivalent to the DOM method.
        """
        if self.hasAttribute('id') and self.getAttribute('id')==id:
            return self
        for child in self.getChildren():
            if isinstance(child, Element):
                e=child.getElementById(id)
                if e:
                    return e


class EmptyElement(Element):
    """
    abstract base class for empty xhtml elements.
    """
    
    empty=1


class ContainerElement(Element):
    """
    abstract base class for non-empty xhtml elements.
    """
    
    empty=0

    def __init__(self, text=None, children=[], attributes=None):
        Element.__init__(self, attributes)
        if text is not None:
            self.addChild(text)
        if children:
            self.addChild(*children)


EMPTY_ELEMENTS=['area',
                'base',
                'br',
                'frame',
                'hr',
                'img',
                'input',
                'isindex',
                'link',
                'meta',
                'param',
                ]
CONTAINER_ELEMENTS=['a',
                    'abbr',
                    'acronym',
                    'address',
                    'applet',
                    'basefont',
                    'b',
                    'bdo',
                    'big',
                    'blockquote',
                    'body',
                    'button',
                    'caption',
                    'center',
                    'cite',
                    'code',
                    'col',
                    'colgroup',
                    'dd',
                    'del',
                    'dfn',
                    'dir',
                    'div',
                    'dl',
                    'dt',
                    'em',
                    'fieldset',
                    'font',
                    'form',
                    'frameset',
                    'head',
                    'h1',
                    'h2',
                    'h3',
                    'h4',
                    'h5',
                    'h6',
                    'html',
                    'i',
                    'iframe',
                    'ins',
                    'kbd',
                    'label',
                    'legend',
                    'li',
                    'list',
                    'map',
                    'menu',
                    'noframes',
                    'noscript',
                    'object',
                    'ol',
                    'optgroup',
                    'option',
                    'p',
                    'pre',
                    'q',
                    'samp',
                    'script',
                    'select',
                    'small',
                    'span',
                    'strike',
                    'strong',
                    'style',
                    'sub',
                    'sup',
                    'table',
                    'tbody',
                    'td',
                    'textarea',
                    'tfoot',
                    'th',
                    'thead',
                    'title',
                    'tr',
                    'tt',
                    'ul',
                    'var'
                    ]

__all__=[]

elementClassRegistry={}

def _makeClass(elemName, empty):
    kname=elemName.capitalize()
    if empty:
        bases=(EmptyElement,)
    else:
        bases=(ContainerElement,)
    kl=new.classobj(kname, bases, {})
    kl.name=elemName
    globals()[kname]=kl
    elementClassRegistry[elemName]=lambda x, y=None, k=kl: k()
    __all__.append(kname)

for k in EMPTY_ELEMENTS:
    _makeClass(k, 1)
for k in CONTAINER_ELEMENTS:
    _makeClass(k, 0)

del _makeClass


import HTMLParser as _h
from xmlutils import makeElement, XMLElement

class XHTMLParser(_h.HTMLParser):
    def __init__(self):
        _h.HTMLParser.__init__(self)
        self.__stack=[]
        self.document=None
        self.elementClassRegistry=elementClassRegistry
  
    def handle_starttag(self, tag, attrs):
        elem=makeElement(tag, self.elementClassRegistry)
        elem.OPEN=1
        if not self.document:
            self.document=elem
        for k, v in attrs:
            elem.setAttribute(k, v)
        self.__stack.append(elem)

    def handle_data(self, data):
        self.__stack.append(data)

    def handle_entityref(self, ref):
        self.__stack.append('&%s;' % ref)

    def handle_endtag(self, tag):
        # find matching tag
        i=-1
        stackLen=len(self.__stack)
        while stackLen+i >= 0:
            p=self.__stack[i]
            if isinstance(p, XMLElement) and hasattr(p, 'OPEN'):
                # found element
                postind=stackLen+i+1
                popped=self.__stack[postind:]
                map (lambda x, y=p: y.addChild(x), popped)
                delattr(p, 'OPEN')
                self.__stack=self.__stack[:postind]
                break
            else:
                i-=1


def parse(xhtmlstring):
    p=XHTMLParser()
    p.feed(xhtmlstring)
    p.close()
    return p.document

__all__ . append(parse.__name__)

## if hasattr(xmlutils, 'ExpatParser'):
##     class XHTMLParser(xmlutils.ExpatParser):
##         def __init__(self):
##             xmlutils.ExpatParser.__init__(self, elementClassRegistry)

##     def parse(xhtmlstring):
##         p=XHTMLParser()
##         p.parse(xhtmlstring)
##         return p.document

##     __all__.append(parse.__name__)
                    

