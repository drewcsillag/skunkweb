# Time-stamp: <02/09/04 15:01:07 smulloni>
# $Id: parser.py,v 1.1 2002/09/03 20:40:36 smulloni Exp $

####################################################################### 
#  Copyright (C) 2002 Jacob Smullyan <smulloni@smullyan.org>
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

import xmlutils
import sys
import types

def WARN(txt):
    print >> sys.stderr, txt

class _flowelement(xmlutils.XMLElement):
    """
    abstract base class for flowdef elements.
    """
    def __init__(self):
        xmlutils.XMLElement.__init__(self, self.name)

    def _getId(self):
        if self.hasAttribute('id'):
            return self.getAttribute('id')
        return None

    def __getattr__(self, k):
        if k=='delegate':
            self.delegate=self._create_delegate()
            return self.delegate
        raise AttributeError, k

    def _getElementById(self, id_, type=None):
        primo=self.getPrimogenitor()
        possible=primo.getChildrenByAttribute('id', id_)
        if not possible:
            return None
        if type is not None and possible[0].name!=type:
            raise InvalidFlowDefException, \
                      "type mismatch: expected %s, got %s" % (type, possible[0].name)
        return possible[0]

    def _resolveIdRef(self):
        idref=self.attributes.get('idref')
        if idref is not None:
            e=self._getElementById(idref, self.name)
            if not e:
                raise InvalidFlowDefException, "dangling idref: %s" % idref
            return e

class _flowdef(_flowelement):
    name='flowdef'

    def _create_delegate(self):
        f=FlowDef()
        for k in self.getChildren():
            n=k.name
            if n=='flow':
                f.flows.append(k.delegate)
            elif n=='stage':
                f.stages.append(k.delegate)
            elif n=='field':
                f.fields.append(k.delegate)
        return f
            

class _node(_flowelement):
    pass

class _stage(_node):
    name="stage"

    def _create_delegate(self):
        ref=self._resolveIdRef()
        if ref is not None:
            return ref.delegate
        
        id_=self._getId()
        # should be all children, actually
        fields=[k.delegate for k in self.getChildren() if k.name=='field']
        inherits=self.attributes.get('inherits', '').split()
        base_stages_elems=filter(lambda x: x is not None and isinstance(x, Stage),
                           [self._getElementById(x) for x in inherits])
        return Stage(id_, fields, [x.delegate for x in base_stages_elems])

class _flow(_node):
    name="flow"

    def _create_delegate(self):
        ref=self._resolveIdRef()
        if ref is not None:
            return ref.delegate
        id_=self._getId()
        nodes=[]
        for k in self.getChildren():
            if k.name in ('stage', 'flow', 'cond'):
                nodes.append(k.delegate)
            else:
                WARN("weird element type in flow: %s" % k.name)
        return Flow(id_, nodes)
    

class _cond(_node):
    name="cond"

    def _create_delegate(self):
        ref=self._resolveIdRef()
        if ref is not None:
            return ref.delegate
        children=self.getChildren()
        lch=len(children)
        id_=self._getId()
        if lch==2:
            expr, if_node=children
            else_node=None
        elif lch==3:
            expr, if_node, else_node=children
        else:
            raise InvalidFlowDefException, "wrong number of children for cond"
        if expr.name!='expr' \
           or if_node.name not in ('stage', 'flow', 'cond') \
           or (else_node is not None and else_node.name not in ('stage', 'flow', 'cond')):
            raise InvalidFlowDefException, "wrong types of children for cond"
        if else_node:
            return Cond(expr.delegate, if_node.delegate, else_node.delegate, id_)
        else:
            return Cond(expr.delegate, if_node.delegate, id=id_)


class _field(_flowelement):
    name="field"

    def _create_delegate(self):
        ref=self._resolveIdRef()
        if ref is not None:
            return ref.delegate
        id_=self._getId()
        data=self.getChildren()
        return Field(fieldname, data, id_)


class _expr(_flowelement):
    name="expr"

    def _create_delegate(self):
        ref=self._resolveIdRef()
        if ref is not None:
            return ref.delegate
        id_=self._getId()
        type=self.attributes.get('type', 'pyeval')
        data=self.getChildren()
        return Expr(data, type, id_)

class FlowDef:
    def __init__(self, flows=[], stages=[], fields=[]):
        self.flows=flows
        self.stages=stages        
        self.fields=fields

STAGE_MARKER='last'

class Node:
    def evaluate(self, state={}):
        return self

class Flow(Node):
    def __init__(self, id=None, nodes=[]):
        self.id=id
        self.nodes=nodes

    def evaluate(self, state={}):
        if not self.nodes:
            return None
        last=state.get(STAGE_MARKER)
        if last:
            found=None
            for n in self.nodes:
                if found:
                    return n.evaluate(state)
                if n.id==last:
                    found=1
            return None

        n=self.nodes[0]
        if self==n or not isinstance(n, Node):
            # a circular flow is permitted
            return n
        else:
            return n.evaluate(state)

class Stage(Node):
    def __init__(self, id=None, fields=[], base_stages=[]):
        self.id=id
        self.fields=fields
        self.base_stages=base_stages
        for b in base_stages:
            for f in b.fields:
                if f not in self.fields:
                    self.fields.append(f)

class Cond(Node):
    def __init__(self, expr, if_node, else_node=None, id=None):
        self.expr=expr
        self.if_node=if_node
        self.else_node=else_node
        self.id=id

    def evaluate(self, state={}):
        if self.expr(state):
            n=self.if_node
        else:
            n=self.else_node
        if n==self:
            raise CircularityError, "circular cond!"
        if isinstance(n, Node):
            return n.evaluate(state)
        else:
            return n

class ExprTypeNotSupported(Exception): pass
class CircularityError(Exception): pass
class InvalidFlowDefException(Exception): pass

class Expr:
    def __init__(self, data, type_="pyeval", id=None):
        if type(data) == types.ListType:
            self.data=''.join(data)
        else:
            self.data=data
        self.type=type_
        self.id=id

    def __call__(self, state={}):
        if EXPR_TYPE_MAP.has_key(self.type):
            return EXPR_TYPE_MAP[self.type](self.data, state)
        else:
            raise ExprTypeNotSupported, self.type
        
EXPR_TYPE_MAP={'pyeval' : lambda x, s: eval(x, {}, s)} 
        
class Field:
    def __init__(self, fieldname, data, id=None):
        self.fieldname=fieldname
        self.data=data
        self.id=id


if hasattr(xmlutils, 'ExpatParser'):
    wrap=lambda x: lambda a, b=None: x()
    elementClassRegistry={'flowdef' : wrap(_flowdef),
                          'stage' : wrap(_stage),
                          'flow' : wrap(_flow),
                          'cond' : wrap(_cond),
                          'field' : wrap(_field),
                          'expr' : wrap(_expr)}
    
    class FlowDefParser(xmlutils.ExpatParser):
        
        def __init__(self):
            xmlutils.ExpatParser.__init__(self, elementClassRegistry)

        def getFlowDef(self):
            if self.document is not None:
                return self.document.delegate
        


                            


