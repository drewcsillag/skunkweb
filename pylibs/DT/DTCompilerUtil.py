#  
#  Copyright (C) 2001 Andrew T. Csillag <drew_csillag@geocities.com>
#  
#      You may distribute under the terms of either the GNU General
#      Public License or the SkunkWeb License, as specified in the
#      README file.
#   
# Time-stamp: <01/04/12 13:13:08 smulloni>
########################################################################
import os
import sys
import types
import string
import cStringIO
StringIO=cStringIO

import DTCommon
import DTParser
import DTExcept
from SkunkExcept import *

tempnum=0
cur_d=None

def getTempName():
    """generates temporary variable names"""
    global tempnum
    newname = '__t.temp%d' % tempnum
    # unlikely though it is, avoid overflow of int
    if tempnum < sys.maxint:
        tempnum += 1
    else:
        tempnum=0

    return newname

def tagDebug(indent, codeout, tag):
    """put some code to mark where we are in terms of execution"""
    codeout.write(indent, '__d.CURRENT_TAG = %s' % repr(repr(tag)))
    codeout.write(indent, '__d.CURRENT_LINENO = %s' % repr(tag.filelineno()))


def convertToNativeLineEndings(s):
    if os.linesep == '\n': # unix style
        s = s.replace('\r\n','\n')
        s = s.replace('\r', '\n')
        return s
    elif os.linesep == '\r': # mac style
        s = s.replace('\r\n', '\r')
        s = s.replace('\n', '\r')
        return s
    elif os.linesep == '\r\n': # dos/win style
        #yes this is fairly convoluted to convert to unix, then cvt to
        #dos/win style, but there is no other convienient way which does
        #not require a regex, which seems overkill
        s = s.replace('\r\n','\n')
        s = s.replace('\r', '\n')
        s = s.replace('\n', '\r\n')
        return s
    
def pyifyArgs(tag, args, parenthesize_exprs = 0):
    """convert arguments to an evalable format"""
    nd={}
    for k,v in args.items():
        if type(v)==types.StringType:
            if len(v)>1 and v[0]==v[-1]=="`":
                if parenthesize_exprs:
                    nd[k]="(%s)" % convertToNativeLineEndings(v[1:-1])
                else:
                    nd[k]=convertToNativeLineEndings(v[1:-1])
            else:
                nd[k]=repr(v)
        else:
            nd[k]=v

        if type(nd[k]) == types.StringType:
            try:
                compile(nd[k]+'\n', nd[k], 'exec')
            except SyntaxError, val:
                raise DTExcept.DTCompileError ( tag, 
                            'syntax error in argument: %s' % val)
    return nd

def pyifyKWArgs(tag, args, parenthesize_exprs = 0):
    nargs=pyifyArgs(tag, args, parenthesize_exprs)
    nl=[]
    for k,v in nargs.items():
        nl.append('%s: %s' % (repr(k),v))
    return '{'+string.join(nl,', ')+'}'

class Output:
    """the output object used for generating code"""
    def __init__(self):
        self.textlist=[]

    def write(self, indent, s):
        self.textlist.append((' '*indent) + s)
        
    def writelines(self, *lines):
        for indent, s in lines:
            self.textlist.append((' '*indent) +s)

    def writemultiline(self, indent, s):
        it = ' '*indent
        for i in s.split('\n'):
            self.textlist.append(it + i)

    def getText(self):
        return string.join(self.textlist,'\n')+'\n'
    
    def writeOutObj(self, outObj):
        self.textlist.append(outObj.getText())

def niceifyStringOutput(indent, s):
    """break lines of long strings at 40 chars"""
    if not len(s):
        return '""'
    nl=[]
    lens=len(s)
    for i in range(0, lens, 40): #break lines at 40 chars
        if i+40 > lens:
            end=lens
        else:
            end=i+40
        nl.append(s[i:end])
    return string.join(map(repr, nl), '\n' + (indent*' '))

def genCodeNode(indent, codeout, tagreg, children, meta):
    for i in children:
        # XXX note that for now, we only generate meta data for top-level
        # tags!!!!
        genCodeChild(indent, codeout, tagreg, i, meta)

def genCodeChild ( indent, codeout, tagreg, thing, meta ):
    if type(thing) == types.StringType:
        codeout.write(indent, '')
        codeout.write(indent, '########################################')
        codeout.write(indent, '__h.OUTPUT.write(%s)' %
                      niceifyStringOutput(indent+16, thing))
        codeout.write(indent, '########################################')
    elif (type(thing) == types.InstanceType
          and thing.__class__ == DTParser.Node):
        tagname=thing.children[0].tagname
        dttag=tagreg.getTag(tagname)

        # Generate the meta-data first
        if meta is not None:
            dttag.genMeta ( thing, meta )

        codeout.write(indent, '')
        codeout.write(indent, '#----------------------------------------')
        dttag.genCode(indent, codeout, tagreg, thing, meta)
        codeout.write(indent, '#----------------------------------------')
    else: #an "empty" tag
        tagname=thing.tagname
        dttag=tagreg.getTag(tagname)

        # Generate the meta-data first
        dttag.genMeta ( thing, meta )

        codeout.write(indent, '')
        codeout.write(indent, '#----------------------------------------')
        dttag.genCode(indent, codeout, tagreg, thing)
        codeout.write(indent, '#----------------------------------------')

class dummy: pass

def setup_h ( cur_h ):
    """
    Add some variables to our hidden namespace
    """
    cur_h.NEWOUTPUT = StringIO.StringIO
    if not hasattr(cur_h, 'OUTPUT'):
        cur_h.OUTPUT = cur_h.NEWOUTPUT()

    if not hasattr ( cur_h, 'VALFMTRGY' ):
        cur_h.VALFMTRGY = DTCommon.ValFmtRgy

def get_d():
    global cur_d
    if cur_d is None:
        cur_d=dummy()
    return cur_d

def checkName(tag, argname, val, ppval = None):
    """
    tag is the tag which we are currently on
    argname is the tag argument name
    val is the val after pyifyArg*
    ppval is optional and is the val before pyifyArg*

    The reason for ppval is that it is possible for checkname to succeed
    on a val of `"foo bar"` and `"foo" + foo + "bar"`
    """
    if ppval and ppval[0]==ppval[-1]=='`':
        raise DTExcept.DTCompileError(tag, ('argument %s is an expression'
                                            ' and should be a string')
                                      % argname)
    if len(val) and (val[0]==val[-1]=='"' or val[0]==val[-1]=="'"):
        return val[1:-1]
    raise DTExcept.DTCompileError ( tag, ('argument %s is an expression and '
                                          'should be a string') % argname)

def safe_import(indent, codeout, modulename):
    """
    imports (in the generated code) the stated module into the hidden
    namespace and returns a string that can be used to refer to it, of
    the form "__h.%s" % modulename.    
    """
    t="__h.%s" % modulename.split('.', 1)[0]
    codeout.write(indent, "%s=__import__('%s')" % (t, modulename))
    return "__h.%s" % modulename
