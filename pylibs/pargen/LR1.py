#  
#  Copyright (C) 2001 Andrew T. Csillag <drew_csillag@geocities.com>
#  
#      You may distribute under the terms of either the GNU General
#      Public License or the SkunkWeb License, as specified in the
#      README file.
#   
"""LR1 methods to compute a parse table for a grammar"""
from CONSTANTS import *
import string
import copy
from Common import *

def closure(items, ruleSet, terminals):
    """compute the LR1 closure of items"""
    I = copy.deepcopy(items)

    added = 1
    while added:
        added = 0

        #for each item [A -> alpha . B Beta, a] in I (result)
        for item in I:
            if item.pointAtEnd(): continue
            A = item.lhs
            alpha = item.rhs[:item.dotPos]
            B = item.rhs[item.dotPos]
            Beta = item.rhs[item.dotPos + 1:]
            a = item.lookaheads

            #for each production B -> gamma in G'
            for prod in getProductions(ruleSet, B):
                #and each terminal b in FIRST(Beta a)
                b = FIRSTS(Beta, a.items(), ruleSet, terminals)
                newItem = prod.getItem()
                newItem.lookaheads.addList(b)
                #such that [B -> . gamma, b] not in I
                if newItem not in I:
                    #add [B -> . gamma, b] to I
                    I.append(newItem)
                    added = 1 
                else: #newItem is in I, but are the lookaheads all there?
                    i = I.index(newItem)
                    #if they aren't add them and say we've added something
                    if (newItem.lookaheads != I[i].lookaheads
                        and not I[i].lookaheads.contains(newItem.lookaheads)):
                        added = 1
                        I[i].lookaheads.addSet(newItem.lookaheads)
    return I

def goto(I, X, ruleSet, terminals):
    """compute goto(I, X) LR1'ly """
    J = []
    for item in I:
        if not item.pointAtEnd() and item.expects() == X:
            J.append(item.newAdvancedDot())
    return closure(J, ruleSet, terminals)
        
def items(ruleSet, terminals, nonTerminals):
    """compute the LR1 items for <ruleSet>"""
    symbols = nonTerminals + terminals
    #start with closure of [ [S' -> S, $] ]
    C = [closure([startItem], ruleSet, terminals)]
    added = 1
    while added:
        added = 0
        for I in C:
            for X in symbols:
                g = goto(I, X, ruleSet, terminals)
                if g and not fullIn(C, g):# not in C:
                    C.append(g)
                    added = 1
    return C

def fullIn(C, g):
    """In operation, but since normal __cmp__ for items ignores the
    lookaheads (since normally we don't care), this one checks the
    lookaheads.
    """
    for set in C:
        if not fullCmpSets(set, g):
            return 1

def fullIndex(C, targetSet):
    """find targetSet in C"""
    for i in range(len(C)):
        if not fullCmpSets(C[i], targetSet):
            return i
    raise 'OhShit', "couldn't find %s\n%s" % (targetSet, C[4])

def fullCmpSets(s1, s2):
    """fully compare s1 and s2"""
    if len(s1) != len(s2):
        return 1
    for s1i, s2i in map(None, s1, s2):
        f = s1i.fullCmp(s2i)
        if f:
            return f
        
