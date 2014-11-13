#  
#  Copyright (C) 2001 Andrew T. Csillag <drew_csillag@geocities.com>
#  
#      You may distribute under the terms of either the GNU General
#      Public License or the SkunkWeb License, as specified in the
#      README file.
#   
# Time-stamp: <2001-04-24 17:11:43 drew>
########################################################################

"""
the base tag class and its principal subclasses
"""

import sys
from types import *
import types
import string
import DTLexer
import DTParser
import DTUtil
import DTCompilerUtil
import DTCommon
from SkunkExcept import *
import DTExcept
import re

ValFmtRgy=DTCommon.ValFmtRgy



class DTTag:
    """
    The base class of all Tags
    """
    def __init__(self, tagname, isempty=0, modules = []):
        self.tagname=tagname
        self.isempty=isempty

        # List of modules which need to be put into tag namespace
        self._modules = modules

    def parseBlock(self, text, taglist, start, tagreg, name):
        """
        should return node, last.  This is only called for
        non-empty tags
        """
        cur=start
        #create a new node
        n=DTParser.Node()
        #get current tag
        t=taglist[cur]
        #this is in case they started a block with the close tag (for whatever
        #reason)
        if t.isclose:
            raise DTExcept.DTCompileError( t, 'close tag out of context' )

        #add current tag to the node
        n.add(t)
        #while we haven't eaten the taglist
        while cur < (len(taglist)-1):
            cur=cur+1
            curtag=taglist[cur]
            if type(curtag)==types.StringType:
                n.add(curtag)
            else:
                #if it's our close tag, add it and return 
                if curtag.tagname == self.tagname and curtag.isclose:
                    n.add(curtag)
                    return n, cur

                #else it's not our tag so we pass it to the generic handler
                nodeortag, last=DTParser.genHandler(text, taglist, cur,
                                                    tagreg, name)
                n.add(nodeortag)
                cur=last

        raise DTExcept.DTCompileError ( t, 'unexpected EOF encountered '
                                        'parsing <:%s:> block' % self.tagname )

    def genMeta ( self, tag, meta ):
        """
        The tag should overload this function to put custom data in the 
        template's meta-data field during compile time. 'meta' is a namespace
        where data can be put
        """
        pass

    def genCode(self, indent, codeout, tagreg, thing):
        """
        indent is indentation level to be passed to codeout.write
        codeout is where we send the source code to
        tagreg is the tag registry
        thing is one of a string, a DTParser.Node, or a tag instance

        ****************************************
        NOTE! if this is a block tag (i.e. isempty = 0), genCode gets
        one more argument named meta which is the meta info about the
        document (currently only used for AE's <:compargs:> tag
        ****************************************
        """
        raise NotImplementedError

class DelTag(DTTag):
    def __init__(self, name = 'del'):
        """
        The <:del:> tag, to delete local variables
        """
        DTTag.__init__(self, name, isempty = 1)
        
    def genCode(self, indent, codeout, tagreg, tag):
        DTCompilerUtil.tagDebug(indent, codeout, tag)
        pargs=args=DTUtil.tagCall(tag, ['name'])
        args=DTCompilerUtil.pyifyArgs(tag, args)
        name = DTCompilerUtil.checkName(tag, 'name', args['name'],
                                        pargs['name'])
        codeout.write(indent, 'del %s' % name)

class ForTag(DTTag):
    def __init__(self, name = 'for'):
        """
        The <:for:> tag
        """
        DTTag.__init__(self, name, isempty = 0)
        
    def genCode(self, indent, codeout, tagreg, node, meta):
        tag=node.children[0]
        DTCompilerUtil.tagDebug(indent, codeout, tag)
        pargs=args=DTUtil.tagCall(tag, ['expr', ('name','"sequence_item"')])
        args=DTCompilerUtil.pyifyArgs(tag, args)

        name = DTCompilerUtil.checkName(tag, 'name', args['name'],
                                        pargs['name'])
        exprval=DTCompilerUtil.getTempName()

        codeout.write(indent, '%s = %s' % (exprval, args['expr']))
        codeout.write(indent, 'if %s:' % exprval)
        codeout.write(indent+4, 'for %s in %s:' % (name, exprval))
        #do main loop shit
        for i in node.children[1:-1]:
            if (type(i) == InstanceType
                and i.__class__ == DTLexer.DTToken
                and i.tagname == 'else'):
                break
            else:
                DTCompilerUtil.genCodeChild(indent+8, codeout, tagreg, i, meta)
        codeout.write(indent, 'else:')
        codeout.write(indent+4, 'pass')
        #do else clause
        on=0
        for i in node.children[1:-1]:
            if (type(i) == InstanceType
                and i.__class__ == DTLexer.DTToken
                and i.tagname == 'else'):
                on=1
            elif on:
                DTCompilerUtil.genCodeChild(indent+4, codeout, tagreg, i, meta)
        codeout.write(indent, 'del %s' % exprval)
        
