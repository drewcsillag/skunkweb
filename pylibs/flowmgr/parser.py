# Time-stamp: <02/09/03 16:39:04 smulloni>
# $Id$

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

class _flowelement(XMLElement):
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
        # TO BE DONE
        pass
        

class _flow(_node):
    name="flow"

class _cond(_node):
    name="cond"

class _field(_flowelement):
    name="field"

class _expr(_flowelement):
    name="expr"


class FlowDef:
    def __init__(self, flows=[], stages=[], fields=[]):
        self.flows=flows
        self.stages=stages        
        self.fields=fields


class Node:
    def evaluate(self):
        return self

class Flow(Node):
    def __init__(self, id=None, nodes=[]):
        self.id=id
        self.nodes=nodes

    def evaluate(self):
        if self.nodes and len(self.nodes)>0:
            n=self.nodes[0]
        if self==n or not isinstance(n, Node):
            # a circular flow is permitted
            return n
        return n.evaluate()

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

    def evaluate(self):
        if self.expr:
            n=self.if_node
        else:
            n=self.else_node
        if n==self:
            raise CircularityError, "circular cond!"
        if isinstance(n, Node):
            return n.evaluate()
        else:
            return n

class ExprTypeNotSupported(Exception): pass
class CircularityError(Exception): pass

class Expr:
    def __init__(self, data, type="pyeval", id=None):
        self.data=data
        self.type=type
        self.id=id

    def __nonzero__(self):
        if EXPR_TYPE_MAP.has_key(self.type):
            return EXPR_TYPE_MAP[self.type](self.data)
        else:
            raise ExprTypeNotSupported, self.type
        
EXPR_TYPE_MAP={'pyeval' : eval} # will probably do something a little different here eventually  
        
class Field:
    def __init__(self, name, data, id=None):
        self.name=name
        self.data=data
        self.id=id


f hasattr(xmlutils, 'ExpatParser'):
    elementClassRegistry={'flowdef' : _flowdef,
                          'stage' : _stage,
                          'flow' : _flow,
                          'cond' : _cond,
                          'field' : _field,
                          'expr' : _expr}
    class FlowDefParser(xmlutils.ExpatParser):
        def __init__(self):
            xmlutils.ExpatParser.__init__(self, elementClassRegistry)

        


                            


