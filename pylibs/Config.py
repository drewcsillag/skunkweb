#  
#  Copyright (C) 2001 Andrew T. Csillag <drew_csillag@geocities.com>
#  
#      You may distribute under the terms of either the GNU General
#      Public License or the SkunkWeb License, as specified in the
#      README file.
#   
"""
An implementation of a general purpose 'Config' class. 
It can be used to store information pertinent to a 
configuration of any python executable.

Eventually, this module will have helper 
functions to assist parsing of 
configuration files, etc.
"""

import types
import string
import sys
import os

# Our modules
import LineWrap
import ErrorHandler
from SkunkExcept import *

# Load the logging functions
#try:
#    from AELogging import LOG,DEBUG,MEMDEBUG
#except ImportError:
#    from Logging import LOG,DEBUG
#    MEMDEBUG = lambda x:None

#
# Some useful hooks for assigning values to elements 
#
def file_path_hook ( el, v ):
    "This hook could be used to construct a list of directories"

    if type(v) == types.ListType:
        el._value = v
    elif type(v) == types.StringType:
        # Allow ':' separated entries, useful for command line
        el._value = map ( lambda p : os.path.abspath(p), 
                          string.split ( v, ':' ) )
    else:
        raise SkunkRuntimeError, \
              'element %s: invalid value for file_path_hook(): %s' % \
              (el.getName(), v)

# 
# This is a hook which assigns a value to a sub-config. Useful for setting
# command line parameters in core config
#
# Pass subconfig by name to avoid unnecessary object references
class assign_sub_config:
    def __init__(self, conf, subconf, elmt):
        self.subconf = subconf          # String name
        self.conf = conf                # Actual pointer to object
        self.elmt = elmt

    def __call__(self, el, v):
        # This creates a circular reference, which 
        # will need to be broken up
        self.conf._subconfigs[self.subconf][self.elmt] = v

# The exception we throw if cmdline parse is not successful
class ParseError ( SkunkRuntimeError ):
    pass

