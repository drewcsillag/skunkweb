#  
#  Copyright (C) 2001 Andrew T. Csillag <drew_csillag@geocities.com>
#  
#      You may distribute under the terms of either the GNU General
#      Public License or the SkunkWeb License, as specified in the
#      README file.
#   
import GrammarLoader
from Common import *

rules = GrammarLoader.loadGrammar(open('oqltest/QueryGrammar.y').read())
t, nt = siftTokens(rules)

