#  
#  Copyright (C) 2001 Andrew T. Csillag <drew_csillag@geocities.com>
#  
#      You may distribute under the terms of either the GNU General
#      Public License or the SkunkWeb License, as specified in the
#      README file.
#   
# $Id: KickStart.py 1722 2006-03-11 20:55:32Z smulloni $
# Time-stamp: <01/05/03 18:32:41 smulloni>
########################################################################

import ConfigLoader

CONFIG_MODULE='SkunkWeb.Configuration'

CONFIG_STRING="""
from SkunkWeb.constants import *
from SkunkWeb.ConfigAdditives import *
"""

#preload the config namespace stuff
ConfigLoader.loadConfigString(CONFIG_STRING,
                              "<initconfig>",
                              CONFIG_MODULE)


########################################################################
# $Log: KickStart.py,v $
# Revision 1.4  2003/05/01 20:45:55  drew_csillag
# Changed license text
#
# Revision 1.3  2002/03/30 20:05:27  smulloni
# added Include directive for sw.conf; fixed IP bug (was being clobbered in sw.conf)
#
# Revision 1.2  2001/10/02 02:35:34  smulloni
# support for scoping on unix socket path; very serious scope bug fixed.
#
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