class Element:
    """
    This is an element that could be stored in a configuration class. 
    It is basically implemented to simplify command line parsing and to 
    enforce types on the configuration parameters

    The Element needs to be initialized with following values:

    Required:

    name              - the name of this config variable
    desc              - a short description of the variable
    value             - default value to set for this element

    Optional:

    short_op          - short options, suitable for getopt - like 'p', 'p:'
    long_op           - also for getopt, like 'port', 'port='
    value_name        - name to use for value in command line parameter
                        note that if it's given, the option is assumed to 
                        require a parameter, and not require one otherwise
    convert_hook      - the hook which is called to convert the (string?)
                        value of the option to whatever type it needs to 
                        be stored in. Most commonly just int() function
    assign_hook       - function to call when an element is assigned to. 
                        Function is called in the f ( el, val ) and 
                        return value is ignored
    readonly          - can be toggled to make element readonly after init
    firstpass         - internal switch, tells config module that this 
                        variable needs to be parsed first
    multi             - allow multiple arguments of given type on command line

    Examples:

    Element ( 'BindPort', 'the port to bind to', 9988,
              'p', 'port', 'port', convert_hook = int )
    """

    def __init__ ( self, name, desc, value, short_op = None, long_op = None, 
                        value_name = None, 
                        convert_hook = None, assign_hook = None, 
                        readonly = 0, subconfig_modify = 1,
                        firstpass = 0, multi = 0):
        # Just assign this stuff
        self._name, self._desc, self._value_name = name, desc, value_name
        self._short_op, self._long_op = short_op, long_op
        self._convert_hook, self._assign_hook = convert_hook, assign_hook

        self._readonly = 0

        # Basically, don't call any hooks at init() - it only makes it 
        # more complicated
        self._value = value

        self._readonly, self._firstpass = readonly, firstpass
        self._multi = multi

        # Just to avoid type errors later. Shouldn't be empty either
        if self._desc == None:
            self._desc = '<no description>'

        # Some sanity check, to remind people we're NOT getopt like options
        if self._short_op and len(self._short_op) > 1:
            raise ValueError, 'invalid short par "%s" given for variable %s' % \
                              ( self._short_op, self._name )

        if self._long_op and self._long_op[-1] == '=':
            raise ValueError, 'invalid long par "%s" given for variable %s' % \
                              ( self._long_op, self._name )

        # A flag indicating if elmt was set on cmd line
        self._cmdset = 0
        

    def __repr__ ( self ):
        "Print self in a debug like manner"
        return '%s = %s\n' % ( self._name, self._value )

    def setCmdLine ( self ):    self._cmdset = 1
    def isSetCmdLine ( self ):     return self._cmdset

    def setValue ( self, val ):
        "Set the value of this element"

        if self.isReadonly():
            # Complain a bit
            raise ValueError, 'assignment to readonly element'

        if self._assign_hook:
            # _assign_hook() overloads all
            try:
                self._assign_hook(self, val) 
            except SystemExit:
                # Some assign hooks could be used to indicate an exit,
                # like 'help' in command line options
                raise 
            except:
                raise SkunkRuntimeError, \
                     'error calling assign hook for config element %s : %s' % \
                     ( self._name, sys.exc_info()[1] )
        elif self._convert_hook:
            try:
                self._value = self._convert_hook ( val )
            except:
                raise SkunkRuntimeError, \
              'error calling convert function for config element %s : %s' % \
               ( self._name, sys.exc_info()[1] )
        else:
            # just assign it then
            self._value = val

    def getValue ( self ):              return self._value

    def getName ( self ):               return self._name

    def isReadonly ( self ):            return self._readonly

    def isMulti ( self ):               return self._multi

    def needsParm ( self ):             
        "Return true if option expects a parameter"

        return self._value_name != None

    def isCmdLine ( self ):
        "Return true if this option is command line configurable"

        if self._short_op or self._long_op:
            return 1
        else:
            return 0

    def paramDesc ( self ):
        "Return a string describing parameters for self"

        # Basically, return one of the following:
        # -x 
        # -x value
        # -x, --fullop=value
        # -x, --fullop
        if self.isCmdLine():
            return self._myJoin ( self.shortOp(1), self.longOp(1), ', ' )
        else:
            return ''

    def paramCmdLine ( self ):
        "return a string suitable for printing in Usage: line"

        # Like so:
        # -x
        # -x foo
        # -x foo | --extra=foo
        # -x | --extra
        if self.isCmdLine():
            return self._myJoin ( self.shortOp(1), self.longOp(1), ' | ' )
        else:
            return ''

    def _myJoin ( self, s1, s2, sep ):
        "My join"

        ret = ''
        if s1:
            ret = s1
        if s2:
            if ret:
                ret = ret + sep + s2
            else:
                ret = s2
        return ret

    def shortOp ( self, full = 0 ):
        "return the short option without the optional param char"
        if self._short_op:
            if full:  
                if self.needsParm():
                    return '-%s %s' % (self._short_op, self._value_name)
                else:
                    return '-%s' % (self._short_op)
            else:
                return self._short_op
        else:
            return None

    def longOp ( self, full = 0 ):
        "return the long option without the optional param char"
        if self._long_op:
            if full:
                if self.needsParm():
                    return '--%s=%s' % ( self._long_op, self._value_name )
                else:
                    return '--%s' % self._long_op
            return self._long_op
        else:
            return None


