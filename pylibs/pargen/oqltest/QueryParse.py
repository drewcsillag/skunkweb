import sys
import QueryLex
import QueryGrammar
import lalr.Parser

class T:
    def __init__(self):
        self.toktype = 'ENDMARKER'
        self.tokval = None
        
def parse(s):
    tokList = QueryLex.lexExp(s)
    #tokList.append(T())
    tokSource = lalr.Parser.ListTokenSource(tokList)
    return lalr.Parser.Parse(QueryGrammar, tokSource, debug = 1)

while 1:
    try:
        s = raw_input('query string:')
        print parse(s)
    except 'ParserException', val:
        print 'blew up on', s
        print val
        break
    except EOFError:
        break
