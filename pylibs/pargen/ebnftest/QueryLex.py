import string
import re
import types

slicere=re.compile('slice')
floatre=re.compile('[0-9]+\.[0-9]+')
intre=re.compile('[0-9]+(?!\.)')
attrThing=re.compile('self.([a-zA-Z_][a-zA-Z0-9_]*)')
op=re.compile('(==|!=|<=|>=|>(?!=)|<(?!=))')
ws=re.compile('\s+')
quotedString=re.compile(r"'(.*?)'")
doubleQuotedString=re.compile(r'"(.*?)"')
bindVar=re.compile('@([a-zA-Z_][a-zA-Z0-9_]*)')
kwre=re.compile('(get|select|exists|count|where|and|or|not|true|range|in)\s+')
datere=re.compile('Date(?=[\s(])')
sortby=re.compile('sort\s+by')
descre=re.compile('desc(?=$|\s+|\s*,)')
paren=re.compile('(\(|\))')
entityName=re.compile('[a-zA-Z_][a-zA-Z_0-9]*(?!\.)')
comma=re.compile(',')
brace=re.compile('(\[|\])')

class Token:
    def __init__(self, ttype, tval):
        self.toktype=ttype
        self.tokval=tval
    def __repr__(self):
        return '<Token %s : "%s">' % (self.toktype, self.tokval)

toklook=(
    (slicere, 'SLICE', lambda x: x.group()),
    (floatre, 'FLOAT', lambda x: float(x.group())),
    (intre, 'INT', lambda x: int(x.group())),
    (attrThing, 'ATTR', lambda x: x.group(1)),
    (op, 'OP', lambda x: x.group()),
    (quotedString, 'QUOTESTR', lambda x: x.group(1)),
    (doubleQuotedString, 'QUOTESTR', lambda x: x.group(1)),
    (bindVar, 'BINDVAR', lambda x: x.group(1)),
    (datere, 'DATE', lambda x: x.group()),
    (kwre, lambda x: string.upper(x.group(1)), lambda x: x.group(1)),
    (paren, lambda x: x.group(1), lambda x: x.group(1)),
    (descre, 'DESC', lambda x: x.group()),
    (sortby, 'SORTBY', lambda x: x.group()),
    (entityName, 'ENTITY_NAME', lambda x: x.group()),
    (comma,',',lambda x: x.group()),
    (brace, lambda x: x.group(1), lambda x: x.group(1)),
    (ws,),
    )
    
     
def lexExp(text):
    toks=[]
    offset=0
    while offset < len(text):
        chunk=text[offset:]
        for i in toklook:
            lre=i[0]
            m=lre.match(chunk)
            if m:
                if len(i)==1:
                    offset=offset+m.end()
                    break
                elif type(i[1])==types.LambdaType:
                    tokname=i[1](m)
                else:
                    tokname=i[1]
                toks.append(Token(tokname, i[2](m)))
                offset=offset+m.end()
                break
        else:
            raise 'LexicalError', 'Invalid thing in query %s' % chunk[:10]
    return toks

if __name__=='__main__':
    while 1:
        print lexExp(raw_input('expression:'))
