#  
#  Copyright (C) 2001 Andrew T. Csillag <drew_csillag@geocities.com>
#  
#      This program is free software; you can redistribute it and/or modify
#      it under the terms of the GNU General Public License as published by
#      the Free Software Foundation; either version 2 of the License, or
#      (at your option) any later version.
#  
#      This program is distributed in the hope that it will be useful,
#      but WITHOUT ANY WARRANTY; without even the implied warranty of
#      MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#      GNU General Public License for more details.
#  
#      You should have received a copy of the GNU General Public License
#      along with this program; if not, write to the Free Software
#      Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111, USA.
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