class Config:
    """
    This is the dictionary-like class, with functions for parsing the 
    command line, printing usage and reading config files. A config object
    is essentially a collection of elements which could be set via command
    line, config files or hard coded. 

    Each element could have a description, look for doc(ConfigElement) for 
    more info. Elements without description are free form and can be assigned
    in any way
    """
    def __init__ ( self, el_list, desc = None, exec_name = sys.argv[0],
                         fixed = 0, name = None):
        "Initialize self, giving description for each element."

        self._dict, self._fixed = {}, 0
        self._name = name

        for el in el_list:
            # Can't be too paranoid
            if type(el) != types.InstanceType and \
                                     not isinstance ( el, Element ):
                raise TypeError, 'instance of Element expected' 

            # Do some checks 
            self.addElement ( el )

        # Add a description for printing when doing usage()
        if desc:
            self._desc = string.replace ( desc, '\n', '' )
        else:
            self._desc = '<no description>'

        self._exec_name = exec_name
        
        # If fixed is set, we're not allowed to add any more elements
        self._fixed = fixed

        # This is a helper dictionary to assist cmd line parsing
        self._opts_set = {}

    def unload ( self ):
        """
        Break some references
        """
        for el in self._dict.values():
            el.__dict__.clear()

    def _element ( self, el ):
        """
        Allow people direct access to elements - discouraged generally
        """
        return self._dict[el]

    def usage ( self ):
        """Represent self in a manner suitable for printing during a 
        command line usage() function"""

        # See if there ARE any command line option
        opts = filter ( lambda x : x.isCmdLine(), self._dict.values() )

        # Be really fancy here - use LineWrap module, etc.
        maxwidth = 80

        ret = 'Usage: %s' % self._exec_name

        if not len(opts):
            # Just add description
            ret = ret + '\n\n%s' % self._desc
            return ret

        # XXX We should change this if we ever get to mutually exclusive /
        # cluster options
        opstr = string.join ( 
                 map ( lambda x : '[%s]' % x.paramCmdLine(), opts ), ' ' )

        pad = len(ret) + 1
        opstr = string.split(LineWrap.wraplines ( opstr, maxwidth - pad ), '\n')

        ret = ret + ' ' + opstr[0] + '\n';
        for l in opstr[1:]:
            ret = ret + ' ' * pad + l + '\n' 

        # Add description
        ret = ret + '\n' + self._desc + '\n'

        ret = ret + '\nCommand line options:\n\n'
        
        # First pass - find the maxlen of params 
        maxpar = max ( map (lambda x : len(x.paramDesc()), self._dict.values()))

        # Give an extra line for too long optional parameters
        if maxpar > 24:
            maxpar = 24 

        # Reserve some more chars 
        res = 6

        for el in opts:

            # LineWrap API changed, emulate old API
            desc = LineWrap.wraplines ( el._desc, maxwidth - maxpar - res )
            desc = string.split ( desc, '\n' )

            parDesc = el.paramDesc()

            if len(parDesc) > maxpar:
                ret = ret + ' %s\n' % parDesc 
                ret = ret + ' ' * (maxpar + res - 2) + '- '
            else:
                ret = ret + ' %s   - ' % string.ljust(parDesc, maxpar)

            ret = ret + desc[0] + '\n';

            for s in desc[1:]:
                ret = ret + ' ' * (maxpar + res) + s + '\n'

        return ret

    def optimize ( self ):
        """
        After the config is setup and is no longer mutable, this function 
        could be used to convert it to a plain dictionary - thus greatly
        speeding up lookups
        """
        ret = {}

        for k, el in self._dict.items():
            ret[k] = el.getValue()

        return ret

    def __repr__( self ):
        "Print self in a way suitable for debug"

        ret = 'Config: %s\n' % self._desc

        pad = '  '
        for el in self._dict.values():
            ret = ret + pad + repr ( el )

        return ret

    def __getitem__ ( self, k ):
        "Implement dictionary []"

        if not self._dict.has_key ( k ):
            raise AttributeError, '%s: no such config variable: %s' % \
                                  (self._name, k)

        return self._dict[k].getValue()

    def __setitem__ ( self, k, v ):
        "Implement dictionary [] set op"

        if not self._dict.has_key ( k ):
            # Create a new dictionary element
            self.addElement ( Element ( k, '<no description>', v ))
        else:
            self._dict[k].setValue ( v )

    def addElement ( self, el ):
        "Add an element, make sure he doesn't step on other's toes"

        if self._dict.has_key ( el.getName() ):
            raise ValueError, 'element %s already exists!' % el.getName()

        if self._fixed:
            raise SkunkRuntimeError, \
                     "attempting to add element '%s' to fixed config object"%\
                     el.getName()

        for l in self._dict.values():
            if l.shortOp() and el.shortOp() and \
               l.shortOp() == el.shortOp():
                raise ValueError, "element %s already defines option '%c'" % \
                                  (l.getName(), l.shortOp())
            elif l.longOp() and el.longOp() and \
               l.longOp() == el.longOp():
                raise ValueError, "element %s already defines option '%s'" % \
                                  (l.getName(), l.longOp())

            # Seems fine I guess...
        else:
            self._dict[el.getName()] = el

    # Parse command line. This function could be called to do complete command
    # line parsing. One can supply a hook function which will be called
    # between first and second pass of the command line arguments
    def parse ( self, args, hook = None ):
        """parse ( self, args, hook = None)
        
        Parse the command line arguments. If hook is callable call it between
        first and second passes

        On parse error, prints usage and exits

        Returns any arguments left after parsing
        """

        # Now, start parsing the command line arguments
        try:
            # First pass
            args = self._parseCmdLine ( args, firstpass = 1 )

            # Call the hook
            if callable(hook):
                hook(self)

            # Second pass
            args = self._parseCmdLine ( args )
        except ParseError:
            sys.stderr.write ( 'Error: %s\n' % sys.exc_info()[1] )
            sys.stderr.write ( self.usage() + '\n' )
            sys.exit(1)

        return args

    # Load a configuration from file 
    def loadFile ( self, fname, ns_dict = {}, chdir = 1 ):
        """Read the configuration file fname. Setup the variables
        
        nsdict contains additional variables to be put in config file's
        namespace when it is being evaluated
        
        If chdir is true, will add to syspath the directory where config file is
        prior to parsing it
        """

        # Search for the file in the pythonpath directory
        realfile = fname
        if not os.path.exists ( fname ) and not os.path.isabs ( fname ):
            for d in sys.path:
                realfile = os.path.join ( d, fname ) 
           
                if os.path.exists ( fname ):
                    break
            else:
                # To restore it back
                realfile = fname

        try:
            code = compile ( open(realfile).read(), fname, 'exec' )
        except SyntaxError, val:
            raise SkunkSyntaxError ( realfile, open(realfile).read(), val )
        except IOError: 
            raise SkunkStandardError, 'cannot read config file %s : %s' % \
                                      ( realfile, sys.exc_info()[1] )

        # Let's be nice to the config file - add the directory it's in to 
        # sys.path
        if chdir:
            _dir = os.path.dirname ( realfile )

            if _dir in sys.path:
                _dir = ''
            else:
                sys.path.insert(0, _dir)

        # Run the code in controlled namespace. Defined variables:
        # 
        # config - pointer to current configuration object
        # yes, no, true, false - various boolean values
        ns_dict['config'] = self

        for y in ( 'yes', 'true', 'YES', 'TRUE', 'Yes', 'True' ):
            ns_dict[y] = 1 
        for n in ( 'no', 'false', 'NO', 'FALSE', 'No', 'False' ):
            ns_dict[n] = 0

        ns = ns_dict.copy()

        try:
            exec code in ns
        except:
            trace = ErrorHandler.readError()

            raise SkunkStandardError, 'cannot parse config file %s :\n%s' % \
                                      ( realfile, trace )
        for k, v in ns.items():
            if type(v) not in (types.ModuleType, types.FunctionType) and \
               k not in [ '__builtins__' ] + ns_dict.keys() and k[0] != '_':
                # Check that it's not set on the command line
                if self.has_key(k) and self._dict[k].isSetCmdLine():
                    continue

                self[k] = v
                
        # Get rid of the _dir in path if we added it there
        if chdir and _dir:
            del sys.path[sys.path.index(_dir)]

        # Should be all done!

    # Make us REALLY look like a dictionary
    def items ( self ):
        return map ( lambda x: (x[0], x[1].getValue()), self._dict.items() )

    def has_key ( self, k ):
        return self._dict.has_key ( k )

    def values ( self ):
        return map ( lambda x: x.getValue(), self._dict.values() )

    # Command line parsing
    def setOpt ( self, el, val = None ):
        "Set the option. Either toggle it or set it"

        # sanity check, this should be taken care of already hence
        # raise ValueError
        if el.needsParm() and val == None:
            raise ValueError, "option '%s' requires parameter" % \
                              el.paramCmdLine()

        if not el.needsParm() and val:
            raise ValueError, "option '%s' does not require parameter" % \
                              el.paramCmdLine()

        if not el.isMulti() and self._opts_set.has_key ( el.getName() ):
            raise ParseError, "attempting to set option '%s' twice" % \
                              el.paramCmdLine()

        if not val:
            # Toggle boolean options
            val = 1

        el.setValue ( val )

        # Indicate that this parameter was set on the command line, so it 
        # is not overriden when we're reading config files
        el.setCmdLine()

    def _parseCmdLine ( self, args, firstpass = 0 ):
        """
        Parse the command line arguments
        """
        all_ops = filter ( lambda x : x.isCmdLine(), self._dict.values() )

        _fail = 0
        if firstpass: 
            ops = filter ( lambda x : x._firstpass, all_ops )
        else:
            _fail = 1
            ops = filter ( lambda x : not x._firstpass, all_ops )

        return self._parseOps ( args, ops, invalid_op_fail = _fail )

    def _parseOps ( self, args, ops, 
                    invalid_op_fail = 0):
        """
        This is the function which actually parses command line 
        arguments, kind of a replacement for python getopt() which 
        sucks ass anyway
        """

        # If nothing, return happily
        if not len(ops):
            return args

        # Create the dict of short options / long options
        shorts, longs = {}, {}

        for op in ops:
            if op.shortOp():
                shorts[op.shortOp()] = op

            if op.longOp():
                longs[op.longOp()] = op

        # Helper function
        is_op = lambda x : x[0] == '-'
        is_longop = lambda x : x[:2] == '--' 

        # Ok, start looking
        # Basically, we're only distinguishing the following cases:
        #
        # -x 
        # -x foo
        # -xfoo
        # --extra foo
        # --extra=foo
        outargs = []

        i = 0
        while i < len(args):
            this = args[i]
            if i < len(args) - 1:
                next = args[i+1]
            else:
                next = None

            # Should we copy it?
            copy = 0

            if is_op ( this ):
                if is_longop(this):
                    # Long option
                    vals = string.split(this[2:], '=')
                    if len(vals) > 1:
                        # Parameter supplied
                        op, val = vals
                    else:
                        op, val = vals[0], None

                    if op in longs.keys():
                        # Our option
                        el = longs[op]
                        if el.needsParm():
                            if not val and (not next or is_op(next)):
                                raise ParseError, \
                                      'option %s requires parameter' % \
                                      ( el.longOp(), )
                            self.setOpt ( el, val or next )
                            # Eat up next
                            if not val:
                                i = i + 1
                        elif val and not el.needsParm():
                            raise ParseError, \
                              'option %s does not require parameter' % \
                              el.longOp()
                        else:
                            # just toggle it
                            self.setOpt ( el )
                    elif invalid_op_fail:
                        raise ParseError, 'unknown option "%s"' % op
                    else:
                        # Copy to args list
                        copy = 1
                else: 
                    # Short option
                    #
                    # Allow -abc option style, plus if c requires a param
                    # -abcfoo == -ab -c foo
                    this = this[1:]             # Strip '-'
                    for idx in range ( 0, len(this) ):
                        op, rest = this[idx], this[idx+1:]
                
                        if op in shorts.keys():
                            # This is a short option, one of ours
                            el = shorts[op]

                            if el.needsParm():
                                if rest:
                                    self.setOpt ( el, rest )
                                elif next:
                                    self.setOpt ( el, next )
                                    i = i + 1
                                else:
                                    raise ParseError, \
                            "option '%s' requires parameter" % el.paramCmdLine()
                            else:
                                self.setOpt ( el )
                        elif invalid_op_fail:
                            raise ParseError, "invalid option '%s'" % op
                        else:
                            # Found unknown option, for safety just copy it 
                            # to output 
                            #
                            # XXX can screw up here, if non-first pass option
                            # is followed by first pass one - so don't do that!
                            outargs.append ( '-%s%s' % (op,rest) )
                            break
            else:
                copy = 1
            
            i = i + 1
            if copy:
                outargs.append ( this )

        return outargs

    #def __del__ ( self ):
    #    if MEMDEBUG:
    #        MEMDEBUG ( 'Config %s deleted' % self._name )
    #    pass

