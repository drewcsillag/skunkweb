# Time-stamp: <02/02/10 16:32:19 smulloni>
# $Id: Hooks.py,v 1.7 2001/09/19 02:11:52 smulloni Exp $

########################################################################
#  
#  Copyright (C) 2001 Andrew T. Csillag <drew_csillag@geocities.com>
#  
#      This program is free software; you can redistribute it and/or modify
#      it under the terms of the GNU General Public License as published by
#      the Free Software Foundation; either version 2 of the License, or
#      (at your option) any later version.
#  
#      This program is distributed in the hope that it will be useful,
#      but WITHOUT ANY WARRANTY; without even the implied warranty of
#      MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#      GNU General Public License for more details.
#  
#      You should have received a copy of the GNU General Public License
#      along with this program; if not, write to the Free Software
#      Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111, USA.
#   
########################################################################

from hooks import Hook, KeyedHook

ChildStart = Hook()
ServerStart = Hook()


########################################################################
# $Log: Hooks.py,v $
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
