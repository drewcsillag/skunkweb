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
"""load the EBNF grammar and convert to regular BNF"""
import Parser
import EBNFLex
import EBNFGrammar
import RuleItems

class RuleBuilder:
    def __init__(self):
        self.ruleList = []
        self.tmpCount = 0
        self.ruleCount = 0

    def noop(self, funcname, *args):
        return args
    
    def _munged(self, symbol):
        """returns the rhs's of rules with lhs == symbol where if an item
        in rhs == symbol, is converted to None

        so can easily compare two non-terminal rulesets to see if they are
        equivalent
        """
        ret = []
        #print 'looking for', symbol
        rules = self._prodsWithLHS(symbol)
        #print 'got', rules
        for rule in rules:
            nr = []
            for token in rule.rhs:
                if token != symbol:
                    nr.append(token)
                else:
                    nr.append(None)
            ret.append(nr)
        return ret

    def _deleteRulesByLHS(self, d):
        i = 0
        while i < len(self.ruleList):
            rule = self.ruleList[i]
            if rule.lhs == d:
                del self.ruleList[i]
            else:
                i = i + 1

    def _replaceRules(self, fromTok, toTok):
        for rule in self.ruleList:
            if fromTok in rule.rhs:
                nr = []
                for i in rule.rhs:
                    if i == fromTok:
                        nr.append(toTok)
                    else:
                        nr.append(i)
                rule.rhs = nr
                
    def removeDupes(self):
        removed = 1

        while removed:
            tnt = self._tempLHS()
            #print 'loop'
            removed = 0
            for si in range(len(tnt)):
                for di in range(si+1, len(tnt)):
                    src = tnt[si]
                    dst = tnt[di]
            #for src in tnt:
            #    for dst in tnt:
                    if src == dst:
                        continue
                    s = self._munged(src)
                    d = self._munged(dst)
                    #print 'comparing', s, d
                    if s == d and s:
                        #print 'removing', dst, 'and replacing with', src
                        removed = 1
                        self._deleteRulesByLHS(dst)
                        self._replaceRules(dst, src)
                
    def _getTempName(self):
        self.tmpCount = self.tmpCount + 1
        return '_temp%d' % self.tmpCount
    
    def _tempLHS(self):
        """returns the set of temp rule non-terminals"""
        l = {}
        for i in self.ruleList:
            if i.lhs[:5] == '_temp':
                l[i.lhs] = 1
        return l.keys()
    
    def _prodsWithLHS(self, lhs):
        r = []
        for i in self.ruleList:
            if i.lhs == lhs:
                r.append(i)
        return r
    #return filter(lambda x, lhs = lhs: x.lhs == lhs, self.ruleList)
    
    def noop1(self, x, i):
        return i
    
    def noopToken(self, x, t):
        return t.tokval

    def ELBuildAnchor(self, x):
        return []

    def ELBuildRecur(self, x, e, el):
        return [e,] + el

    def buildStar(self, x, pexpr, star):
        """
        X -> A B* C

        becomes:

        X -> A _temp C
        _temp -> B _temp
        _temp -> 
        """   
        nlhs = self._getTempName()
        self.ruleList.append(RuleItems.Rule(nlhs, [pexpr, nlhs], -2,
                                            '_STARRECUR'))
        self.ruleList.append(RuleItems.Rule(nlhs, [], -2, '_STARANCHOR'))
        return nlhs

    def buildPlus(self, x, optex, plus):
        """
        X -> A B+ C

        becomes:

        X -> A _temp C
        _temp -> B _temp
        _temp -> B
        """
        nlhs = self._getTempName()
        self.ruleList.append(RuleItems.Rule(nlhs, [optex, nlhs], -2,
                                             '_PLUSRECUR'))
        self.ruleList.append(RuleItems.Rule(nlhs, [optex], -2, '_PLUSANCHOR'))
        return nlhs

    def buildOptional(self, x, lbrack, el, rbrack):
        """
        X -> A [B C D] E

        becomes:

        X -> A _temp E
        _temp -> B C D
        _temp ->
        """
        nlhs = self._getTempName()
        self.ruleList.append(RuleItems.Rule(nlhs, el, -2, '_OPTEXISTS'))
        self.ruleList.append(RuleItems.Rule(nlhs, [], -2, '_OPTMISSING'))
        return nlhs

    def ExprSingle(self, x, el):
        """
        X -> A B C D
        becomes:
        X -> _temp
        _temp -> A B C D
        """
        nlhs = self._getTempName()
        self.ruleList.append(RuleItems.Rule(nlhs, el, -2, '_PARENPASS'))
        return [nlhs]

    def ExprRecur(self, x, el, bar, elr):
        """
        X -> A B | C D
        becomes
        X -> _temp
        _temp -> A B
        _temp -> C D
        """
        nlhs = self._getTempName()
        #print 'el is', el
        #print 'elr is', elr
        self.ruleList.append(RuleItems.Rule(nlhs, el, -2, '_PARENPASS'))
        self.ruleList.append(RuleItems.Rule(nlhs, elr, -2, '_ALTPASS'))
        return [nlhs]
    
    def buildAlternate(self, x, e, bar, pe):
        """
        X -> A B | C D

        becomes:

        X -> _temp
        _temp -> A B
        _temp -> C D
        """
        nlhs = self._getTempName()
        self.ruleList.append(RuleItems.Rule(nlhs, e, -2, '_ALTPASS'))
        self.ruleList.append(RuleItems.Rule(nlhs, pe, -2, '_ALTPASS'))
        return [nlhs]

    def buildParens(self, x, lp, el, rp):
        """
        X -> A (B C) D

        becomes:

        X -> A _temp D
        _temp -> B C
        """
        nlhs = self._getTempName()
        self.ruleList.append(RuleItems.Rule(nlhs, el, -2, '_PARENPASS'))
        return nlhs

    def buildRule(self, x, col1, func, col2, lhs, col3, rhs):
        self.ruleList.append(RuleItems.Rule(lhs.tokval, rhs, self.ruleCount, func.tokval))
        self.ruleCount = self.ruleCount + 1
                                            
