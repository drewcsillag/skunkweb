######################################################################## 
#  Copyright (C) 2002 Jacob Smullyan <smulloni@smullyan.org>
#  
#      You may distribute under the terms of either the GNU General
#      Public License or the SkunkWeb License, as specified in the
#      README file.
########################################################################

"""
a simple tree class.
"""

from fieldcontainer import FieldContainer

class NodeNotFoundException(Exception): pass

class TreeNode(object):
    def __init__(self,
                 name,
                 children=None,
                 data=None):
        self.name=name
        self.__children=FieldContainer(children or [],
                                       fieldmapper=lambda x: x.name,
                                       storelists=0)
        self.parent=None
        self.data=None
        
    def _get_path(self):
        return '/'.join([x.name for x in self.pathitems()])

    path=property(_get_path)

    def _get_children(self):
        return self.__children[:]

    children=property(_get_children)

    def addChild(self, child):
        if child.name=='':
            raise ValueError, "name of child node cannot be an empty string"
        child.parent=self
        self.__children.append(child)

    def _get_root(self):
        if self.parent==None:
            return self
        return self.parent._get_root()

    root=property(_get_root)
    
    def resolvePath(self, path):
        vector=path.split('/')
        if path.startswith('/'):
            node=self._get_root()
            vector.pop(0)
        else:
            node=self
        for v in vector:
            try:
                node=node.children[v]
            except KeyError:
                raise NodeNotFoundException, path
        return node

    def createPath(self, path, *args, **kw):
        vector=path.split('/')
        if path.startswith('/'):
            node=self._get_root()
            vector.pop(0)
        else:
            node=self
        for v in vector:
            if node.children.has_key(v):
                node=node.children[v]
            else:
                n=self.__class__(v, *args, **kw)
                node.addChild(n)
                node=n
        return node
                
    def iterparents(self):
        return _parent_iterator(self)

    def pathitems(self):
        l=[x for x in self.iterparents()]
        l.reverse()
        return l + [self]

    def walk(self, visitfunc, state=None, filter=None):
        if filter is not None:
            if not filter(self):
                return
        visitfunc(self, state)
        for c in self._get_children():
            c.walk(visitfunc, state, filter)

class _parent_iterator(object):
    def __init__(self, node):
        self.node=node

    def next(self):
        if self.node.parent is None:
            raise StopIteration
        self.node=self.node.parent
        return self.node

    def __iter__(self):
        return self
    
