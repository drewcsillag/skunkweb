#  
#  Copyright (C) 2001 Andrew T. Csillag <drew_csillag@geocities.com>
#  
#      You may distribute under the terms of either the GNU General
#      Public License or the SkunkWeb License, as specified in the
#      README file.
#   
"""The main place to be if you want to use the DT library
"""
import sys
import types
import string
import copy

import DTParser
import DTLexer
import DTTags
import DTTagRegistry
import DTC
import DTExcept
import DTCompilerUtil
from SkunkExcept import *

class dummy:
    """not user servicable"""
    pass

# Types of template execution 
DT_REGULAR, DT_DATA, DT_INCLUDE = 0, 1, 2

class _current_tag_thingy:
    """no user servicable parts inside"""
    def __init__(self, tag, lineno):
        self.tag = tag
        self._name, self._lineno = tuple ( string.split ( lineno, ':' ))
    def lineno(self): return int(self._lineno)
    def name(self): return self._name
    def __str__(self): return self.tag
    def __repr__(self): return self.tag

def compileTemplate ( text, path, tag_registry = None ):
    """create a compiled STML template.

    parameters:
    
    text -- the text of the template
    path -- a name for the template (seen in tracebacks and
            the like)

    tag_registry -- a tag registry object -- if None
                    the default tag registry is used

    After the thing is built, call the produced DT object like a function
    whose arguments are:
    
    local_ns  -- the local namespace dictionary
    global_ns -- the global namespace dictionary
    hidden_ns -- the "hidden" namespace dictionary
    call_type -- one of:
        DT_REGULAR -- the default, a regular template
        DT_INCLUDE -- use parent namespace games
        DT_DATA    -- a data template, enable <:return:> tag
    """

    # Check that valid tag registry is passed
    if not isinstance ( tag_registry, DTTagRegistry.DTTagRegistry ):
        raise SkunkRuntimeError, 'valid tag registry needs to be supplied'

    # Meta data is a dictionary to keep it marshallable
    meta = {} 

    # Generate the python code
    progtext = DTC.compileTemplate ( text, path, tag_registry, meta )

    # Compile python code
    cobj = DTC.compileText ( progtext, path )

    return DT ( path, progtext, cobj, meta )

class DT:
    """
    class representing a template. Can be pickled up and used at a later
    date
    """
    def __init__ ( self, path, text, compiled, meta ):
        """
        Create the template object
        """

        self.path = path

        self._text, self._compiled, self._meta = text, compiled, meta

    def meta ( self ):
        """
        Get a handle on our meta-data
        """
        return self._meta

    def source(self):
        """Get the source for self"""
        return self._text

    def setError ( self, err ): 
        """These are to propagate error, if the real template failed to 
        compile and we're using a cached one to avoid blowing up the site
        """
        self._error_text = err

    def getError ( self ):
        return getattr ( self, '_error_text', None )

    def errorTag ( self ):
        """
        Returns the error tag, should be called in 'except...' clause
        """
        return getattr ( self, '_error_tag', None )

    def __store_ns(self, ns, env):
        for v in ('__t', '__h', '__d'):
            if ns.has_key(v):
                env[v]=ns[v]
                
    def __unstore_ns(self, ns, env):
        self.__store_ns(env, ns)

    def __call__(self, local_ns, global_ns, hidden_ns, 
                       call_type = DT_REGULAR ):
        """
        This function is called to actually evaluate the template
        """

        ns = local_ns
        temp_ns={}
        if call_type == DT_INCLUDE:
            # Store somewhere parent's stuff
            # this failed when trying to do an include call
            # from a top-level python document; now be a little
            # more careful
            #__t, __h, __d = ns['__t'], ns['__h'], ns['__d']
            self.__store_ns(ns, temp_ns)

        # 
        # Add our stuff to local namespace
        #
        ns['__t'] = dummy()                     # temporary var space
        _h = ns['__h'] = copy.copy(hidden_ns)   # hidden ns

        #ATC
        #_d = ns['__d'] = DTCompilerUtil.get_d() # debug info ns
        #/ATC
        
        _d = ns['__d'] = DTCompilerUtil.dummy()
        
        # Add our own stuff to global_ns
        DTCompilerUtil.setup_h ( _h )

        # Clear out current tag
        self._error_tag = None

        if call_type == DT_DATA:
            # We are called as data component, prepare return value
            ns['__return'] = None
            ns['__return_set'] = None

        # Does the finally: clause need to setup the current tag?
        _needs_tag = 1
        try:
            try:
                exec self._compiled in global_ns, ns
            except DTExcept.DTHaltError:
                # Set the error tag, just in case error occurs
                pass
            else:
                _needs_tag = 0
        finally:
            if _needs_tag:
                self._error_tag = _current_tag_thingy ( _d.CURRENT_TAG,
                                                        _d.CURRENT_LINENO )
            # Cleanup the local namespace
            for k in ( '__t', '__h', '__d' ):
                 del ns[k]
        
            if call_type == DT_INCLUDE:
                # Restore parent's stuff
                #ns['__t'], ns['__h'], ns['__d'] = __t, __h, __d
                self.__unstore_ns(ns, temp_ns)

        # Check the return value
        if call_type == DT_DATA:
             if not ns['__return_set']:
                 raise SkunkStandardError, \
                       'no <:return:> tag was found in a data component'

        if call_type == DT_DATA:
            return ns['__return']
        else:
            return _h.OUTPUT.getvalue()
