# $Id$
# Time-stamp: <2003-03-28 08:46:54 drew>

########################################################################  
#  Copyright (C) 2001 Jacob Smullyan <smulloni@smullyan.org>
#  
#      You may distribute under the terms of either the GNU General
#      Public License or the SkunkWeb License, as specified in the
#      README file.
#
import string, types

class SQLOperator:
    def asTuple(self):
        """
        returns a lisp-like nested tuple representation of the operator and its
        arguments, included nested operators.  The tuple is of the form (symbol, *args)
        """
        _astuple=lambda val: (isinstance(val, SQLOperator) and val.asTuple()) or val
        lst=[self.__class__.symbol]
        for v in self.values:
            lst.append(_astuple(v))
        return tuple(lst)
    
    def asSQL(self, fieldDict=None, conn=None):
        """
        this performs no escaping, as we don't necessarily know what the field
        or its type is in this context.  However, the use of type-specifier input
        classes, like FIELD, could ameliorate the problem to a degree.
        """
        _assql=lambda v: (isinstance(v, SQLOperator) and "(%s)" % v.asSQL()) \
                or (type(v) in (types.StringType, types.UnicodeType) and "'%s'" % v) or str(v)
        vallen=len(self.values)
        if vallen==1:            
            return "%s %s" % (self.__class__.symbol, _assql(self.values[0]))
        else:
            return (" %s " % self.__class__.symbol).join(map(_assql, self.values))

class MonadicOperator(SQLOperator):
    def __init__(self, val):
        self.values=(val,)
        
class DyadicOperator(SQLOperator):
    def __init__(self, lval, rval):
        self.values=(lval, rval)

class PolyadicOperator(SQLOperator):
    def __init__(self, *values):
        self.values=values

class FIELD:
    """
    a cheesy way of indicating that a string represents the
    name of a field, not a string literal
    """
    def __init__(self, fieldname):
        if type(fieldname)!=type(""):
            raise TypeError, "fieldname must be a string"
        self.fieldname=fieldname

    def __str__(self):
        return self.fieldname

    def __repr__(self):
        return "FIELD(%s)" % self.fieldname

class SET:
    """
    a cheesy way of passing a set into PyDO where clauses
    (for IN), e.g.:
    
    IN(FIELD('foo'), SET('spam', 'eggs', 'nougat'))
    """
    def __init__(self, *values):
        if not len(values):
            raise ValueError, "you must supply some values"
        self.values=tuple(values)
        
    def __str__(self):
        l=len(self.values)
        if l>1:
            return "(%s)" % ', '.join([self.__escape(x) for x in self.values])
        else:
            return "(%s)" % self.__escape(self.values[0])

    def __escape(self, thing):
        """
        this is somewhat inadequate, as it doesn't handle types
        beyond ints and strings; you'll need to perform your own
        escaping for dates and times (I can't tell what field is
        intended, whether you need a data or a time, etc.)
        """
        if type(thing) in (types.StringType, types.UnicodeType):
            return "'%s'" % string.replace(thing, "'", "\\'")
        return str(thing)
    
    def __repr__(self):
        return "SET(%s)" % self.__str__()

"""
mapping of symbols to operator classes
"""
symbol_table={}

def tupleToSQL(optuple):
    """
    takes the tuple notation, as produced by SQLOperator.asTuple(),
    and translates it into SQL
    """
    _assql=lambda v: (type(v)==type(()) and "(%s)" % tupleToSQL(v)) \
            or (type(v) in (types.StringType, types.UnicodeType) and "'%s'" % v) or str(v)
    lent=len(optuple)
    if lent<2:
        raise ValueError, "malformed input"
    if lent==2: # monadic
        return "%s %s" % (optuple[0], _assql(optuple[1]))
    elif lent>2: #dyadic or better
        return (" %s " % optuple[0]).join(map(_assql, optuple[1:]))

def tupleToSQLOperator(optuple):
    """
    inverse operator of SQLOperator.asTuple()
    """
    lent=len(optuple)
    if lent<2:
        raise ValueError, "malformed input"    
    sym=optuple[0]
    kl=symbol_table.get(sym)
    if not kl:
        raise ValueError, "symbol %s not recognized" % sym
    arglist=map(lambda x: (type(x)==type(()) and tupleToSQLOperator(x)) or x, optuple[1:])
    return kl(*arglist)

def __makeOperators():
    """
    generates the operator classes;
    more need to be added, here are some obvious ones
    """
    import new
    _factory=(  (  MonadicOperator,
                   ('NOT', '!'),
                   ),
                (  DyadicOperator,
                   ('EQ', '='),
                   ('NE', '!='),
                   ('LT', '<'),
                   ('LT_EQ', '<='),
                   ('GT', '>'),
                   ('GT_EQ', '>='),
                   ('LIKE', 'LIKE'),
                   ('IN', 'IN'),
                   ),
                (  PolyadicOperator,
                   ('AND', 'AND'),
                   ('OR', 'OR'),
                   ('PLUS', '+'),
                   ('MINUS', '-'),
                   ('MULT', '*'),
                   ('DIV', '/'),
                   )
                )
    for tup in _factory:
        base=tup[0]
        for specs in tup[1:]:
            klname, sym=specs
            kl=new.classobj(klname, (base,), {})
            kl.symbol=sym
            globals()[klname]=kl
            symbol_table[sym]=kl


            
########################################################################
            
__makeOperators()
del __makeOperators
        