class ValTag(DTTag):
    """the <:val:> tag"""
    def __init__(self):
        DTTag.__init__(self, 'val', isempty = 1)

    def genCode(self, indent, codeout, tagreg, tag):
        DTCompilerUtil.tagDebug(indent, codeout, tag)
        args=DTUtil.tagCall ( tag, ['expr',
                                  ('fmt', 'None'),
                                   ] )
        #expr = args['expr']
        args=DTCompilerUtil.pyifyArgs(tag, args)
        expr = args['expr']
        #if len(expr)>1 and expr[0]==expr[-1]=='`':
        #    expr=expr[1:-1]
        #elif len(expr)>1 and expr[0]==expr[-1]=='"':
        #    expr=expr[1:-1]
        #elif len(expr)>1 and expr[0]==expr[-1]=="'":
        #    expr=expr[1:-1]
        #else:
        #    pass #expr=exrepr(expr)
        
        codeout.write(indent, '__t.val = %s' % expr)

        codeout.write(indent, 'if __t.val is None:')
        codeout.write(indent+4, '__t.val = ""')
        codeout.write(indent, 'else:')
        codeout.write(indent+4, '__t.val = str(__t.val)')
        if args['fmt'] and args['fmt'][1:-1] not in \
	    ('None', 'plain', 'plaintext'):
            codeout.write(indent, 
                         '__t.val=__h.VALFMTRGY.get(%s, lambda x: x)(__t.val)'
                          % args['fmt'])
        codeout.write(indent, '__h.OUTPUT.write(__t.val)')
        codeout.write(indent, 'del __t.val')

class CallTag(DTTag):
    """the <:call:> tag. Used to call arbitrary python expressions"""
    def __init__(self):
        DTTag.__init__(self, 'call', 1)

    def genCode(self, indent, codeout, tagreg, tag):
        DTCompilerUtil.tagDebug ( indent, codeout, tag )
        pargs = args = DTUtil.tagCall(tag, [('expr', 'None')])
        args = DTCompilerUtil.pyifyArgs(tag, args)

        try:
            DTCompilerUtil.checkName(tag, 'expr', args['expr'], pargs['expr'])
        except:
            pass
        else:
            raise DTExcept.DTCompileError( tag, 'cannot call a string')

        stmt = args['expr'] + '\n'

        try:
            compile(stmt, stmt, 'exec')
        except SyntaxError:
            raise DTExcept.DTCompileError ( tag, 
                                  'syntax error in statement "%s"' % stmt )

        codeout.writemultiline(indent, stmt)
                      
class ContinueTag(DTTag):
    "just raises the continue exception on invocation"
    def __init__(self):
        DTTag.__init__(self, 'continue', isempty=1)

    def genCode(self, indent, codeout, tagreg, tag):
        DTCompilerUtil.tagDebug(indent, codeout, tag)

        args = DTUtil.tagCall ( tag, [] )

        codeout.write ( indent, 'continue' )

class BreakTag(DTTag):
    '''just raises the break exception on invocation'''
    def __init__(self):
        DTTag.__init__(self, 'break', isempty=1)
        
    def genCode(self, indent, codeout, tagreg, tag):
        DTCompilerUtil.tagDebug(indent, codeout, tag)
        args=DTUtil.tagCall(tag, [])
        codeout.write ( indent, 'break' )

class ElseTag(DTTag):
    """marker class for else tags"""
    def __init__(self):
        DTTag.__init__ ( self, 'else', isempty = 1, modules = [ DTExcept ] )

    def genCode ( self, indent, codeout, tagreg, tag ):
        """
        If we got here, we're out of context
        """
        DTCompilerUtil.tagDebug ( indent, codeout, tag )

        # Raise an exception
        DTExcept.raiseRuntime ( codeout, indent, 
                          '<:%s:> tag out of context' % self.tagname )
        
