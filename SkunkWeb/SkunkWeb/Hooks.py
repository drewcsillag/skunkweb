# Time-stamp: <03/05/02 13:39:12 smulloni>
# $Id: Hooks.py,v 1.9 2003/05/01 20:45:55 drew_csillag Exp $

########################################################################
#  
#  Copyright (C) 2001 Andrew T. Csillag <drew_csillag@geocities.com>
#  
#      You may distribute under the terms of either the GNU General
#      Public License or the SkunkWeb License, as specified in the
#      README file.
#   
########################################################################

from hooks import Hook, KeyedHook

ChildStart = Hook()
ServerStart = Hook()
