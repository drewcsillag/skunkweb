#  
#  Copyright (C) 2001 Andrew T. Csillag <drew_csillag@geocities.com>
#  
#      You may distribute under the terms of either the GNU General
#      Public License or the SkunkWeb License, as specified in the
#      README file.
#   
# ----------------------------------------------------------------
# string8859
#
# $Id: string8859.py,v 1.1.1.1 2001/08/05 15:00:23 drew_csillag Exp $
#
# ----------------------------------------------------------------
"""
This module provides functions identical to those found in
the Python string module, except that this module's
functions handle properly the accented characters in the 
ISO-8859-1 character set used for Western European languages
(including English).
"""

import string
import types

# stuff to strip accents

# note: 0x9f (159) is a Windows cheat...value not used in 8859-1
# (still supported to make things symmetrical; no harm done)
# (fyi: it's the capital Y with umlaut)

# accented upper character map range
_aur = range(192,198) + range(199,215) + range(216,222) + [159]

# accented lower character map range
_alr = range(224,230) + range(231,247) + range(248,254) + [255]

# these join the above into strings, for use with maketrans()
_accented_upper = string.join(map((lambda x: chr(x)), _aur), '')
_accented_lower = string.join(map((lambda x: chr(x)), _alr), '')

# these are for use with maketrans() as well
_convert_upper  = 'AAAAAACEEEEIIII' + 'DNOOOOOOUUUUYY'
_convert_lower  = 'aaaaaaceeeeiiii' + 'dnoooooouuuuyy'

# lower to upper mapping for non-accented characters
_uppercase = string.uppercase
_lowercase = string.lowercase

# the translation tables

_accent_transtable = string.maketrans(_accented_upper + _accented_lower,
                                      _convert_upper + _convert_lower)

_lower_transtable = string.maketrans(_accented_upper + _uppercase,
                                     _accented_lower + _lowercase)

_upper_transtable = string.maketrans(_accented_lower + _lowercase,
                                     _accented_upper + _uppercase)

_swap_transtable = string.maketrans(_accented_lower + _lowercase + 
                                    _accented_upper + _uppercase,
                                    _accented_upper + _uppercase + 
				    _accented_lower + _lowercase)

# regexes to help us

import re

_NONALPHA_REGEX = re.compile('\W+')
_LEADSCORE_REGEX = re.compile('^_+')
_TRAILSCORE_REGEX = re.compile('_+$')

# coercion func to handle null object attributes
# of value None...

def _coerce(str):
    if type(str) == types.NoneType: return ''
    else: return str

# the following are just like string.* functions

def lower(str):
    """
    Returns the string in lowercase, honoring
    accents.
    """
    str = _coerce(str)
    return string.translate(str, _lower_transtable)

def upper(str):
    """
    Returns the string in uppercase,
    honoring accents.
    """
    str = _coerce(str)
    return string.translate(str, _upper_transtable)

def swapcase(str):
    """
    Returns a string with each letter converted to
    the opposite case. Accents are honored.
    """
    str = _coerce(str)
    return string.translate(str, _swap_transtable)

def capitalize(str):
    """
    Returns the string with the first
    character converted to uppercase. If the 
    character is not a letter, the string is returned
    unchanged. Accents are honored.
    """
    str = _coerce(str)
    if not len(str): return str
    first = str[0]
    rest = ''
    if len(str) > 1: rest = str[1:]
    return upper(first) + rest

def capwords(str):
    """
    Like capitalize, but capitalizes
    all words. As a side effect, leading and trailing
    whitespace characters are removed in the returneD
    string.
    """
    str = _coerce(str)
    words = string.split(string.strip(str))
    new = []
    for word in words:
	new.append(capitalize(word))
    return string.join(new)

# the following are new functions...


def initcap(str):
    """
    Works like Oracle's initcap: suppresses
    all words to lowercase, then capitalizes
    the first character of each word. As a side
    effect, leading and trailing whitespace are
    removed in the returned string.
    """
    str = _coerce(str)
    return capwords(lower(str))

def unaccent(str):
    """
    Strips accents off accented characters.
    Does not change case, nor alter any other "non-alpha"
    characters.
    """
    str = _coerce(str)
    return string.translate(str, _accent_transtable)


def clean(str):
    """
    The function that SMN should have used
    to make "clean" StarNombres. This function
    strips accents from characters, converts
    all characters to lowercase, removes leading
    and trailing whitespace and undersscores, and then converts
    each sequence of non-alpha ([^a-z0-9_]) characters
    to a single '_'.

    Note that multiple underscores are also
    condensed to a single underscore if they occur
    inside the string. So the string 
    "__du_$_de__"
    is changed to "dude" by this function.
    """
    str = _coerce(str)
    clean = string.strip(lower(unaccent(str)))
    clean = _NONALPHA_REGEX.sub('_', clean)
    clean = _LEADSCORE_REGEX.sub('', clean)
    clean = _TRAILSCORE_REGEX.sub('', clean)
    return clean