class ElifTag(DTTag):
    """marker class for elif tags"""
    def __init__(self):
        DTTag.__init__ ( self, 'elif', isempty = 1, modules = [ DTExcept ] )

    def genCode ( self, indent, codeout, tagreg, tag ):
        """
        If we got here, we're out of context
        """
        DTCompilerUtil.tagDebug ( indent, codeout, tag )
        DTExcept.raiseRuntime ( codeout, indent, 
                         '<:%s:> tag out of context' % self.tagname )

class IfTag(DTTag):
    """
    This is the implementation of an if statement
    """
    def __init__(self):
        DTTag.__init__(self, 'if', isempty = 0)

    def genCode(self, indent, codeout, tagreg, node, meta):
        iftag = node.children[0]
        DTCompilerUtil.tagDebug(indent, codeout, iftag)
        args = DTUtil.tagCall(iftag, ['expr'])
        args = DTCompilerUtil.pyifyArgs(iftag, args)

        codeout.write ( indent, 'if (%s):' % args['expr'])
        for i in node.children[1:-1]:
            #if not an else or elif tag and on is true, render the child
            if (type(i) != InstanceType or i.__class__ != DTLexer.DTToken
                or i.tagname not in ('else', 'elif')):
                DTCompilerUtil.genCodeChild ( indent + 4, codeout, tagreg, i,
                                              meta )
            else:
                if i.tagname == 'elif':
                    #
                    # XXX has to move to the elif tag genCode()!
                    #
                    args=DTUtil.tagCall ( i, ['expr'] )
                    args=DTCompilerUtil.pyifyArgs(i, args)
                    
                    codeout.write(indent, 'elif (%s):' % (args['expr']))
                    # XXX kind of sucks to do this after the elif statement
                    DTCompilerUtil.tagDebug(indent + 4, codeout, i)
                    codeout.write(indent+4, 'pass' )
                else: #tagname is else
                    codeout.write(indent, 'else:')
                    codeout.write(indent+4, 'pass')

class BoolTag(DTTag):
    """
    Boolean tag - similar to <expr> ? val1 : val2 in C
    """
    def __init__(self, name = 'bool', def_true = '', def_false = ''):
        DTTag.__init__(self, name, isempty = 1 )

        self._def_true, self._def_false = def_true, def_false

    def genCode(self, indent, codeout, tagreg, tag):
        DTCompilerUtil.tagDebug(indent, codeout, tag)
        args = DTUtil.tagCall(tag, ['expr', ('valTrue', self._def_true), 
                                            ('valFalse', self._def_false)],)
        args = DTCompilerUtil.pyifyArgs(tag, args)

        # Ok, write out the stuff
        codeout.write ( indent, 'if %s:' % args['expr'] )
        codeout.write ( indent+4, '__h.OUTPUT.write ( %s )' % args['valTrue'] )
        codeout.write ( indent, 'else:' )
        codeout.write ( indent+4, '__h.OUTPUT.write ( %s )' % args['valFalse'] )

class VardictTag(DTTag):
    """
    This is the implementation of the <:vardict:> tag, used to create 
    dictionaries from local namespace
    """
    def __init__(self):
        DTTag.__init__(self, 'vardict', isempty = 1)

    def genCode(self, indent, codeout, tagreg, tag):
        DTCompilerUtil.tagDebug(indent, codeout, tag)
        pargs = args = DTUtil.tagCall(tag, ['var'], 'plainArgs', 'kwArgs' )
        kwargs = DTCompilerUtil.pyifyArgs(tag, args['kwArgs'])
        args = DTCompilerUtil.pyifyArgs(tag, args)

        varname = DTCompilerUtil.checkName(tag, 'var', args['var'],
                                           pargs['var'])
        # First, generate the plain args
        out = []
        for _j in args['plainArgs']:
            out.append ( '"%s": %s' % ( _j, _j ) )

        codeout.write ( indent, '%s = { %s }' % ( varname,
                                                  string.join ( out, ', ' )) )

        # Now, add the keyword arguments
        codeout.write ( indent, '%s.update(%s)' % ( varname,
                                                    str(args['kwArgs']) ))

class WhileTag(DTTag):
    """
    This is the implementation of an while statement
    """
    def __init__(self):
        DTTag.__init__(self, 'while', isempty = 0)

    def genCode(self, indent, codeout, tagreg, node, meta):
        whiletag = node.children[0]
        DTCompilerUtil.tagDebug(indent, codeout, whiletag)
        args = DTUtil.tagCall(whiletag, ['expr'])
        args = DTCompilerUtil.pyifyArgs(whiletag, args)

        codeout.write ( indent, 'while (%s):' % args['expr'])
        for i in node.children[1:-1]:
            # Just generate the code
            DTCompilerUtil.genCodeChild ( indent + 4, codeout, tagreg, i, meta)

        # That's it
        
