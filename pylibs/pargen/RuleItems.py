#  
#  Copyright (C) 2001 Andrew T. Csillag <drew_csillag@geocities.com>
#  
#      You may distribute under the terms of either the GNU General
#      Public License or the SkunkWeb License, as specified in the
#      README file.
#   
import sys
import string

class Set:
    def __init__(self, *items):
        self.set = {}
        for i in items:
            self.set[i] = 1

    def items(self):
        k = self.set.keys()
        k.sort()
        return k

    def add(self, *items):
        for i in items:
            try:
                self.set[i] = 1
            except TypeError:
                raise TypeError, 'value %s is not a valid set member' % i, \
                      sys.exc_traceback
                      

    def addList(self, itemList):
        try:
            for i in itemList:
                self.set[i] = 1
        except AttributeError:
            raise AttributeError, 'itemlist %s is not sequenceable' % itemList

    def addSet(self, set):
        self.set.update(set.set)
        
    def __len__(self):
        return len(self.set)

    def copy(self):
        return apply(Set, tuple(self.items()))

    def __cmp__(self, other):
        if other == None:
            return 1
        return cmp(self.set, other.set)

    def __repr__(self):
        return '<Set %s>' % repr(self.items())

    def contains(self, other):
        for i in other.items():
            if not self.set.has_key(i):
                return 0
        return 1

    def __sub__(self, s):
        a = self.items()
        a.remove(s)
        return apply(Set, tuple(a))

    def __getitem__(self, ind):
        return self.items()[ind]
    
class Rule:
    def __init__(self, lhs, rhs, ruleNumber, funcName = ''):
        self.ruleNumber = ruleNumber
        self.funcName = funcName
        self.lhs = lhs
        self.rhs = rhs

    def __repr__(self):
        return '<Rule #%d "%s -> %s" calls "%s">' % (self.ruleNumber,
                                                     self.lhs,
                                                     string.join(self.rhs),
                                                     self.funcName)

    def __str__(self):
        try:
            return '%s -> %s' % (self.lhs, string.join(self.rhs))
        except:
            raise 'CRAP', 'crap in rhs %s' % str((self.lhs, self.rhs))
    
    def getItem(self):
        return Item(self.lhs, self.rhs, 0, self.ruleNumber, self.funcName)
    
class Item:
    def __init__(self, lhs, rhs, dotPos, ruleNumber, funcName = '',
                 lookaheads = None):
        if lookaheads == None:
            lookaheads = Set()
        if type(rhs) != type([]):
            raise TypeError, 'rhs is not a list %s' % str(rhs)
        self.ruleNumber = ruleNumber
        self.funcName = funcName
        self.lhs = lhs
        self.rhs = rhs
        self.dotPos = dotPos
        self.lookaheads = lookaheads

    def __repr__(self):
        f = self.rhs[:]
        f.insert(self.dotPos, '.')
        if not len(self.lookaheads):
            return '<Item "%s -> %s" from rule #%s calls "%s">' % (
                self.lhs, string.join(f),
                self.ruleNumber, self.funcName)
        else:
            return '<Item "%s -> %s", %s from rule #%s calls "%s">' % (
                self.lhs, string.join(f), self.lookaheads.items(),
                self.ruleNumber, self.funcName)

    def __str__(self):
        f = self.rhs[:]
        f.insert(self.dotPos, '.')
        if not len(self.lookaheads):
            return '%s -> %s' % (self.lhs, string.join(f))
        else:
            return '%s -> %s \t,%s' % (
                self.lhs, string.join(f),
                string.join(map(str, self.lookaheads), ', '))

    def pointAtLeft(self):
        if self.dotPos == 0:
            return 1
        
    def pointAtEnd(self):
        if self.dotPos >= len(self.rhs):
            return 1

    def expects(self):
        try:
            return self.rhs[self.dotPos]
        except IndexError:
            return None

    def __cmp__(self, other):
        #if not hasattr(other, 'dotPos'):
        #    raise TypeError, 'other is %s!' % other
        if self.dotPos != other.dotPos:
            return cmp(self.dotPos, other.dotPos)
        elif self.lhs != other.lhs:
            return cmp(self.lhs, other.lhs)
        elif self.rhs != other.rhs:
            return cmp(self.rhs, other.rhs)
        elif self.ruleNumber != other.ruleNumber:
            return cmp(self.ruleNumber, other.ruleNumber)
        return 0

    def fullCmp(self, other):
        #if not hasattr(other, 'dotPos'):
        #    raise TypeError, 'other is %s!' % other
        if self.dotPos != other.dotPos:
            return cmp(self.dotPos, other.dotPos)
        elif self.lhs != other.lhs:
            return cmp(self.lhs, other.lhs)
        elif self.rhs != other.rhs:
            return cmp(self.rhs, other.rhs)
        elif self.ruleNumber != other.ruleNumber:
            return cmp(self.ruleNumber, other.ruleNumber)
        elif self.lookaheads != other.lookaheads:
            return cmp(self.lookaheads, other.lookaheads)
        
    def newAdvancedDot(self):
        return Item(self.lhs, self.rhs, self.dotPos + 1, self.ruleNumber,
                    self.funcName, self.lookaheads.copy())
    
if __name__ == '__main__':
    a = Rule('S', ['Foo', 'bar', 'baz'], 1, 'foo')
    print a
    i = a.getItem()
    print i
    a = Rule('S', [], 3, 'starter')
    print a 
    print a.getItem()
