#  
#  Copyright (C) 2001 Andrew T. Csillag <drew_csillag@geocities.com>
#  
#      You may distribute under the terms of either the GNU General
#      Public License or the SkunkWeb License, as specified in the
#      README file.
#   
"""A top down, recursive decent, extensible parsing engine"""
import types
import string
import sys

import DTExcept

#used for if an exception is raised, to find out which tag we blew chunks
#on (either during parsing or evaluating).  This is inherently not
#thread safe and may be a bad way to do this (the 'correct' way to do
#this would be to catch and reraise all exceptions with the current
#tag, but that is really a pain in the neck and might lead to problems
#later on, but they can be fixed later if we decide that this sucks
#ass
CurrentTag=None

class Stack:
    """I don't think this really needs to be documented, or even mentioned"""
    
    def __init__(self):
        self.s=[]
        
    def pop(self):
        if not self.s: return
        ret=self.s[-1]
        self.s=self.s[:-1]
        return ret

    def push(self, item):
        self.s.append(item)
        
    def peek(self):
        if self.s: return self.s[-1]

    def empty_p(self):
        return not s

class Node:
    """A non-leaf node in the parse tree"""
    def __init__(self):
        self.children=[]

    def add(self, item):
        self.children.append(item)

    #the next two provide a printable version of this thing for debugging
    def myrep(self, indent=0):
        t=(indent*' ')+'Node: {\n'
        for i in self.children:
            if type(i)==type(''):
                t=t+((indent+4)*' ')+'String: "'+string.strip(i)+'"\n'
            else:
                try:
                    t=t+i.myrep(indent+4)
                except AttributeError:
                    t=t+((indent+4)*' ')+'Tag: '+str(i)+'\n'
                    
        return t+(indent*' ')+'}\n'
    def __str__(self):
        return self.myrep()

def parseit(text, taglist, tagreg, name):
    """parse the taglist and return list of text/nodes"""
    cur=0
    retl=[] #this isn't really a node, but it will be, so treat it that way
    #while we haven't passed the end of the tag list
    while cur < len(taglist):
        #if the current tag is text, append to the current Node
        if type(taglist[cur]) == types.StringType:
            retl.append(taglist[cur])
            cur=cur+1
        else:
            #it's a dtml tag, pass it to the generic handler for further
            #processing
            item, last=genHandler(text, taglist, cur, tagreg, name)
            cur=last+1
            retl.append(item)
    x=Node()
    #add all things from retl into x.  Question: why didn't I just create
    #a node in the first place?  Answer: no fucking idea.
    map(lambda y, x=x: x.add(y), retl)
    return x

def genHandler(text, taglist, start, tagreg, name):
    '''we got a tag that needs to be parsed'''
    curTag=taglist[start]
    tagname=curTag.tagname
    #get the DTTag object for the current tag
    try:
        dttag=tagreg.getTag(tagname)
    except KeyError, val: #not a valid tagname, barf
        raise DTExcept.DTCompileError ( curTag, 'invalid tag name %s' % tagname )

    #if an empty tag (like <:var:>, <:break:>, et. al.)
    if dttag.isempty:
        if curTag.isclose:
            #it's a closing empty tag????
            raise DTExcept.DTCompileError ( curTag, 'empty close tag??? %s' %
                                            curTag.tagname )
        return curTag, start
    else: #it's a non-empty tag (like <:if:><:/if:>)
        #have the DTTag parse it's block
        return dttag.parseBlock(text, taglist, start, tagreg, name)

if __name__=='__main__':
    import DTLexer
    import sys
    import DTTagRegistry
    text=open(sys.argv[1]).read()
    taglist=DTLexer.doTag(text)
    node=parseit(text, taglist, DTTagRegistry.defaultTagRegistry, None)
    print '--------------------'
    print node
