#  
#  Copyright (C) 2001 Andrew T. Csillag <drew_csillag@geocities.com>
#  
#      You may distribute under the terms of either the GNU General
#      Public License or the SkunkWeb License, as specified in the
#      README file.
#   
"""LALR(1) operations"""
import LR0
import LR1
import copy
from Common import *

def canonicalLRToLALR(C):
    """converts a canonical LR(1) set of items to an LALR(1) set"""
    nC = []
    
    for i in range(len(C)):
        I = C[i]
        #since we're building nC one bit at a time, there will be at
        #most one duplicate of I in nC
        
        #find dup rules (ignoring lookaheads)
        try:
            dup = nC.index(I)
        except: #no duplicate, add to nC
            nC.append(copy.deepcopy(I))
        else:   #duplicate found, update lookaheads
            for ncItem, CItem in map(None, nC[dup], I):
                ncItem.lookaheads.addSet(CItem.lookaheads)
    return nC

def compareSet(old, new):
    """returns:
    1 if new has lookaheads not in old
    0 otherwise
    """
    for oldItem, newItem in map(None, old, new):
        if not oldItem.lookaheads.contains(newItem.lookaheads):
            return 1
    return 0

def updateLookaheads(old, new):
    """add the lookaheads from new to old"""
    for oldItem, newItem in map(None, old, new):
        oldItem.lookaheads.addSet(newItem.lookaheads)
        
def items(ruleSet, terminals, nonTerminals):
    """compute LALR1 items for ruleset"""
    symbols = nonTerminals + terminals
    #start with closure of [ [S' -> S, $] ]
    C = [LR1.closure([startItem], ruleSet, terminals)]
    added = 1
    while added:
        added = 0
        for I in C:
            for X in symbols:
                g = LR1.goto(I, X, ruleSet, terminals)

                if g and not g in C: #if no core already there:
                    added = 1
                    C.append(g)
                elif g and g in C: #if core is there:
                    target = C[C.index(g)]
                    if compareSet(target, g):
                        added = 1
                        updateLookaheads(target, g)
    return C





