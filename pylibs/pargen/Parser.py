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
"""Really the only user-usable module in the pargen area.  Contains
the actual interface to run the parser.  Also provides a useful
ListTokenSource object so if you just have a list of tokens,
you're all set.  Also provides a generic token object Token"""

from CONSTANTS import *
class _Stack:
    def __init__(self):
        self.s=[]

    def push(self, item):
        self.s.insert(0, item)

    def pop(self):
        x=self.s[0]
        self.s=self.s[1:]
        return x

    def peek(self):
        return self.s[0]

    def isempty(self):
        return len(self.s) == 0

class Token:
    """a pretty generic token class"""
    def __init__(self, toktype, tokval = None):
        self.toktype = toktype
        self.tokval = tokval

    def  __repr__(self):
        return '<Token type=%s, val=%s>' % (self.toktype, self.tokval)

class ListTokenSource:
    """give it a list of tokens, and you can pass it to Parse.
    """
    def __init__(self, toklist, verbose = 0):
        self.toklist=toklist
        self.ind=0
        self.verbose = verbose
        
    def getToken(self):
        """called by the parser to get the next token"""
        if self.ind == len(self.toklist):
            if self.verbose: print 'returning $'
            return Token('$')
        ret=self.toklist[self.ind]
        self.ind=self.ind+1
        if self.verbose:
            print 'returning', ret
        return ret

class ParseTree:
    """if you don't provide a callback object to the parser, it
    uses an instance of me (ParseTree).  Any more rhymes?
    """
    def __getattr__(self, item):
        self.itemname=item
        return self.action

    def action(self, lhs, *args):
        """the reduction action for everything"""
        return (self.itemname, lhs, args)

class EBNFCallBackBase:
    """If you were brave enough to use an EBNF grammar as input,
    your callback class should derive from me or it probably won't work
    since there are "hidden" rules created from the grammar to do some
    of the ugly work.
    """
    def _STARRECUR(self, x, newItem, itemTuple):
        return (newItem,) + itemTuple
    
    def _STARANCHOR(self, x):
        return ()

    def _PLUSRECUR(self, x, newItem, itemTuple):
        return (newItem,) + itemTuple
    
    def _PLUSANCHOR(self, x, newItem):
        return (newItem,)
    
    def _OPTEXISTS(self, x, *args):
        return args
    
    def _OPTMISSING(self, x):
        return ()
    
    def _ALTPASS(self, x, item):
        return item
    
    def _PARENPASS(self, x, *args):
        return args
    
def _parse(states, gotos, tokenSource, rules, terminals,
          callbackInstance = None, debug = None):
    tokens = tokenSource
    if callbackInstance == None:
        callbackInstance = ParseTree()
    stack = _Stack()
    stack.push(0)

    tok = tokens.getToken()
    while 1:
        state = stack.peek()
        if debug:
            print 'state', state
            print 'token', tok
        try:
            action = states[state][tok.toktype]
        except KeyError:
            validTerminals = []
            for i in states[state].keys():
                if i in terminals:
                    validTerminals.append(i)
            raise 'ParserException', 'expecting one of %s, got %s' % (
                validTerminals, tok)
        
        if action[0] == SHIFT:
            if debug:
                print 'shifting', tok, 'and', action[1]
            stack.push(tok)
            stack.push(action[1])
            tok = tokens.getToken()
            
        elif action[0] == REDUCE:
            if debug:
                print 'reducing on', tok
            r = rules[action[1]]
            if debug:
                print 'reducing', r['ruleString']

            parseItems = []
            #for i in range(len(r.rhs)):
            for i in range(r['lenrhs']):
                stack.pop() #state
                parseItems.insert(0, stack.pop()) # item (token possibly)

            s = stack.peek() #get s'
            if debug:
                choices = gotos[s].keys()
                if r['lhs'] not in choices:
                    print 'Cannot go to %s?!?! choices were %s' % (
                        r['lhs'], choices)
                print 'going to state %s s=%s' % (gotos[s][r['lhs']], s)

            #if not r.funcName:
            if not r['funcName']:
                funcName = r['lhs']
                #funcName = r.lhs
            else:
                #funcName = r.funcName
                funcName = r['funcName']

            method = getattr(callbackInstance, funcName)
            if debug:
                print 'calling method %s with args %s' % (
                    method, (r['lhs'],)+tuple(parseItems))
            #print method
            ret = apply(method, (r['lhs'],)+tuple(parseItems))
            
            stack.push(ret)
            #stack.push(gotos[s][r.lhs])
            stack.push(gotos[s][r['lhs']])

        elif action[0] == ACCEPT:
            if debug:
                print 'accepting'
            return stack.s[1]

        else:
            raise 'ParserError', action

def Parse(tableObj, tokenSource, callbackInstance = None, debug = None):
    """given the parse table in tableObj which can
    be either a module or a dictionary, a source of tokens in
    tokenSource that has a getToken method that takes
    no arguments a returns an object that has a string attribute
    toktype and an unconstrained attribute tokval,
    attempts to parse the token stream.
    
    The callbackInstance parameter is used to do the reductions.
    The first item on the lines on the grammar input file is the name of a
    method that we fetch out of this instance to handle the reduction.
    If the debug parameter is set to some true value, the
    output gets verbose and shows the states that the parser traverses.
    """
    if type(tableObj) != type({}):
        tableObj = tableObj.__dict__
        
    states = tableObj['states']
    gotos = tableObj['gotos']
    terminals = tableObj['terminals']
    rules = tableObj['rules']
    
    return _parse(states, gotos, tokenSource, rules, terminals,
                 callbackInstance, debug)
