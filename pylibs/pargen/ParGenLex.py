#  
#  Copyright (C) 2001 Andrew T. Csillag <drew_csillag@geocities.com>
#  
#      You may distribute under the terms of either the GNU General
#      Public License or the SkunkWeb License, as specified in the
#      README file.
#   
import sys
sys.path.insert(0, '..')
from Parser import Token
import re

idre=re.compile('[A-Za-z_][A-Za-z0-9_]*')
wsre=re.compile('[\r\n\t ]+')
tre=re.compile('[-=<>!|^&/%~\[\]{}`A-Za-z0-9_+().*$;,]+')
comment=re.compile('#.*')

def lex(s):
    i=0
    toklist=[]
    while i < len(s):
        com=comment.match(s[i:])
        if com:
            i=i+com.end()
            #print 'comment, skipping'
            continue
        ws=wsre.match(s[i:])
        if ws:
            i=i+ws.end()
            #print 'whitespace, skipping'
            continue
        if s[i]==':':
            i=i+1
            toklist.append(Token('COLON'))
            #print 'colon'
            continue
        id=idre.match(s[i:])
        if id:
            i=i+id.end()
            toklist.append(Token('id', id.group()))
            #print 'id: %s' % id.group()
            continue
        tok=tre.match(s[i:])
        if tok:
            i=i+tok.end()
            toklist.append(Token('Token', tok.group()))
            #print 'Token: %s' % tok.group()
            continue
        print 'ARGHH!! Lexer Error:', s[i:20+i]
    toklist.append(Token('$'))
    return toklist

if __name__=='__main__':
    tl=lex(open(sys.argv[1]).read())
    for i in tl: print i
