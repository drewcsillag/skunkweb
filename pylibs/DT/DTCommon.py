#  
#  Copyright (C) 2001 Andrew T. Csillag <drew_csillag@geocities.com>
#  
#      You may distribute under the terms of either the GNU General
#      Public License or the SkunkWeb License, as specified in the
#      README file.
#   
import DTUtil
import urllib

ValFmtRgy={
    'plain': (lambda x: x),
    'plaintext': (lambda x: x),
    'base64': DTUtil.b64,
    'html': DTUtil.htmlquote,
    'htmlquote': DTUtil.htmlquote,
    'uri': urllib.quote,
    'url': urllib.quote,
    'uriquote': urllib.quote,
    'urlquote': urllib.quote,
    'latin': DTUtil.latinquote,
    'latinquote': DTUtil.latinquote,
    'fulluri': DTUtil.fullquote,
    'fullurl': DTUtil.fullquote,
}
