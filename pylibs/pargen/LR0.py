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
"""LR(0) (SLR) grammar routines"""
from CONSTANTS import *
from Common import *

def closure(items, ruleSet, nonTerminals):
    """compute the closure of <items>"""
    result = items[:]
    added = 1
    while added:
        added = 0
        for item in result:
            if not item.pointAtEnd():
                symbol = item.expects()
            else:
                continue
            if symbol in nonTerminals:
                prods = getProductions(ruleSet, symbol)
                for rule in prods:
                    newItem = rule.getItem()
                    if newItem not in result:
                        result.append(newItem)
    return result

def goto(I, X, ruleSet, nonTerminals):
    """compute goto(I, X) or goto(I, X) LR0'ly
    """
    closureI = []
    for item in I:
        if not item.pointAtEnd() and item.expects() == X:
            closureI.append(item.newAdvancedDot())
    return closure(closureI, ruleSet, nonTerminals)
            
def items(ruleSet, terminals, nonTerminals):
    """compute the LR0 items"""
    symbols = nonTerminals + terminals
    C = [ closure([startItem], ruleSet, nonTerminals) ]
    added = 1
    while added:
        added = 0
        for I in C:
            for X in symbols:
                g = goto(I, X, ruleSet, nonTerminals)
                if g and g not in C:
                    added = 1
                    C.append(g)
    return C

def generateStateTable(C, ruleSet, terminals, nonTerminals):
    """from the LR0 collection of item sets, generate the state and
    goto tables
    """
    #initialize the state table
    stateDict = {}
    for i in range(len(C)):
        stateDict[i] = {}

    #initialize the goto table
    gotoDict = {}
    for i in range(len(C)):
        gotoDict[i] = {}

    #loop through the item sets in the collection
    for state in range(len(C)):
        #loop through the the items in the current state/set
        for item in C[state]:
            exp = item.expects() #what to we expect to see next?
            #do we go anywhere, and if so, where do we go?
            targetSet = goto(C[state], exp, ruleSet, nonTerminals)

            #if we go somewhere, shift and go there
            #check for conflicts
            if targetSet:
                if exp in terminals:
                    if stateDict[state].has_key(exp):
                        x = stateDict[state][exp]
                        if x[0] == SHIFT:
                            print ('shift/shift conflict for %s, favoring '
                                   'this') % item
                        if x[1] == REDUCE:
                            print ('shift/reduce conflict for %s, was '
                                   'reducing by %s, now shifting') % (
                                       item, str(ruleSet[x[1]]))

                    targetState = C.index(targetSet)
                    stateDict[state][exp] = (SHIFT, targetState)

            #else if the point is at the end and not S', reduce
            elif item.pointAtEnd and item.lhs != "S'":
                a = FOLLOW(item.lhs, ruleSet, terminals, nonTerminals)
                for i in a:
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

                    else:
                        stateDict[state][i] = (REDUCE, item.ruleNumber)

            #else the point is at the end and is S', so accept
            elif item.pointAtEnd and item.lhs == "S'":
                stateDict[state]['$'] = (ACCEPT, item.ruleNumber)

            #else, panic
            else:
                raise RuntimeError, 'Waaaaaaah!!! Aieeee!'
            
    #compute goto
    for I, state in map(None, C, range(len(C))):
        for nt in nonTerminals:
            set = goto(I, nt, ruleSet, terminals)
            if set and set in C:
                print set
                targetState = C.index(set)
                gotoDict[state][nt] = targetState

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

    t, nt = siftTokens(ruleSet)
    C = items(ruleSet, t, nt)
    print 'LR0 Items'
    for i in range(len(C)):
        print 'state %d' % i
        for j in C[i]:
            print '        ', j

    sd, gd = generateStateTable(C, ruleSet, t, nt)
    print ; print
    printStateTable(C, t, nt, sd, gd)

    import Parser
    p = Parser.ListTokenSource(['id', '+', 'id', '*', 'id'])
    Parser.parse(sd, gd, p, ruleSet)
