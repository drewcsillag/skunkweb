#  
#  Copyright (C) 2001 Andrew T. Csillag <drew_csillag@geocities.com>
#  
#      You may distribute under the terms of either the GNU General
#      Public License or the SkunkWeb License, as specified in the
#      README file.
#   
"""A method-independant (sort of) way of computing the grammar"""
from Common import *
import LR1
import LR0
import LALR

def compileGrammar(method, ruleSet, showStates = None, showItems = None,
                   statusMsg = 1):
    """given the method and the ruleset, generate a parsing table.
    the other options are debug shit
    """
    if statusMsg:
        print 'scanning grammar for terminals and nonterminals'
    terminals, nonTerminals = siftTokens(ruleSet)
    digestedRules = digestRules(ruleSet)

    if statusMsg:
        print 'producing items for grammar'
        
    if method == 'LALR1': #LALR via canonical LR
        C = LR1.items(ruleSet, terminals, nonTerminals)
        C = LALR.canonicalLRToLALR(C)

    elif method == 'LALR0': #LALR via LR1 -roundaboutly
        C = LALR.items(ruleSet, terminals, nonTerminals)
        #C = LALR.computeLALRKernels(C, ruleSet, terminals, nonTerminals)

    elif method == 'LR1': #canonical LR
        C = LR1.items(ruleSet, terminals, nonTerminals)

    elif method == 'LR0': #SLR (LR0)
        C = LR0.items(ruleSet, terminals, nonTerminals)

    if showItems != None:
        printItems('%s Items' % method, C)
        if showItems == 2:
            return {}

    if statusMsg:
        print 'generating state and goto tables'
        
    if method == 'LALR1': #LALR via canonical LR
        stateTable, gotoTable = LR1.generateStateTable(C, ruleSet, terminals,
                                                       C.index)

    elif method == 'LALR0': #LALR via CLR - roundaboutly
        stateTable, gotoTable = LR1.generateStateTable(C, ruleSet, terminals,
                                                        C.index)

    elif method == 'LR1': #canonical LR
        stateTable, gotoTable = LR1.generateStateTable(
            C, ruleSet, terminals, lambda x, y=C: LR1.fullIndex(y, x))

    elif method == 'LR0': #SLR (LR0)
        stateTable, gotoTable = LR0.generateStateTable(C, ruleSet, terminals,
                                                       nonTerminals)
        
        
    if showStates != None:
        printStateTable(C, terminals, nonTerminals, stateTable, gotoTable)
        
    return {'states': stateTable,
            'gotos': gotoTable,
            'terminals': terminals,
            'rules': digestedRules
            }
