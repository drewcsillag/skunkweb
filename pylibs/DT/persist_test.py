#  
#  Copyright (C) 2001 Andrew T. Csillag <drew_csillag@geocities.com>
#  
#      You may distribute under the terms of either the GNU General
#      Public License or the SkunkWeb License, as specified in the
#      README file.
#   
import sys
import DTParser
import types
import timer

plat=sys.platform
#if plat[:4]=='java':
#    def pfunc(item):
#        from java.io import ByteArrayOutputStream, ObjectOutputStream
#        bos=ByteArrayOutputStream()
#        oos=ObjectOutputStream(bos)
#        oos.writeObject(item)
#        return str(bos)
#    def ufunc(s):
#        from java.io import ByteArrayInputStream, ObjectInputStream
#        bis=ByteArrayInputStream(s)
#        ois=ObjectInputStream(bis)
#        return ois.readObject()
#else:
if 1:
    #import cPickle
    #pickle=cPickle
    import pickle

    def pfunc(item):
        return pickle.dumps(item)
    def ufunc(s):
        return pickle.loads(s)

def pertest(name, item):
    print name, item
    print len(pfunc(item))
    
class nsc:
    this='that'
    num=1
ns=nsc()

import DT
t=timer.Timer()
print t, 'start'
x=DT.DT(open('tests/test1.dtml').read())
print t, 'cooked'
output= x(ns)
print t, 'rendered'

#node=x.node
#for i in node.children:
#    pertest('i',i)
#    if hasattr(i, 'children'):
#        for j in i.children:
#            pertest('j',j)
#            if hasattr(j,'children'):
#                for k in j.children:
#                    pertest('k', k)

print 'serializing'
print t, 'before'
data=pfunc(x)
print t, 'after'
print 'len of ser data', len(data)

print 'de serializing'
print t, 'before'
y=ufunc(data)
print t, 'after'
data=y.render(ns)
print t,'rendered'
print 'rendered:',y.render(ns)
