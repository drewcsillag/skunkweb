import sre


def dosub(match):
    return '<A HREF="%s">%s</A>' % (match.group(0), match.group(0))

numre = sre.compile('[0-9]+\)')
firstchar = sre.compile('^[a-zA-Z]')
faqtext = open('FAQ').read()
linktext = sre.compile(r'http:[^ \n]+')
questions = []
output = []
counter = 1
for i in  numre.split(faqtext):
    if not i:
        continue

    
    i = linktext.sub(dosub, i)



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

    if x[b:].find('<li>') == -1:
        x = x[:b] + '</ul>' + x[b:]
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

