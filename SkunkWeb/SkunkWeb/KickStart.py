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
# $Id: KickStart.py,v 1.1.1.1 2001/08/05 14:59:37 drew_csillag Exp $
# Time-stamp: <01/05/03 18:32:41 smulloni>
########################################################################

import ConfigLoader

CONFIG_MODULE='SkunkWeb.Configuration'

CONFIG_STRING="""
from SkunkWeb.ConfigAdditives import Location, Host, Port, Scope, IP, UNIXPath
from SkunkWeb.constants import *
"""

#preload the config namespace stuff
ConfigLoader.loadConfigString(CONFIG_STRING,
                              "<initconfig>",
                              CONFIG_MODULE)


########################################################################
# $Log: KickStart.py,v $
# Revision 1.1.1.1  2001/08/05 14:59:37  drew_csillag
# take 2 of import
#
#
# Revision 1.8  2001/07/09 20:38:40  drew
# added licence comments
#
# Revision 1.7  2001/05/04 18:38:53  smullyan
# architectural overhaul, possibly a reductio ad absurdum of the current
# config overlay technique.
#
# Revision 1.6  2001/05/03 16:14:59  smullyan
# modifications for scoping.
#
# Revision 1.5  2001/05/01 23:03:39  smullyan
# added support for name-based virtual hosts.
#
# Revision 1.4  2001/05/01 21:46:28  smullyan
# introduced the use of scope.Scopeable to replace the the ConfigLoader.Config
# object.
#
########################################################################
