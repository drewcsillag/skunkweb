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
