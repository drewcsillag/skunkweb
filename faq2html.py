import sre

numre = sre.compile('[0-9]+\)')
firstchar = sre.compile('^[a-zA-Z]')
faqtext = open('FAQ').read()

questions = []
output = []
counter = 1
for i in  numre.split(faqtext):
    if not i:
        continue

    x = i.replace('*','<li>')
    firstli = x.find('<li>')
    x = x[:firstli].replace('\n\n', '<P>') + '<ul>' + x[firstli:]
    questions.append((counter, x[:firstli].split('<P>')[0]))

    z = x
    while 1:
        b = z.rfind('\n\n')
        if x[b:].strip():
            break
        z = z[:b]

    #print '----', x[b:]
    #print '----', x[b:].find('<li>')
    if x[b:].find('<li>') == -1:
        x = x[:b] + '</ul>' + x[b:]
        #print '======', x[b:]
        #raise SystemExit
    else:
        x += '</ul>'
    
    output.append('<HR>%d) <A NAME="sec%d">%s' % (counter, counter, x))
    counter += 1

print "<OL>"
for i in questions:
    print '<LI><A HREF="#sec%d">%s</A></li>' % i
    print

print '</ol>'

for i in output:
    print i

