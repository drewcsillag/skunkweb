# Time-stamp: <02/08/28 16:46:15 smulloni>
# $Id$

# a library similar in intent to HTMLGen or Java's ECS, but quite minimal.
# Should generate valid XHTML.

import xmlutils
import new
import keyword

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

    """
    an alias for addChild()
    """
    addElement=xmlutils.XMLElement.addChild

    def getElementsByAttribute(self, attr, val, limit=1):
        """
        returns a list of elements with an attribute with the name
        given by attr and a value V where, if val is not callable,
        V = val, or if val is callable, where val(V) is true.  limit
        is the maximum number of elements to return; if limit is < 1,
        all matching elements will be returned.
        """
        if callable(val):
            f=val
        else:
            f=lambda x, v=val: x==v
        result=[]
        self._private_getElementsByAttribute(attr, f, limit, result)
        return result
               

    def _private_getElementsByAttribute(self, attr, valfunc, limit, result):
        if self.hasAttribute(attr) and valfunc(self.getAttribute(attr)):
            result.append(self)
        if 0 < limit and limit <= len(result):
            return
        for child in self.getChildren():
            if isinstance(child, Element):
                child._private_getElementsByAttribute(attr, valfunc, limit, result)
        
                                  
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
                'i',
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

def _makeClass(elemName, empty):
        
    if keyword.iskeyword(elemName) or __builtins__.has_key(elemName):
        kname=elemName+'_'
    else:
        kname=elemName
    if empty:
        bases=(EmptyElement,)
    else:
        bases=(ContainerElement,)
    kl=new.classobj(kname, bases, {})
    kl.name=elemName
    globals()[kname]=kl
    __all__.append(kname)

for k in EMPTY_ELEMENTS:
    _makeClass(k, 1)
for k in CONTAINER_ELEMENTS:
    _makeClass(k, 0)

del _makeClass

                    