def generateStateTable(C, ruleSet, terminals, indexFunc):
    """Generate an LR(1) state table"""
    #initialize the state dictionary
    stateDict = {}
    for i in range(len(C)):
        stateDict[i] = {}

    gotoDict = {}
    for i in range(len(C)):
        gotoDict[i] = {}
    
    #compute the states
    for state in range(len(C)):
        for item in C[state]:
            exp = item.expects()
            targetSet = goto(C[state], exp, ruleSet, terminals)

            #check for conflicts
            #if there is a goto, shift
            if targetSet:
                #targetState = C.index(targetSet)
                #targetState = fullIndex(C, targetSet)
                targetState = indexFunc(targetSet)
                if stateDict[state].has_key(exp):
                    x = stateDict[state][exp]
                    if x[0] == SHIFT and x[1] != targetState:
                        print 'shift/shift conflict! for %s' % item
                        print 'favoring this on %s' % exp
                    if x[0] == REDUCE:
                        print ('shift/reduce conflict for %s, was reducing '\
                              'by %s, now shifting on %s') % (
                                  item, str(ruleSet[x[1]]), exp)
                stateDict[state][exp] = (SHIFT, targetState)

            #else if point is at the end and lhs isn't S', reduce
            elif item.pointAtEnd() and item.lhs != "S'":
                for i in item.lookaheads:
                    if stateDict[state].has_key(i):
                        x = stateDict[state][i]
                        if x[0] == SHIFT:
                            print ('shift/reduce conflict for %s, was '
                                   'shifting, will not reduce') % item
                        if x[0] == REDUCE:
                            print 'reduce/reduce conflict for %s' % item
                            thisRule = ruleSet[item.ruleNumber]
                            thatRule = ruleSet[x[1]]
                            if len(thisRule.rhs) > len(thatRule.rhs):
                                print 'favoring redux by %s over %s' % (
                                    thisRule, thatRule)
                                stateDict[state][i] = (REDUCE,
                                                       item.ruleNumber)
                            else:
                                print 'favoring redux by %s over %s' % (
                                    thatRule, thisRule)
                            print
                    else:
                        stateDict[state][i] = (REDUCE, item.ruleNumber)

            #else if point is at the and and lhs is S', accept
            elif item.pointAtEnd() and item.lhs == "S'":
                for i in item.lookaheads:
                    stateDict[state][i] = (ACCEPT, item.ruleNumber)

            #else, panic
            else:
                raise RuntimeError, 'Waaaaaaah!!! Aieeee!'

    #compute goto table
    ## ATC -- this and the LR0 version are identical, move to common
    for state in range(len(C)):
        for item in C[state]:
            targetSet = goto(C[state], item.lhs, ruleSet, terminals)
            if targetSet:
                targetState = C.index(targetSet)
                gotoDict[state][item.lhs] = targetState

    return stateDict, gotoDict


if __name__ == '__main__':
    from RuleItems import Rule
    ruleSet = [
      Rule('S', ['E'], 0),
      Rule('E', ['E', '+', 'T'], 1),
      Rule('E', ['T'], 2),
      Rule('T', ['T', '*', 'F'], 3),
      Rule('T', ['F'], 4),
      Rule('F', ['(', 'E', ')'], 5),
      Rule('F', ['id'], 6),
      ]
    #ruleSet = [
    #    Rule('S', ['L', '=', 'R'], 0),
    #    Rule('S', ['R'], 1),
    #    Rule('L', ['*', 'R'], 2),
    #    Rule('L', ['id'], 3),
    #    Rule('R', ['L'], 4),
    #    ]
    #ruleSet = [
    #    Rule('S', ['C', 'C'], 1),
    #    Rule('C', ['c', 'C'], 2),
    #    Rule('C', ['d'], 3),
    #    ]
    #ruleSet = [
    #    Rule('S', ['i', 'S', 'e', 'S'], 1),
    #    Rule('S', ['i', 'S'], 2),
    #    Rule('S', ['a'], 3),
    #    ]
    t, nt = siftTokens(ruleSet)

    lr1 = items(ruleSet, t, nt)
    print 'LR1 Items'
    for i in range(len(lr1)):
        print 'state %d' % i
        for j in lr1[i]:
            print '        ', j

    sd, gd = generateStateTable(lr1, ruleSet, t)
    print ; print
    printStateTable(lr1, t, nt, sd, gd)

    import Parser
    p = Parser.ListTokenSource([
        Parser.Token('id'),
        Parser.Token('+'),
        Parser.Token('id'),
        Parser.Token('*'),
        Parser.Token('id')])
    r = Parser.parse(sd, gd, p, ruleSet)
    print r
