CODE, LITERAL = ('CODE', 'LITERAL')#range(2)

def psp_compile(s, name):
    """<% and %> are the code delimiters"""
    l = []
    while 1:
        ci = s.find('<%')
        if ci == -1:
            l.append((LITERAL, s))
            break
        l.append((LITERAL,s[:ci]))
        code = s[ci+2:]
        #print 'code is ', code
        ce = code.find('%>')
        if ce == -1:
            raise 'EOFError', 'End of file reached while in code'
        code = code[:ce]
        l.append((CODE, code))
        s = s[ci + 2 + ce+2:]

    codestr = ''
    for kind, s in l:
        #print kind, repr(s)
        if kind == LITERAL:
            sl = s.split('\n')
            for si in sl:
                codestr+='print %s\n' % repr(si)
        else:
            cs = s.split('\n')
            if cs[0].strip() == '': #stuff after initial <% is blank to eol
                s = '\n'.join(cs[1:])
            codestr+=s
    #print 'codestr is', codestr
    return compile(codestr, name, 'exec'), codestr

if __name__=='__main__':
    t = """Counting to 3<%
for i in range(3):
    print i
%>

done counting"""
    co = psp_compile(t,'<string>')
    exec co[0] in {}
