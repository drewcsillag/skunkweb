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
# used to to natural comparisons - i.e. sorting with numbers in strings
# in a natural way (i.e. version sorting)
# based on strnatcmp.c from apache v2
import string

def isdigit(c):
    return (c is not None) and c in string.digits

def isspace(c):
    return (c is not None) and c in string.whitespace

def compare_right(a, b):
    #The longest run of digits wins.  That aside, the greatest
    #value wins, but we can't know that it will until we've scanned
    #both numbers to know that they have the same magnitude, so we
    #remember it in BIAS. */

    bias = 0
    for ca, cb in map(None, a, b):
        if ca is None or cb is None:
            return bias
        if not isdigit(ca) and not isdigit(cb):
            return bias
        elif not isdigit(ca):
            return -1
        elif not isdigit(cb):
            return +1
        elif ca != cb and not bias:
            bias = cmp(ca, cb)
    return bias

def strnatcmp0(a, b, fold_case):
    ai = bi = 0
    lena = len(a)
    lenb = len(b)
    while 1:
        if ai == lena:
            if bi == lenb:
                return 0
            else:
                return -1
        elif bi == lenb:
            return 1
        
        ca = a[ai]
        cb = b[bi]
        
        # skip over leading spaces or zeros 
        while isspace(ca) or ca == '0':
            ai = ai + 1
            if ai == lena:
                ca = None
            else:
                ca = a[ai]

        while isspace(cb) or cb == '0':
            bi = bi + 1
            if bi == lenb:
                cb = None
            else:
                cb = b[bi]

        # process run of digits 
        if isdigit(ca) and isdigit(cb):
            result = compare_right(a[ai:], b[bi:])
            if result != 0:
                return result

        if fold_case:
            ca = (ca is None) and None or string.upper(ca)
            cb = (cb is None) and None or string.upper(cb)
        
        if ca != cb:
            return cmp(ca, cb)

        ai = ai + 1
        bi = bi + 1

def strnatcmp(a, b):
    return strnatcmp0(a, b, 0)

def strnatcasecmp(a, b):
    return strnatcmp0(a, b, 1)