#
# Add ability to add sub-configs to the Config class
#
class ExtendedConfig ( Config ):
    """
    Implementaion of Config class which allows adding sub-configs to 
    the config class
    """

    def __init__ ( self, *args, **kwargs ):
        "Just call the higher level init"

        apply ( Config.__init__, (self,) + args, kwargs )
        
        self._subconfigs = {}

    def addSubConfig ( self, name, conf ):
        "Set a subconfig class"

        if self._subconfigs.has_key(name):
            raise AttributeError, 'subconfig %s already exists' % name

        self._subconfigs[name] = conf

    def __getattr__ ( self, attr ):
        "Give people access to our subconfig classes"

        if attr[0] == '_':
            raise AttributeError, 'cannot access attribute %s' % attr

        if not self._subconfigs.has_key(attr):
            raise AttributeError, 'no such subconfig: %s' % attr

        return self._subconfigs[attr]

    #def __del__ ( self ):
    #    "Just debugging"
    #    MEMDEBUG ( 'ExtendedConfig: instance deleted' )

    def unload ( self ):
        "Clean up some circular references that may exist"

        for sub in self._subconfigs.values():
            sub.unload()
            
        del self._subconfigs

        for el in self._dict.values():
            el.__dict__.clear()

#
# Make a shortcut for the element class
#
el = Element