class GenericCommentTag(DTTag):
    """the <:comment:> tag"""
    def __init__(self, token):
        DTTag.__init__(self, token, isempty=0)

    def parseBlock(self, text, taglist, start, tagreg, name):
        cur=start
        n=DTParser.Node()
        t=taglist[cur]

        while cur < (len(taglist)-1):
            #basically, ignore tokens until we see <:/comment:>
            cur=cur+1
            curtagl=taglist[cur]
            if type(curtagl) == types.StringType:
                pass
            else:
                if curtagl.tagname == self.tagname and curtagl.isclose:
                    n.add(curtagl)
                    return n, cur
                else:
                    pass
        raise DTExcept.DTCompileError ( t, 'unexpected EOF encountered '
                                        'parsing <:%s:> block' % self.tagname )
                    
    def genCode(self, *args):
        pass

# Comment tags
class FullCommentTag ( GenericCommentTag ):
    def __init__(self):
        GenericCommentTag.__init__(self, 'comment')

class BriefCommentTag ( GenericCommentTag ):
    def __init__(self):
        GenericCommentTag.__init__(self, '#')
    
class RaiseTag(DTTag):
    """raise an error"""
    def __init__(self):
        DTTag.__init__(self, 'raise', isempty=1)

    def genCode ( self, indent, codeout, tagreg, tag ):
        DTCompilerUtil.tagDebug ( indent, codeout, tag )
        args=DTUtil.tagCall ( tag, [('exc', None)] )
        args=DTCompilerUtil.pyifyArgs(tag, args)
        tvar=DTCompilerUtil.getTempName()
        
        # Just do a regular python raise - you should know to raise instances
        # 
        # <:raise MyExcept('hello'):> works
        # <:raise MyExcept, 'hello':> doesn't
        # <:raise 'string exception':> works
	# <:raise:> by itself now re-raises exception properly
	if args['exc'] is None:
            codeout.write ( indent, 'import sys' )
            codeout.write ( indent, 'raise' )
	else:
            codeout.write ( indent, 'raise (%s)' % args['exc'] )

class ExceptTag(DTTag):
    """marker class for except tags"""
    def __init__(self):
        DTTag.__init__ ( self, 'except', isempty = 1, modules = [ DTExcept ] )

    def genCode ( self, indent, codeout, tagreg, tag ):
        """
        If we got here, we're out of context
        """
        DTCompilerUtil.tagDebug ( indent, codeout, tag )

        # Raise an exception
        DTExcept.raiseRuntime ( codeout, indent, 
                          '<:%s:> tag out of context' % self.tagname )

class FinallyTag(DTTag):
    """marker class for finally tags"""
    def __init__(self):
        DTTag.__init__ ( self, 'finally', isempty = 1, modules = [ DTExcept ] )

    def genCode ( self, indent, codeout, tagreg, tag ):
        """
        If we got here, we're out of context
        """
        DTCompilerUtil.tagDebug ( indent, codeout, tag )

        # Raise an exception
        DTExcept.raiseRuntime ( codeout, indent, 
                          '<:%s:> tag out of context' % self.tagname )
        
