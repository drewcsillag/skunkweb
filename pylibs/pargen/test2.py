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
