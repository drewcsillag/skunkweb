#  
#  Copyright (C) 2001 Andrew T. Csillag <drew_csillag@geocities.com>
#  
#      You may distribute under the terms of either the GNU General
#      Public License or the SkunkWeb License, as specified in the
#      README file.
#   
"""The reduction callback instance for loading pargen grammars"""
import RuleItems
import ParGenGrammar
import ParGenLex
import Parser

class RuleBuilder:
    """callback class for rule building reductions"""
    def __init__(self):
        self.ruleCount = 0
        self.rules = []

    def idToTokItem(self, X, id):
        return id.tokval

    def TokenToTokItem(self, X, token):
        return token.tokval

    def NullToTokList(self, X):
        return []

    def TTtoTokList(self, X, id, toklist):
        if type(toklist) != type([]):
            toklist=[toklist]
        return [id.tokval]+toklist

    def RuleLine(self, X, c1, funcName, c2, lhs, c3, rhs):
        funcName = funcName.tokval
        self.rules.append(RuleItems.Rule(lhs, rhs, self.ruleCount,
                                         funcName))
        #print 'Rule(%s, %s, %s, %s)' % (repr(lhs), repr(rhs),
        #                                repr(self.ruleCount), repr(funcName))
        self.ruleCount=self.ruleCount+1

    def noop(self, *args):
        pass

def loadGrammar(text, status = 1):
    if status:
        print 'loading grammar'
    tokenList = ParGenLex.lex(text)
    tokenSource = Parser.ListTokenSource(tokenList)
    ruleBuilder = RuleBuilder()
    Parser.Parse(ParGenGrammar, tokenSource, ruleBuilder)
    return ruleBuilder.rules