class TryTag(DTTag):
    def __init__(self):
        DTTag.__init__ ( self, 'try', isempty = 0 )

    def genCode(self, indent, codeout, tagreg, node, meta):
        tag=node.children[0]

        # Do the debug
        DTCompilerUtil.tagDebug(indent, codeout, tag)
        DTUtil.tagCall(tag,[])
        oldout=DTCompilerUtil.getTempName()

        #
        # First, determine if this is a 'try...finally' form
        #
        for i in node.children[1:-1]:
            if ( type(i) == InstanceType
                 and i.__class__ == DTLexer.DTToken 
                 and i.tagname in ( 'finally', )):
                has_finally = 1
                break
        else:
            has_finally = 0

        if has_finally:
            # This is a try...finally block
            codeout.write ( indent, 'try:')

            for i in node.children[1:-1]:
                if ( type(i) == InstanceType
                     and i.__class__ == DTLexer.DTToken
                     and i.tagname in ( 'else', 'except', 'finally' ) ):

                    if i.tagname in ( 'else', 'except' ):
                        # This is an error
                        raise DTExcept.DTCompileError ( i, 
                          'tag %s inside of a try...finally block' % str(i) )
                    else:            # i.tagname == 'finally':
                        codeout.write ( indent, 'finally:' )
                        codeout.write ( indent+4, '__d.FTAG=__d.CURRENT_TAG')
                        codeout.write ( indent+4,
                                        '__d.FLINENO=__d.CURRENT_LINENO')
                        DTCompilerUtil.tagDebug ( indent + 4, codeout, i)
                else:
                    DTCompilerUtil.genCodeChild(indent + 4, codeout, tagreg, i,
                                                meta)
            codeout.write( indent+4, '__d.CURRENT_TAG=__d.FTAG')
            codeout.write( indent+4, '__d.CURRENT_LINENO=__d.FLINENO')
            codeout.write( indent+4, 'del __d.FTAG, __d.FLINENO')
            #
            # Ok, we're done - return
            #
            return

        #
        # Store a reference to current output object. Basically, if an exception
        # occurs we kind of rollback to the point before the 'try' block
        #
        codeout.write ( indent, '%s = __h.OUTPUT' % oldout)
        codeout.write ( indent, '__h.OUTPUT=__h.NEWOUTPUT()')
        codeout.write ( indent, 'try:')

        waselse = 0
        wasexcept = 0

        for i in node.children[1:-1]:
            if ( type(i) == InstanceType
                 and i.__class__ == DTLexer.DTToken 
                 and i.tagname in ( 'else', 'except' )):
                if i.tagname == 'except':
                    # Get the arguments for the except clause
                    args = DTUtil.tagCall ( i, [('exc', 'None')] )
                    args = DTCompilerUtil.pyifyArgs(tag, args)

                    if args['exc'] != None:
                        codeout.write ( indent, 'except %s:' % args['exc'])
                    else:
                        codeout.write ( indent, 'except:' )

                    # Do the debugging
                    DTCompilerUtil.tagDebug ( indent + 4, codeout, i)
                        
                    # Restore the original output
                    codeout.write(indent + 4, '__h.OUTPUT = %s' % oldout)
                    codeout.write(indent + 4, 'del %s' % oldout)

                    wasexcept = 1
                else:      # i.tagname == 'else':
                    codeout.write ( indent, 'else:' )

                    DTCompilerUtil.tagDebug ( indent + 4, codeout, i)

                    # Print and restore the original output
                    codeout.write(indent+4, '%s.write(__h.OUTPUT.getvalue())' %
                                            oldout )
                    codeout.write(indent + 4, '__h.OUTPUT = %s' % oldout)
                    codeout.write(indent + 4, 'del %s' % oldout)

                    waselse = 1
            else:
                DTCompilerUtil.genCodeChild(indent + 4, codeout, tagreg, i,
                                            meta)

        if not wasexcept:
            raise DTExcept.DTCompileError ( tag, '<:try:> without <:except:>' )
            
        if not waselse:
            codeout.write(indent, 'else:')
            codeout.write(indent+4, '%s.write(__h.OUTPUT.getvalue())' % oldout)
            codeout.write(indent+4, '__h.OUTPUT = %s' % oldout)
            codeout.write(indent+4, 'del %s' % oldout)
        
class DefaultTag(DTTag):
    def __init__(self):
        DTTag.__init__(self, 'default', isempty=1)

    def genCode(self, indent, codeout, tagreg, tag):
        DTCompilerUtil.tagDebug(indent, codeout, tag)
        pargs=args=DTUtil.tagCall(tag, ['name', ('value', '""')])
        args=DTCompilerUtil.pyifyArgs(tag, args)
        name = DTCompilerUtil.checkName(tag, 'name', args['name'],
                                        pargs['name'])
        codeout.write(indent, 'try:')
        codeout.write(indent+4, '%s' % name)
        codeout.write(indent, 'except (NameError, AttributeError):')
        codeout.write(indent+4, '%s = %s' % (name, args['value']))
        codeout.write(indent, 'else:')
        codeout.write(indent+4, 'if %s is None:' % name)
        codeout.write(indent+8, '%s = %s' % (name, args['value']))
                      
        
class HaltTag(DTTag):
    def __init__(self):
        DTTag.__init__(self, 'halt', isempty = 1, modules = [ DTExcept ])

    def genCode(self, indent, codeout, tagreg, tag):
        DTCompilerUtil.tagDebug(indent, codeout, tag)
        args=DTUtil.tagCall(tag, [])

        # Generate a halt
        DTExcept.raiseHalt ( codeout, indent ) 

