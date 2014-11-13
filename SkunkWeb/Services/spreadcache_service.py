# Time-stamp: <03/04/15 00:23:55 smulloni>
# $Id: spreadcache_service.py 1722 2006-03-11 20:55:32Z smulloni $

########################################################################  
#  Copyright (C) 2003 Jacob Smullyan <smulloni@smullyan.org>
#  
#      You may distribute under the terms of either the GNU General
#      Public License or the SkunkWeb License, as specified in the
#      README file.
#
########################################################################

from SkunkWeb import Configuration
import spreadcache

Configuration.mergeDefaults(SpreadConnectParams={})

for alias, params in Configuration.SpreadConnectParams.items():
    spreadcache.initAlias(alias, **params)