def loadGrammar(text, status = 1):
    if status:
        print 'loading grammar'
    cbi = RuleBuilder()
    tokenList = EBNFLex.lexExp(text)
    tokenSource = Parser.ListTokenSource(tokenList)
    r = Parser.Parse(EBNFGrammar, tokenSource, cbi)
    if status:
        print 'cleaning up generated rules'

    rules = makeCores(cbi.ruleList)
    for i in range(len(rules)):
        rules[i].ruleNumber = i

    return trim(rules)
    #cbi.removeDupes()
    #renumber the rule numbers due to additions, removals
    #for i in range(len(cbi.ruleList)):
    #    cbi.ruleList[i].ruleNumber = i
    #return cbi.ruleList

class Core:
    def __init__(self, prod):
        self.rhs = []
        self.funcName = prod.funcName
        self.lhs = prod.lhs
        
        for i in prod.rhs:
            if i != prod.lhs:
                self.rhs.append(i)
            else:
                self.rhs.append(None)

    def asRule(self):
        nrhs = []
        for i in self.rhs:
            if i == None:
                nrhs.append(self.lhs)
            else:
                nrhs.append(i)
                
        return RuleItems.Rule(self.lhs, nrhs, -1, self.funcName)

    def __cmp__(self, other):
        c = cmp(self.rhs, other.rhs)
        if c:
            return c
        return cmp(self.funcName, other.funcName)
        
    def rewrite(self, fromT, toT):
        for i in range(len(self.rhs)):
            if self.rhs[i] == fromT:
                #print 'rewriting %s' % self.asRule()
                #print 'rewriting %s -> %s' % (fromT, toT)
                self.rhs[i] = toT
                #print 'to %s' % self.asRule()
                
