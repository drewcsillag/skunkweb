#  
#  Copyright (C) 2001 Andrew T. Csillag <drew_csillag@geocities.com>
#  
#      You may distribute under the terms of either the GNU General
#      Public License or the SkunkWeb License, as specified in the
#      README file.
#   
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

