######################################################################## 
#  Copyright (C) 2002 Jacob Smullyan <smulloni@smullyan.org>
#  
#      You may distribute under the terms of either the GNU General
#      Public License or the SkunkWeb License, as specified in the
#      README file.
######################################################################## 
import types

def extract_args(argsrc, *args, **kwargs):
    """
    extracts and returns a dictionary of the specified fields
    from argsrc.  args are argument names to look for; they
    will be placed in the dictionary unconverted, or None if not
    found.  The values for kwargs may be one of three forms:

      1. a default value (which must not be a sequence and not callable);
      2. a callable object, which will be taken to be a conversion function;
      3. a sequence of length one or two, the first item of which must
         be a callable and will be used as a conversion function, and the
         second item of which, if present, will be used as a default value.

    This is supposed to be equivalent to the <:args:> tag in STML.
    """

    d={}
    for i in args:
        d[i]=argsrc.get(i)
    for k, v in kwargs.items():
        #default=None
        if callable(v):
            converter=v
            default=None
        elif type(v) in (types.TupleType, types.ListType):
            vlen=len(v)
            if vlen not in (1, 2) or not callable(v[0]):
                raise ValueError, \
                      "inappropriate conversion/default specification: %s" % str(v)
            converter=v[0]
            if vlen==2:
                default=v[1]
            else:
                default=None
        else:
            default=v
            converter=None
        val=argsrc.get(k, default)
        if val != default and converter != None:
            try:
                d[k]=converter(val)
            except:
                d[k]=None
        else:
            d[k]=val
    return d
