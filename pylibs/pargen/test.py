#  
#  Copyright (C) 2001 Andrew T. Csillag <drew_csillag@geocities.com>
#  
#      You may distribute under the terms of either the GNU General
#      Public License or the SkunkWeb License, as specified in the
#      README file.
#   
from Common import *
from RuleItems import Rule

ruleSet = [
  Rule('S', ['T', "E'"], 0),
  Rule("E'", ['+', 'T', "E'"], 1),
  Rule("E'", [], 2),
  Rule('T', ['F', "T'"], 3),
  Rule("T'", ['*', 'F', "T'"], 4),
  Rule("T'", [], 5),
  Rule('F', ['(', 'S', ')'], 6),
  Rule('F', ['id'], 7),

  ]
t, nt = siftTokens(ruleSet)
print FOLLOW('id', ruleSet, t, nt)
