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

ruleSet=[
    #Rule("Start", ['S','$'], 0, 'noop'),
    Rule('S', ['RuleList'], 0, 'noop'),
    Rule('RuleList', ['Rule', 'RuleList'], 1, 'noop'),
    Rule('RuleList', [], 2, 'noop'),
    Rule('Rule', ['COLON', 'id', 'COLON', 'TokItem', 'COLON', 'TokList'],
         3,'RuleLine'),
    Rule('TokList', ['Token', 'TokList'], 4, 'TTtoTokList'),
    Rule('TokList', ['id', 'TokList'], 5, 'TTtoTokList'),
    Rule('TokList', [], 6, 'NullToTokList'),
    Rule('TokItem', ['Token',], 7, 'TokenToTokItem'),
    Rule('TokItem', ['id',], 8, 'idToTokItem'),
    ]

print 'Rules'
print '--------------------'
for i in ruleSet:
    print i

grammar = CompileGrammar.compileGrammar('LALR1', ruleSet, showStates = 1, showItems = 1)
gf = open ('ParGenGrammar.py', 'w')
for i in grammar.items():
    gf.write('%s = %s\n' % i)
gf.close()