class CoreSet:
    def __init__(self, lhs, prods):
        self.lhs = lhs
        self.cores = []
        for i in prods:
            self.cores.append(Core(i))

    def __cmp__(self, other):
        return cmp(self.cores, other.cores)

    def rewrite(self, fromT, toT):
        for c in self.cores:
            c.rewrite(fromT, toT)

    def asRules(self):
        return map(lambda x: x.asRule(), self.cores)

    def __repr__(self):
        s = 'CoreSet:\n'
        for i in self.asRules():
            s=s+'    %s\n' % i
        return s
    

def makeCores(ruleSet):
    import Common
    term, nonTerminals = Common.siftTokens(ruleSet)
    css = []
    for nt in nonTerminals:
        prods = filter(lambda x, lhs=nt: x.lhs == lhs, ruleSet)
        css.append(CoreSet(nt, prods))
    css.sort()

    removed = 1
    while removed:
        #print 'toppy'
        #for c in css:
        #    print c
        removed = 0
        ncss = [css[0]]
        lastSeen = css[0].lhs
        for i in range(1, len(css)):
            if css[i] != css[i-1] or css[i].lhs[0] != '_':
                ncss.append(css[i])
                lastSeen = css[i].lhs
            else:
                #print 'removing', css[i], 'in favor of', lastSeen
                removed = 1
                for cs in css:
                    cs.rewrite(css[i].lhs, lastSeen)
        css = ncss
        css.sort()
        
    newRules = []
    for cs in ncss:
        newRules.extend(cs.asRules())
    return newRules
        

def realTest():
    import sys, string
    text = open(sys.argv[1]).read()
    rules = loadGrammar(text, 0)
    for i in rules:
        print ':%s:%s:%s' % (i.funcName, i.lhs, string.join(i.rhs))

def cheesyPoofs():
    cbi = RuleBuilder()
    import sys
    text = open(sys.argv[1]).read()
    tokenList = EBNFLex.lexExp(text)
    tokenSource = Parser.ListTokenSource(tokenList)
    r = Parser.Parse(EBNFGrammar, tokenSource, cbi)

    import copy
    import time
    cbi2 = copy.deepcopy(cbi)

    print 'grammar loaded, removing dup rules'
    import Common
    t, nt = Common.siftTokens(cbi2.ruleList)
    beg = time.time()
    f = makeCores(cbi2.ruleList)
    end = time.time()

    print
    print 'new fasioned way:', end - beg, len(f)
    #for i in f:
    #    print i

    beg = time.time()
    cbi.removeDupes()
    end = time.time()

    print
    print 'old fasioned way:', end-beg, len(cbi.ruleList)
    #for i in cbi.ruleList:
    #    print i

    #renumber the rule numbers due to additions, removals
    #for i in range(len(cbi.ruleList)):
    #    cbi.ruleList[i].ruleNumber = i
    #return cbi.ruleList
    

def trim(rules):
    import Common
    t, nt = Common.siftTokens(rules)

    did_collapse = 1

    while did_collapse:
        did_collapse = 0
        #find singly defined, non recursive temp rules
        collapseables = {}
        for i in nt:
            rm = []
            for j in rules:
                if j.lhs == i:
                    rm.append(j)
            if len(rm) == 1 and rm[0].lhs[:5] == '_temp':
                cand = rm[0]
                if cand.lhs in cand.rhs:
                    #would seem to be bad as it would be an infinitely recurring
                    #rule
                    print 'not candidate, recursive', cand
                else:
                    print 'candidate', cand
                    collapseables[cand.lhs] = cand

        #collapse rules into users
        for i in rules:
            for j,c in zip(i.rhs, range(len(i.rhs))):
                if collapseables.has_key(j):
                    did_collapse = 1
                    print 'collapsing %s in %s' % (j, i)
                    i.rhs[c:c+1] = collapseables[j].rhs

        nrules = []
        for i in rules:
            if not collapseables.has_key(i.lhs):
                nrules.append(i)
        rules = nrules

    print 'renumbering'
    for i in range(len(rules)):
        rules[i].ruleNumber = i

    return rules

if __name__ == '__main__':
    #realTest()
    cheesyPoofs()