class SpoolTag(DTTag):
    _attend_to_comments = 0
    
    def __init__(self):
        DTTag.__init__(self, 'spool', isempty = 0)

    def genCode ( self, indent, codeout, tagreg, node, meta):
        tag = node.children[0]
        DTCompilerUtil.tagDebug(indent, codeout, tag)
        tagargs=['name']
        if self._attend_to_comments:
            tagargs.append(('comments', None))
        pargs = args = DTUtil.tagCall(tag, tagargs)
        args = DTCompilerUtil.pyifyArgs(tag, args)
        if self._attend_to_comments and args['comments'] is not None:
            self._testCommentLevel(indent, codeout, args['comments'])
            stuff=self._pushCommentLevel(indent, codeout, args['comments'])

        name = DTCompilerUtil.checkName(tag, 'name', args['name'],
                                        pargs['name'])
        
        oldout = DTCompilerUtil.getTempName()
        codeout.write(indent, '%s = __h.OUTPUT' % oldout)
        codeout.write(indent, '__h.OUTPUT=__h.NEWOUTPUT()')
        for i in node.children[1:-1]:
            DTCompilerUtil.genCodeChild(indent, codeout, tagreg, i, meta)
        codeout.write(indent, '%s = __h.OUTPUT.getvalue()' % name)
        codeout.write(indent, '__h.OUTPUT = %s' % oldout)
        codeout.write(indent, 'del %s' % oldout)
        if self._attend_to_comments and args['comments'] is not None:
            self._popCommentLevel(indent, codeout, *stuff)

    def _pushCommentLevel(self, indent, codeout, val):
        pass
    
    def _popCommentLevel(self, indent, codeout, *args):
        pass

    def _testCommentLevel(self, indent, codeout, commentLevel):
        pass

_splitter=re.compile(r', ?')

class ImportTag(DTTag):
    def __init__(self):
        DTTag.__init__ ( self, 'import', isempty=1,  
                         modules = [ string ] )
    def genCode(self, indent, codeout, tagreg, tag):
        DTCompilerUtil.tagDebug(indent, codeout, tag)
        oargs = args = DTUtil.tagCall(tag, ['module', ('items', 'None'),
                                            ('as', 'None')])
        args = DTCompilerUtil.pyifyArgs(tag, args)
        module = DTCompilerUtil.checkName(tag, 'module', args['module'],
                                          oargs['module'])

        if oargs['as'] != None:
            asname = DTCompilerUtil.checkName(tag, 'as', args['as'],
                                              oargs['as'])
            asStr = " as %s" % asname
        else:
            asStr = ''
            
        if oargs['items'] != None:
            items = DTCompilerUtil.checkName('import', 'items', args['items'],
                                             oargs['items'])
            # allow items to be separated by commas or spaces
            if ',' in items:
                formattedItems=','.join(_splitter.split(items))
            else:
                formattedItems=','.join(items.split())
            codeout.write(indent,
                          'from %s import %s%s' % (module,
                                                   formattedItems,
                                                   asStr))
        else:
            codeout.write(indent, 'import %s%s' % (module, asStr))

class SetTag(DTTag):
    def __init__(self):
        DTTag.__init__(self, 'set', isempty=1)

    def genCode(self, indent, codeout, tagreg, tag):
        DTCompilerUtil.tagDebug(indent, codeout, tag)
        pargs=args=DTUtil.tagCall(tag, ['name', 'value'])
        args=DTCompilerUtil.pyifyArgs(tag, args)
        name = DTCompilerUtil.checkName(tag, 'name', args['name'],
                                        pargs['name'])
        codeout.write(indent, '%s = (%s)' % (name, args['value']))

# Treat it like a comment at this level
class DocTag ( GenericCommentTag ):
    def __init__ ( self ):
        GenericCommentTag.__init__ ( self, 'doc' )

#class DummyTag(DTTag):
#    def __init__(self):
#        DTTag.__init__(self, 'dummy', isempty=1)
#
#    def genCode(self, indent, codeout, tagreg, tag):
#        DTCompilerUtil.tagDebug(indent, codeout, tag)
#        args=DTUtil.tagCall(tag, [], None, 'kw')
#        codeout.write(indent, 'testfunc(%s)' %
#                      DTCompilerUtil.pyifyKWArgs(args['kw']))

