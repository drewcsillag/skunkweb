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
from CONSTANTS import *
import RuleItems
Set = RuleItems.Set

startItem = RuleItems.Item("S'", ['S'], 0, -1, None, Set('$'))

#def FIRST(symbol, ruleSet, terminals, recurSymbols = []):
#    """compute the set of terminals that begin strings derived from <symbol>
#    internal version that works with dicts"""
#    # if it's a terminal, duh, just return a set of self
#    if symbol in terminals:
#        return [symbol]
#
#    # did we recursively hit ourselves, if so, just return empty
#    if symbol in recurSymbols:
#        return []
#
#    symbols = Set()
#
#    productions = getProductions(ruleSet, symbol)
#    for rule in productions:
#        if not len(rule.rhs): #rhs is Epsilon
#            symbols.add(None)
#        else:
#            #print 'symbol is:', symbol
#            #print 'recursymbols is:', recurSymbols
#            #print 'new symbol is:', rule.rhs[0]
#            f = FIRST(rule.rhs[0], ruleSet, terminals, [symbol] + recurSymbols)
#            symbols.addList(f)
#    #if symbols.contains(Set(None)):
#    #    symbols = symbols - None
#    #    symbols.add('$')
#    return symbols.items()


#def FIRSTBase(symbol, ruleSet, terminals, recurSymbols = []):
#    """compute the set of terminals that begin strings derived from <symbol>
#    internal version that works with dicts"""
#    # if it's a terminal, duh, just return a set of self
#    if symbol in terminals:
#        return [symbol]
#
#    # did we recursively hit ourselves, if so, just return empty
#    if symbol in recurSymbols:
#        return []
#
#    symbols = Set()
#
#    productions = getProductions(ruleSet, symbol)
#    for rule in productions:
#        if not len(rule.rhs): #rhs is Epsilon
#            symbols.add(None)
#        else:
#            #print 'symbol is:', symbol
#            #print 'recursymbols is:', recurSymbols
#            #print 'new symbol is:', rule.rhs[0]
#            f = FIRSTBase(rule.rhs[0], ruleSet, terminals, [symbol] + recurSymbols)
#            symbols.addList(f)
#    #if symbols.contains(Set(None)):
#    #    symbols = symbols - None
#    #    symbols.add('$')
#    return symbols.items()
#
#def FIRST(X, ruleSet, terminals):
#    symbols = [X]
#    firsts = Set(None)
#
#    while 1:
#        #print 'symbols =', symbols, 'firsts=', firsts
#        oldFirsts = firsts
#        
#        #remove None from firsts
#        firsts = firsts - None
#
#        #add FIRSTBase to firsts
#        for symbol in symbols:
#            firsts.addList(FIRSTBase(symbol, ruleSet, terminals))
#
#        if firsts == oldFirsts:
#            break
#        
#        if not firsts.contains(Set(None)):
#            break
#                           
#        #find symbols Y where A -> alpha X Y Beta
#        #symbols = []
#        for rule in ruleSet:
#            if X in rule.rhs:
#                for ind in range(len(rule.rhs)):
#                    #print 'found rule with %s in it' % X, rule
#                    #if there is something after X
#                    if rule.rhs[ind] == X and (ind + 1) < len(rule.rhs):
#                        newSymbol = rule.rhs[ind + 1]
#                        if newSymbol not in symbols:
#                            #print 'adding', rule.rhs[ind+1]
#                            symbols.append(rule.rhs[ind+1])
#
#    #if firsts.contains(Set(None)):
#    #    firsts = firsts - None
#    #    firsts.add('$')
#    return firsts.items()
#
#
#def FIRSTS(symbols, symbolSet, ruleSet, terminals):
#    if symbols:
#        f = FIRST(symbols[0], ruleSet, terminals)
#        return f
#    else:
#        return symbolSet
#def FIRSTS(symbols, symbolSet, ruleSet, terminals):
#    firsts = Set()
#    ind = 0
#    while ind < len(symbols):
#        X = symbols[ind]
#        ind = ind + 1
#        if ind == len(symbols):
#            break
#        firsts.addList(FIRST(X, ruleSet, terminals))
#        if not firsts.contains(Set(None)):
#            break
#        firsts = firsts - None
#    if firsts.contains(Set(None)) or not firsts.items(): #index blew out first
#        #firsts = firsts - None
#        firsts.addList(symbolSet)
#
#    return firsts.items()



