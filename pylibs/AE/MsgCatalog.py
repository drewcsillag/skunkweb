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
# $Id: MsgCatalog.py,v 1.4 2001/07/09 20:38:41 drew Exp $
# Time-stamp: <01/04/26 14:56:47 smulloni>
########################################################################

import re
import cfg
from SkunkExcept import SkunkStandardError

cfg.Configuration._mergeDefaultsKw(
    strictMessageCatalogs = 1,
    DefaultLanguage="eng"
    )

def getMessage(catalog,
               message,
               lang = cfg.Configuration.DefaultLanguage,
               fmt = lambda x: x,
               bindvars = {}):
    """
    A gentle getMessage function, to extract a message from a catalog
    """
    if isinstance(catalog, MultiLingualCatalog):
         return fmt(catalog.getMessage(message,
                                      lang = lang, 
                                      bindvars = bindvars))
    else:
        return fmt(catalog.getMessage(message,
                                      bindvars = bindvars))


class MessageCatalog:
    def __init__(self, dict, name):
        self._dict = dict
        self._name = name

    def msg (self,
             message,
             bindvars = {},
             fmt = lambda x:x,
             lang = None):
        return fmt(self.getMessage(message,
                                   bindvars = bindvars))
    
    def getMessage(self, name, bindvars = {}):
        """
        Retrieve a message by name
        """

        try: 
            msg = self._dict[name]
        except KeyError:
            if not cfg.Configuration.strictMessageCatalogs:
                msg = 'Error: no such message "%s" in catalog %s' % \
                      (name, self._name)
            else:
                raise SkunkStandardError, \
                      'no such message "%s" in catalog %s' % (
                          name, self._name)
        if not msg or len(bindvars) == 0:
            return msg
        else:
            return self._bind(msg, bindvars)

    def _bind (self, msg, bindvars):
        """
        Perform item substitution
        """
        regexes = {} 
        for k, v in bindvars.items():
            regexes[ re.compile('\[\[%s\]\]' % k) ] = str(v)

        for k, v in regexes.items():
            msg = k.sub ( v, msg )

        return msg

class MultiLingualCatalog(MessageCatalog):
    
    def msg (self,
             message,
             bindvars = {},
             fmt = lambda x:x,
             lang = cfg.Configuration.DefaultLanguage):

        return fmt(self.getMessage(message,
                                   lang = lang, 
                                   bindvars = bindvars))
    
    def getMessage(self, name, lang, bindvars = {}):
        """
        Retrieve a message by name and language
        """

        # fix: 'spa' maps to 'esp' language string,
        # but message catalogs  may not have 'spa'
        # string directly inside them
        if lang == 'spa': lang = 'esp'

        try:
            msg = self._dict[lang][name]
        except KeyError:
            if not cfg.Configuration.strictMessageCatalogs:
                msg = 'Error: no such message "%s" for language %s in ' \
                      'catalog %s' % ( name, lang, self._name )
            else:
                raise SkunkStandardError, \
                      'no such message "%s" for language %s in catalog %s' % \
                      ( name, lang, self._name)

        if not msg or len(bindvars) == 0:
            return msg
        else:
            return self._bind(msg, bindvars)

########################################################################
# $Log: MsgCatalog.py,v $
# Revision 1.4  2001/07/09 20:38:41  drew
# added licence comments
#
# Revision 1.3  2001/04/26 19:01:30  smullyan
# added DefaultLanguage to Configuration and fixed references to AED and
# SkunkStandardError in MsgCatalog
#
########################################################################
