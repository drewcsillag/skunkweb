# Time-stamp: <02/02/10 16:32:19 smulloni>
# $Id: Hooks.py,v 1.8 2002/02/14 02:58:25 smulloni Exp $

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


########################################################################
# $Log: Hooks.py,v $
# Revision 1.8  2002/02/14 02:58:25  smulloni
# moved hooks into a pylib; added some logging to templating handler, and minor fix
# to web service.
#
# Revision 1.7  2001/09/19 02:11:52  smulloni
# fixed typo
#
# Revision 1.6  2001/09/09 02:37:41  smulloni
# performance enhancements, removal of sundry nastinesses and erasure of
# reeking rot.
#
# Revision 1.5  2001/08/27 18:37:05  drew_csillag
# Only
# put out DEBUG msg if DEBUGIT.
#
# Revision 1.4  2001/08/12 18:11:23  smulloni
# better fix to DEBUG import problem
#
# Revision 1.3  2001/08/12 01:35:31  smulloni
# backing out previous change, which broke everything
#
# Revision 1.2  2001/08/11 23:39:45  smulloni
# fixed a maladroit import-from inside a frequently called method
#
# Revision 1.1.1.1  2001/08/05 14:59:37  drew_csillag
# take 2 of import
#
#
# Revision 1.8  2001/07/09 20:38:40  drew
# added licence comments
#
# Revision 1.7  2001/04/10 22:48:30  smullyan
# some reorganization of the installation, affecting various
# makefiles/configure targets; modifications to debug system.
# There were numerous changes, and this is still quite unstable!
#
# Revision 1.6  2001/04/04 18:11:37  smullyan
# KeyedHooks now take glob as keys.  They are tested against job names with
# fnmatch.fnmatchcase.   The use of '?' is permitted, but discouraged (it is
# also pointless).  '*' is your friend.
#
# Revision 1.5  2001/04/04 14:46:31  smullyan
# moved KeyedHook into SkunkWeb.Hooks, and modified services to use it.
#
########################################################################
