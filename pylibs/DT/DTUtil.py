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
import string
import base64
import types
import DTExcept

def debacktick(v):
    '''removes backticks from [0] and [-1] if they are there'''
    if len(v) and (v[0]==v[-1]=='`'):
        return v[1:-1]
    return v

def htmlquote(s):
    l=[]
    for i in s:
        if i=='&': l.append('&amp;')
        elif i=='<': l.append('&lt;')
        elif i=='>': l.append('&gt;')
        # elif i=='\n': l.append('<BR>')
        elif i=='"': l.append('&quot;')
        else: l.append(i)
    return string.join(l, '')

def latinquote(s):
    """Escapes all characters >=160 to numeric escape."""
    l = []
    for i in s:
	if ord(i) >=160: l.append("&#%03d;" % ord(i))
	else: l.append(i)
    return string.join(l, '')

def fullquote(s):
    """Escapes all characters to %XX format."""
    l = []
    for i in s:
        l.append( "%%%02x" % ord(i) )
    return string.join(l, '')

def b64(s):
    return base64.encodestring(s)

def pseudoApply(nds, tup=(), dict={}, tcol=None, kwcol=None):
    retdict={}
    
    lennds=len(nds)
    lentup=len(tup)

    keywordables={}
    adjustkwcol=adjusttcol=0

    if kwcol is not None:
        adjustkwcol=1
        retdict[kwcol]={}
    if tcol is not None:
        adjusttcol=1
        retdict[tcol]=()
        
    #make a dict of argument names for later perusal
    for i in nds:
        if type(i)==types.TupleType:
            keywordables[i[0]]=1
        else:
            keywordables[i]=1
            
    #handle tuple arguments
    for i in range(min(lennds, lentup)):
        if type(nds[i])==types.TupleType:
            retdict[nds[i][0]]=tup[i]
        else:
            retdict[nds[i]]=tup[i]

    #oops, too many args
    if lentup>lennds:
        if tcol is None:
            raise TypeError, 'too many arguments; expected %d, got %d' % (
                lentup, lennds)
        else:
            retdict[tcol]=tup[lennds:]

    #handle keyword arguments
    for k,v in dict.items():
        if retdict.has_key(k):
            raise TypeError, 'keyword parameter redefined'
        elif not keywordables.has_key(k):
            if kwcol is None:
                raise TypeError, 'unexpected keyword argument: %s' % k
            else:
                retdict[kwcol][k]=v
        else:
            retdict[k]=v

    #handle default arguments
    for i in nds:
        if type(i)==types.TupleType:
            if not retdict.has_key(i[0]):
                val=i[1]
                #some hacks to make this fit into the old way
                if val=='None':
                    val=None
                elif val=='""':
                    val=''
                elif (type(val)==types.StringType
                    and len(val)>1
                    and val[0]==val[-1]=='"'): #dumb quoted string
                    val=val[1:-1]
                #end of bullshit hacks
                retdict[i[0]]=val

    #make an adjustment for length comparison
    adjustedretdictlen=len(retdict)-(adjusttcol+adjustkwcol)

    #did we get enough args?
    if lennds > adjustedretdictlen:
        #print retdict
        raise TypeError, 'not enough arguments; expected %d, got %d' % (
            lennds, adjustedretdictlen)

    #return
    #print retdict
    return retdict

def tagCall(tag, argspec, tcol=None, kwcol=None):
    t,d = tag.tupargs, tag.dictargs
    try:
        return pseudoApply ( argspec, t, d, tcol, kwcol )
    except:
        raise DTExcept.DTCompileError ( tag, 'error parsing arguments: %s\n'
             'args are %s, tuple args are %s, dictargs are %s' % 
             ( sys.exc_info()[1], argspec, t, d ) )