def FIRST(symbols, ruleSet, terminals, recurSymbols = None):
    if recurSymbols is None:
        recurSymbols = []
    if type(symbols) not in (type(()), type([])):
        symbols = [symbols]

    first = Set()

    addNone = 0
    #print 'symbols is', symbols
    #from pg 189
    for X in symbols:
        #print 'X is', X
        #if we're already doing X, just continue
        if X in recurSymbols:
            #print 'already in me'
            continue
        #if X is terminal, then FIRST(X) is {X}
        if X in terminals:
            #print 'X (%s) is terminal' % X
            first.add(X)
            break
        prods = getProductions(ruleSet, X)
        for rule in prods:
            #if X -> Epsilon then add Epsilon (None for us) to FIRST(X)
            if len(rule.rhs) == 0:
                #print 'rule "%s" .rhs is NULL' % rule
                addNone = 1
                first.add(None)

            else: #if X -> Y1Y2... then add FIRST(Y1Y2Y3) to FIRST(X)
                #print 'rule %s, doing FIRST(%s)' % (rule, rule.rhs)
                first.addList(FIRST(rule.rhs, ruleSet, terminals,
                                    recurSymbols + [X]))
            
        if not first.contains(Set(None)):
            #print 'firsts is', first
            break

    if addNone:
        first.add(None)
    return first.items()

def FIRSTS(symbols, symbolSet, ruleSet, terminals):
    myExtraRules = []
    for X in symbolSet:
        myExtraRules.append(
            RuleItems.Rule('$BOGO$', [X], -2))
    r = FIRST(symbols, ruleSet + myExtraRules, terminals)
    if None in r or len(r) == 0:
    #if len(r) == 0:
        r.extend(symbolSet)
    if None in r:
        r.remove(None)
    return r

def FOLLOW(lookie, ruleSet, terminals, nonTerminals):
    symbols = terminals + nonTerminals
    fset = {}
    for i in symbols:
        fset[i] = {}

    fset['S']['$'] = 1
    
    for X in symbols:
        firsts = []
        for rule in ruleSet:
            if X in rule.rhs:
                for j in range(len(rule.rhs)):
                    if j + 1 < len(rule.rhs) and rule.rhs[j] == X:
                        firsts.extend(FIRST(rule.rhs[j+1], ruleSet, terminals))
        for i in firsts:
            if i != None: fset[X][i] = 1

    added = 1
    while added:
        added = 0
        for rule in ruleSet:
            if len(rule.rhs):
                B = rule.rhs[-1]
                A = rule.lhs
                id = fset[B].copy()
                fset[B].update(fset[A])
                if fset[B] != id:
                    added = 1

            if len(rule.rhs) >= 2:
                for i in range(-1, -len(rule.rhs), -1):
                    if None not in FIRST(rule.rhs[i], ruleSet, terminals):
                        B = rule.rhs[i]
                        A = rule.lhs
                        id = fset[B].copy()
                        fset[B].update(fset[A])
                        if fset[B] != id:
                            added = 1
                        
                    
    #for k in fset.keys():
    #    print '%s: %s' % (k, fset[k].keys())
    return fset[lookie].keys()

                
def siftTokens(ruleSet):
    """Sifts through <ruleSet> and returns three things:
        1) the terminals
        2) the non-terminals
    """
    terminals = {'$':1}
    nonTerminals = {}

    for rule in ruleSet:
        nonTerminals[rule.lhs] = 1 #lhs is obviously a non-terminal
        for token in rule.rhs:
            terminals[token] = 1   #for now, we'll kill the nt's below

    #remove the known non-terminals from the terminals dict
    for token in nonTerminals.keys():
        if terminals.has_key(token): 
            del terminals[token]

    return terminals.keys(), nonTerminals.keys()

def getProductions(ruleSet, nonTerminal):
    """return all rules in <ruleSet> with <nonTerminal> as the lhs"""
    return filter(lambda x, nt = nonTerminal: x.lhs == nt, ruleSet)

def printItems(legend, items):
    print legend
    for i in range(len(items)):
        print 'state %d' % i
        for j in items[i]:
            print '        ', j

def printStateTable(newRules, t, nt, sd, gd):
    #t = t + ['$']

    print '   ', 'action',(' '*((len(t)-1)*6))+'      goto'

    print '   ',
    for s in t:
        print '%5s' % repr(s),
    print '    ',
    for s in nt:
        print '%3s' % s,
    print
    
    for i in range(len(newRules)):
        print '%3s' % i,
        for s in t:
            if sd[i].has_key(s):
                if sd[i][s][0] == SHIFT:
                    print '%5s' % ('s%d' % sd[i][s][1]),
                elif sd[i][s][0] == REDUCE:
                    print '%5s' % ('r%d' % sd[i][s][1]),
                else:
                    print '%5s' % 'acc',
            else:
                print '%5s' % ' ',

        print '    ',
        for s in nt:
            if gd[i].has_key(s):
                print '%3s' % gd[i][s],
            else:
                print '%3s' % ' ',
        print

def digestRules(ruleSet):
    """reduces the rules in ruleset to a form that
    1) is marshallable
    2) is literable
    and
    3) is only what the parser actually needs (well mostly)
    """
    nr = []
    for rule in ruleSet:
        nr.append({
            'funcName': rule.funcName,
            'lhs': rule.lhs,
            'lenrhs': len(rule.rhs),
            'ruleString': str(rule)
            })
    return nr
