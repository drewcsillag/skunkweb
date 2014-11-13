#  
#  Copyright (C) 2001 Jacob Smullyan <smulloni@smullyan.org>
#  
#      You may distribute under the terms of either the GNU General
#      Public License or the SkunkWeb License, as specified in the
#      README file.
#   
# Time-stamp: <01/05/04 13:41:40 smulloni>

import AE.Component
import types
import cPickle
import sys

def handleRequestHookFunc(requestData, sessionDict):
    if type(requestData)==types.TupleType and len(requestData)==5:
        return apply(AE.Component.fullCallComponent, requestData)
    else:
        raise TypeError, "inappropriate arguments for remote call"

def handleRequestFailedHookFunc(exc_text, sessionDict):
    excClass, excInstance=sys.exc_info()[:2]
    return cPickle.dumps((excClass, excInstance, exc_text))


########################################################################
# $Log: handler.py,v $
# Revision 1.3  2003/05/01 20:45:53  drew_csillag
# Changed license text
#
# Revision 1.2  2001/10/30 15:41:17  drew_csillag
# now returns the rendered and expired flags properly
#
# Revision 1.1.1.1  2001/08/05 15:00:05  drew_csillag
# take 2 of import
#
#
# Revision 1.7  2001/07/30 16:44:46  smulloni
# fixed remote services to work with changed API of AE.Component.
#
# Revision 1.6  2001/07/09 20:38:40  drew
# added licence comments
#
# Revision 1.5  2001/05/04 18:38:49  smullyan
# architectural overhaul, possibly a reductio ad absurdum of the current
# config overlay technique.
#
# Revision 1.4  2001/04/23 04:55:45  smullyan
# cleaned up some older code to use the requestHandler framework; modified
# all hooks and Protocol methods to take a session dictionary argument;
# added script to find long lines to util.
#
# Revision 1.3  2001/04/02 22:31:40  smullyan
# bug fixes.
#
# Revision 1.2  2001/04/02 00:54:16  smullyan
# modifications to use new requestHandler hook mechanism.
#
# Revision 1.1  2001/03/29 20:17:07  smullyan
# experimental, non-working code for requestHandler and derived services.
#
