#! /usr/bin/env python

PYTHON="/usr/local/bin/python"
SOURCEPATH="/home/smulloni/src/Python-2.3.3c1"

#if /eval_frame(<foo>)/
#   f = <foo>
#
#p f->f_lineno
#p ((char*)&((PyStringObject*)f->f_code->co_filename)->ob_sval)

import time
import sys

import popen2
import select
import os
import sre
import linecache

tb = []

corefile = sys.argv[1]
if len(sys.argv) > 2:
    verbose = 1
else:
    verbose = 0
sout, sin, serr = popen2.popen3('gdb %s %s' % (PYTHON,corefile), bufsize=0)

def sleep(t):
    return
    if verbose:
        time.sleep(t)
        
def send(s):
    if verbose:
        sys.stdout.write(s)
        sys.stdout.flush()
    sin.write(s)

def read(n, p = sout):
    i = p.read(n)
    if verbose:
        sys.stdout.write(i)
        sys.stdout.flush()
    return i

def readline(p = sout):
    i = p.readline()
    if verbose:
        sys.stdout.write(i)
        sys.stdout.flush()
    return i

def findprompt():
    #print "####FIND PROMPT"
    while 1:
        m = read(6)
        if m=='(gdb) ':
            break
        line = m+readline()
        #print line,
    #print "/####FIND PROMPT"

def checkerror():
    diderror = 0
    while 1:
        r,w,e = select.select([serr],[],[],0)
        diderror = 1
        if serr in r:
            err = serr.readline()
            if err[:9] != 'No symbol':
                realbreak=1
                break
            print '!!!', err
        else:
            break
    return diderror

outfar = ''
while 1:
    r, w, e = select.select([sout, serr], [sin], [])
    if sout in r:
        f = readline()
        if f[0] == '#':
            #print readline()
            print "!!!!!"
            break
        
        #m = sout.read(5)
        #f += m
        outfar += f
        #sys.stdout.write(f); sys.stdout.flush()
        #if m == '(gdb)':
        #    break
        
        #if outfar.find('<q return to quit') != -1:
        #    sin.write('q\n')
        #    break
    if serr in r:
        f = serr.readline()
        #sys.stdout.write(f); sys.stdout.flush()
    
sin.write('dir %s\n' % SOURCEPATH)
print sout.readline()
print sout.read(5)
print '----------'


realbreak=0
while 1:
    send('up\n')
    sleep(1)
    m=''

    if realbreak:
        break
    
    while 1:
        m = read(5)
        if m=='(gdb)':
            break
        line = m+readline()
        #print line,
        #line = line+m
        #print '----', line
        if line.find('Py_Main') != -1:
            print '!!!!!--->', line
            realbreak = 1
            break
        
        if line.find('eval_frame') != -1:
            findprompt()
            #print 'line was---->', line
            send('p f->f_lineno\n')
            while 1:
                nline = readline()
                if nline.strip()[0] != '$':
                    print "DOOKY", line
                    if checkerror():
                        nline = None
                        break
                else:
                    break
            if nline is None:
                break
            sleep(1)

            #if checkerror():
            #    continue
            lineno = sre.sub(r'\$[0-9]+ = ([0-9]+)', r'\1', nline)
            #findprompt()
            read(5)
            send('p ((char*)&((PyStringObject*)f->f_code->co_filename)->ob_sval)\n')
            #if checkerror():
            #    continue
            #while 1:
            #    nline = readline()
            #    if nline.strip()[0] != '$':
            #        print "DOOKY2", line
            #        if checkerror():
            #            nline = None
            #            break
            #    else:
            #        break
            #if nline is None:
            #    break

            filename = sre.sub(r'\$[0-9]+ = 0x[0-9a-f]+ "([a-zA-Z_./0-9]+)"', r'\1', readline())#nline)
            sleep(1)

            try:
                item = (filename.strip(), int(lineno.strip()))
                #print item
                if not tb or item != tb[-1]:
                    tb.append(item)
            except:
                print "HUH!!!", lineno, filename


#print '!',serr.readline()
tb.reverse()

for file, lineno in tb:
    print '%s: %s' % (file, lineno)
    line = linecache.getline(file, lineno)
    if line:
        print '    %s' % line.strip()
    
