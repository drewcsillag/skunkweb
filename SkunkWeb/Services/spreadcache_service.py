# Time-stamp: <03/04/15 00:23:55 smulloni>
# $Id: __init__.py,v 1.3 2002/01/13 20:12:20 smulloni Exp $

########################################################################  
#  Copyright (C) 2003 Jacob Smullyan <smulloni@smullyan.org>
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

from SkunkWeb import Configuration
import spreadcache

Configuration.mergeDefaults(SpreadConnectParams={})

for alias, params in Configuration.SpreadConnectParams.items():
    spreadcache.initAlias(alias, **params)
