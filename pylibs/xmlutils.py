# $Id$
# Time-stamp: <02/08/29 11:36:27 smulloni>

######################################################################## 
#  Copyright (C) 2001-2002 Jacob Smullyan <smulloni@smullyan.org>
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
########################################################################

"""
a pleasantly minimal XML-to-Python object translator.
XMLElement can also be used to build XML documents.
The parser requires expat, but XMLElement does not.
Based on the Java xml parser (org.skunk.minixml)
used for SkunkDAV (http://skunkdav.sf.net/).
"""

import types

try:
    import xml.parsers.expat as expat

    class ExpatParser:
        """
        takes an input xml string and produces a corresponding XMLElement (deposited in the 'document' attribute).
        Currently ignores comments, CDATA, processing instructions, etc.
        """
        def __init__(self, elementClassRegistry={}):
            self.__parser=expat.ParserCreate()
            self.__parser.StartElementHandler=self.start
            self.__parser.EndElementHandler=self.end
            self.__parser.CharacterDataHandler=self.data
            self.__stack=[]
            self.document=None
            self.elementClassRegistry=elementClassRegistry
            
        def start(self, tag, attrs):
            elem=makeElement(tag, self.elementClassRegistry)
            elem.OPEN=1
            if not self.document:
                self.document=elem
            for k, v in attrs.items():
                elem.setAttribute(k, v)
            self.__stack.append(elem)
            
        def data(self, data):
            self.__stack.append(data)
            
        def end(self, tag):
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
                
        def parse(self, data):
            self.__parser.Parse(data, 0)

    def parse(xmlstring):
        p=ExpatParser()
        p.parse(xmlstring)
        return p.document
    
except ImportError:
    pass
            
XMLNS_ATTR='xmlns'

def makeElement(fullElementName, elementClassRegistry={}):
    classFactory=elementClassRegistry.get(fullElementName, XMLElement)
    colonIndex=fullElementName.find(':')
    if colonIndex==-1:
        return classFactory(fullElementName)
    else:
        
        return classFactory(fullElementName[colonIndex+1:],
                            fullElementName[:colonIndex])

class XMLElement:
    def __init__(self,
                 name,
                 namespaceCode=None,
                 namespace=None,
                 empty=None,
                 html_compat=None):
        self.name=name
        self.namespaceCode=namespaceCode
        self.empty=empty
        self.html_compat=html_compat
        self.__children=[]
        self.__attributes={}
        self.__namespaces={}
        self.__defaultNamespace=''
        if namespace:
            if namespaceCode:
                self.setAttribute('%s:%s' % (XMLNS_ATTR, namespaceCode), namespace)
            else:
                self.setAttribute(XMLNS_ATTR, namespace)
        self.__parent=None

    def __str__(self):
        buff=['<']
        if self.namespaceCode:
            buff.append('%s:' % self.namespaceCode)
        buff.append(self.name)
        for attr, val in self.__attributes.items():
            buff.append(' %s="%s"' % (attr, val))
        if len(self.__children):
            buff.append('>')
            buff.extend(map(str, self.__children))
            buff.append('</')
            if (self.namespaceCode):
                buff.append('%s:' % self.namespaceCode)
            buff.append(self.name)
            buff.append('>')
        else:
            if self.html_compat:
                if self.empty:
                    buff.append(' />')
                else:
                    buff.append("></%s>" % self.name)
            else:
                buff.append('/>')
        return ''.join(buff)

    def hasAttribute(self, name):
        return self.__attributes.has_key(name)
            
    def getAttribute(self, name):
        if self.__attributes.has_key(name):
            return self.__attributes[name]
        raise KeyError, name

    def setAttribute(self, name, value):
        if name.startswith(XMLNS_ATTR):
            colindex=name.find(':')
            if colindex==-1:
                self.__defaultNamespace=value
            else:
                self.setNamespace(value, name[colindex+1:])
        self.__attributes[name]=value
        # for convenience
        return self

    def getChildren(self, suppressWhitespace=1):
        if suppressWhitespace:
            return filter(lambda x: type(x) not in (types.UnicodeType,
                                                    types.StringType) or x.strip(),
                          self.__children)
        else:
            return self.__children[:]

    def addChild(self, *children):
        for child in children:
            if isinstance(child, XMLElement):
                child.__parent=self
            self.__children.append(child)
        # for convenience
        return self

    def getChildrenByAttribute(self, attr, val, limit=1):
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
        self._private_getChildrenByAttribute(attr, f, limit, result)
        return result

    def _private_getChildrenByAttribute(self, attr, valfunc, limit, result):
        if self.hasAttribute(attr) and valfunc(self.getAttribute(attr)):
            result.append(self)
        if 0 < limit and limit <= len(result):
            return
        for child in self.getChildren():
            if isinstance(child, XMLElement):
                child._private_getChildrenByAttribute(attr, valfunc, limit, result)

    # aliases 
    addElement=addChild
    getElements=getChildren
    getElementsByAttribute=getChildrenByAttribute

    def getNamespace(self, namespaceCode=None):
        if not namespaceCode:
            namespaceCode=self.namespaceCode
        if not namespaceCode:
            return self.getDefaultNamespace()
        ns=self.__namespaces.get(namespaceCode)
        if not ns and self.__parent!=None:
            ns=self.__parent.getNamespace(namespaceCode)
        return ns

    def getDefaultNamespace(self):
        if (not self.__defaultNamespace) and self.__parent:
            return self.__parent.getDefaultNamespace()
        return self.__defaultNamespace

    def setDefaultNamespace(self, ns):
        self.__defaultNamespace=ns

    def setNamespace(self, namespace, namespaceCode):
        self.__namespaces[namespaceCode]=namespace
        self.namespaceCode=namespaceCode

    def getChild(self, name, namespace=None, index=0):
        i=-1
        for kid in self.__children:
            if kid.name==name and (namespace==None \
                                   or namespace==kid.getNamespace()):
                i+=1
                if i==index:
                    return kid
        return None

    

########################################################################
# $Log$
# Revision 1.5  2002/08/29 15:37:10  smulloni
# add/revised copyright notice and license
#
# Revision 1.4  2002/08/29 14:59:06  smulloni
# added xhtml parser and moved some code from ecs.xhtml to xmlutils.
#
# Revision 1.3  2002/08/28 20:55:27  smulloni
# some tweaks for xhtml compatibiity.
#
# Revision 1.2  2001/12/02 20:57:50  smulloni
# First fold of work done in September (!) on dev3_2 branch into trunk:
# vfs and PyDO enhancements (webdav still to come).  Also, small enhancement
# to templating's <:img:> tag.
#
# Revision 1.1.2.2  2001/10/16 03:27:15  smulloni
# merged HEAD (basically 3.1.1) into dev3_2
#
# Revision 1.1.2.1  2001/09/27 03:36:07  smulloni
# new pylibs, work on PyDO, code cleanup.
#
########################################################################
        
        

    
            
    
