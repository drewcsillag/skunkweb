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
