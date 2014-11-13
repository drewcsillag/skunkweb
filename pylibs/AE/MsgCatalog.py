#  
#  Copyright (C) 2001 Andrew T. Csillag <drew_csillag@geocities.com>
#  
#      You may distribute under the terms of either the GNU General
#      Public License or the SkunkWeb License, as specified in the
#      README file.
#   
# Time-stamp: <01/04/26 14:56:47 smulloni>
########################################################################

import re
import cfg
from SkunkExcept import SkunkStandardError

cfg.Configuration.mergeDefaults(
    strictMessageCatalogs = 1,
    DefaultLanguage="eng"
    )

class NO_DEFAULT: pass

def getMessage(catalog,
               message,
               lang = cfg.Configuration.DefaultLanguage,
               fmt = lambda x: x,
               bindvars = {},
               default=NO_DEFAULT):
    """
    A gentle getMessage function, to extract a message from a catalog
    """
    if isinstance(catalog, MultiLingualCatalog):
        if not default is NO_DEFAULT:
            if not catalog.hasMessage(message, lang):
                return default
        return fmt(catalog.getMessage(message,
                                      lang = lang, 
                                      bindvars = bindvars))
    else:
        if not default is NO_DEFAULT:
            if not catalog.hasMessage(message):
                return default
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

    def hasMessage(self, name):
        return self._dict.has_key(name)
    
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

    def hasMessage(self, name, lang):
        return self._dict.has_key(lang) and \
               self._dict[lang].has_key(name)
    
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
# Revision 1.4  2003/05/01 20:45:58  drew_csillag
# Changed license text
#
# Revision 1.3  2003/04/19 14:19:35  smulloni
# changes for scopeable
#
# Revision 1.2  2002/07/15 15:07:11  smulloni
# various changes: configuration (DOCROOT); new sw.conf directive (File);
# less spurious debug messages from rewrite; more forgiving interface to
# MsgCatalog.
#
# Revision 1.1.1.1  2001/08/05 15:00:37  drew_csillag
# take 2 of import
#
#
# Revision 1.4  2001/07/09 20:38:41  drew
# added licence comments
#
# Revision 1.3  2001/04/26 19:01:30  smullyan
# added DefaultLanguage to Configuration and fixed references to AED and
# SkunkStandardError in MsgCatalog
#
########################################################################
