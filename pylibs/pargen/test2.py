#  
#  Copyright (C) 2001 Andrew T. Csillag <drew_csillag@geocities.com>
#  
#      You may distribute under the terms of either the GNU General
#      Public License or the SkunkWeb License, as specified in the
#      README file.
#   
from RuleItems import Rule
import CompileGrammar
ruleSet = [
    Rule('S', ['E'], 0),
    Rule('E', ['E', '+', 'T'], 1),
    Rule('E', ['T'], 2),
    Rule('T', ['T', '*', 'F'], 3),
    Rule('T', ['F'], 4),
    Rule('F', ['(', 'E', ')'], 5),
    Rule('F', ['id'], 6),
]

import Parser
tokenList = [
    Parser.Token('id'),
    Parser.Token('+'),
    Parser.Token('id'),
    Parser.Token('*'),
    Parser.Token('id'),
    ]

results = []
for method in 'LALR1', 'LALR0':#'LR1', 'LALR1', 'LALR0', 'LR0':
    cdg = CompileGrammar.compileGrammar(method, ruleSet, 1, 1)
    #print cdg
    p = Parser.ListTokenSource(tokenList)
    results.append(Parser.Parse(cdg, p))#, debug=1))
    #print Parser.Parse(cdg, p)
for i in results:
    print 
    print i
