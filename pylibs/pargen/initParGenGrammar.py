#  
#  Copyright (C) 2001 Andrew T. Csillag <drew_csillag@geocities.com>
#  
#      You may distribute under the terms of either the GNU General
#      Public License or the SkunkWeb License, as specified in the
#      README file.
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
