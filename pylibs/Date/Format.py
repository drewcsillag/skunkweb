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
# date format funclets

import types
import time
import string
import re
import DateTime
import Locales

# _DateFormatter is a class whose instances produce
# a string for a single date format string.
# for each 'format element' found in a format
# string, a _FormatElement instance is created.
# Then the main formatting function calls
# the format() method on the instance, and
# works with the result.

def isDateTime(x):
    return isinstance ( x, DateTime.DateTimeType )

class _FormatElement:

    def __init__(self, part):
        self.part = part

	# decide if element needs case considerations
	self.initcap = 0
	self.allcaps = 0
	self.lowercase = 0

	pl = string.lower(part)
        # is it allcaps?
	if part == string.upper(part):
	    self.allcaps = 1
	# else is it initcap? compare part to pl capitalized
        elif part == string.capitalize(pl):
	    self.initcap = 1
        # if not allcaps or initcap, we consider it lowercase,
	# even if it's in stuDlyCaPS
	else: self.lowercase = 1

        # link thyself to the proper rendering function
	# try it with the case as is, so that the uppercase
	# numeric formats will get their leading zeroes stripped
	func = _format_parts.get(part) or _format_parts.get(pl)
	if func is None:
	    raise ValueError, "'%s' not a valid date format element" % part
	# self.func will not be a bound method, just a func.
        self.func = func
	    
    def format(self, d, l):
	result = self.func(d, l)

	if self.allcaps:
	    result = string.upper(result)
	elif self.initcap:
	    result = string.capitalize(result)
	else:
	    result = string.lower(result)
        return result

_FormatElementCache = {}

def _GetFormatElement(eltname):
    if _FormatElementCache.has_key(eltname):
	return _FormatElementCache[eltname]
    else:
	elt = _FormatElement(eltname)
	_FormatElementCache[eltname] = elt
	return elt

# STRFTIME EQUIVALENCE
#
# For extra speed, we want a date format string to be implemented
# via time.strftime() if possible. A date format string is implementable
# in strftime() if the following conditions are met:
#
# - all of its format elements are present in _format_strftime_equiv
# - the Date.Locale object matches the machine locale
#   (until I figure out how to map Date.Locale to POSIX,
#   this means, "Date.Locale is English, and machine locale is English")
#   if any of the elements are locale-dependent
# - all of the format elements which are case-sensitive
#   are in lowercase (because strftime formatting does 
#   not allow playing with case)

# the format of the values in this dict are 3-tuples:
#    (strftime format, is_locale_dependent, is_case_sensitive)
#
# The values for case-sensitive, if true, mean as follows:
#
#  'allcaps': element will have a leading zero 
#             or be uppercase in strftime,
#             and that is only correct iff element is ALLCAPS
#
#  'initcap': element will generate an initcapped string in
#             strftime, and that is correct iff element is Initcap
#
#  'lowercase': element will be a lowercase string in strftime,
#               only correct iff element is not initcap or ALLCAPS

_format_strftime_equiv = {
   'dd': ('%d', 0, 'lowercase'),
   'dy': ('%a', 1, 'initcap'),
   'day': ('%A', 1, 'initcap'),
   'mm': ('%m', 0, 'lowercase'),
   'mon': ('%b', 1, 'initcap'),
   'month': ('%B', 1, 'initcap'),
   'yy': ('%y', 0, 'lowercase'),
   'yyyy': ('%Y', 0, 'lowercase'),
   'hh12': ('%I', 0, 'lowercase'),
   'hh24': ('%H', 0, 'lowercase'),
   'hh': ('%H', 0, 'lowercase'),
   'mi': ('%M', 0, 'lowercase'),
   'min': ('%M', 0, 'lowercase'),
   'ss': ('%S', 0, 'lowercase'),
   'am': ('%p', 1, 'lowercase'),
   'pm': ('%p', 1, 'lowercase'),
}

# RENDERING FUNCTION DICTIONARY
# A dictionary to look up rendering functions for different 
# date format parts. Note that the keys are all in lowercase;
# thus any code using this dictionary must convert the date format
# part to lowercase before trying the lookup.

_format_parts = {}

# RENDERING FUNCTIONS
#
# These functions server to render a "part" of a date format
# for a particular date, in a linguistic locale and for a 
# particular timezone. Each function takes two arguments:
# d, the Date object; and l, the locale object.
#
# The names of these functions coincide with the names of the
# date format parts: __dd() is the function for 'dd', etc.
#
# If you want to add a new date format part, write its rendering function
# below to accept the same three arguments. Have it return a string, always.
# Make it a lambda of three arguments if at all possible.
#
# Then add a mapping entry (or entries) to _format_parts, as below, 
# for all of the
# lowercase strings that indicate the part. (For instance, both "hh" and
# "hh24" indicate the 24-hour hour element. 'hh24' gets a lambda assigned
# to it, and then 'hh' gets the same lambda.
#
# Special note on numeric format elements: the convention here
# is that if the format is allcaps, e.g. 'MM', then leading zeroes
# are preserved. If the format is not allcaps, then leading zeroes
# are stripped. If you add a numeric format element, add one
# lambda for the allcaps name and have it preserve leading zeroes.
# Then add another in lowercase that does not preserve the zeroes.

_format_parts['DD'] = lambda d,l: '%i' % d.day
_format_parts['dd'] = lambda d,l: '%02i' % d.day
_format_parts['dy'] = lambda d,l: l.DayAbbr[d.day_of_week]
_format_parts['day'] = lambda d,l: l.Day[d.day_of_week]
_format_parts['MM'] = lambda d,l: '%i' % d.month
_format_parts['mm'] = lambda d,l: '%02i' % d.month
_format_parts['mon'] = lambda d,l: l.MonthAbbr[d.month]
_format_parts['month'] = lambda d,l: l.Month[d.month]
_format_parts['YY'] = lambda d,l: '%i' % (d.year % 100)
_format_parts['yy'] = lambda d,l: '%02i' % (d.year % 100)
_format_parts['YYYY'] = lambda d,l: '%i' % d.year
_format_parts['yyyy'] = lambda d,l: '%04i' % d.year
_format_parts['HH12'] = lambda d,l: '%i' % (d.hour - ( (d.hour > 12) * 12 ) + ( (d.hour == 0) * 12 ) )
_format_parts['hh12'] = lambda d,l: '%02i' % (d.hour - ( (d.hour > 12) * 12 ) + ( (d.hour == 0) * 12 ) )
_format_parts['HH24'] = lambda d,l: '%i' % d.hour
_format_parts['hh24'] = lambda d,l: '%02i' % d.hour
_format_parts['HH'] = _format_parts['HH24']
_format_parts['hh'] = _format_parts['hh24']
_format_parts['MI'] = lambda d,l: '%i' % d.minute
_format_parts['mi'] = lambda d,l: '%02i' % d.minute
_format_parts['MIN'] = _format_parts['MI']
_format_parts['min'] = _format_parts['mi']
_format_parts['SS'] = lambda d,l: '%i' % d.second
_format_parts['ss'] = lambda d,l: '%02i' % d.second
_format_parts['am'] = lambda d,l: '%s' % l.AmPm[ ( d.hour >= 12 ) ]
_format_parts['pm'] = _format_parts['am']

# ORDER OF DATE FORMAT PARTS
#
# make a list of the format names, and sort them
# by longest to shortest

_format_elts = _format_parts.keys()
_format_elts.sort( lambda x, y: cmp(len(y), len(x)) )

# REGULAR EXPRESSION TO RECOGNIZE A DATE FORMAT PART
# the monster regex made of all format elements

_format_rex = re.compile(
    r'(?xi)' +    # a verbose regex, and case insensitive
    r'(' +       # start of group
    string.join(_format_elts, '|') + # all format elts in big OR group
    r')'
    )
    
# DATE FORMAT "COMPILATION" FUNCTION
#
# _match_elements() takes a string, which ostensibly contains
# a date format. The function decomposes the string into a list
# of date format parts (_FormatElement instances) and filler strings.
# Example:
#
# 'hey dd' -> ['hey ', <_FormatElement for 'dd'>]

def _match_elements(origst):
    result = []
    start = 0
    end = len(origst)
    match = _format_rex.search(origst, start)
    while match:
	mstart = match.start()
	mend = match.end()
        snippet = origst[start:mstart]
	if snippet: result.append(snippet)
	result.append( _GetFormatElement(origst[mstart:mend]) )
	start = mend
        match = _format_rex.search(origst, start)
    tail = origst[start:end]
    if tail: result.append(tail)
    return result


# the date formatter.
# here's the real _DateFormatter class...

class _DateFormatter:
    """
    _DateFormatter is a class whose instances produce
    a string for a single date format string.
    for each 'format element' found in a format
    string, a _FormatElement instance is created.
    Then the main formatting function calls
    the format() method on the instance, and
    works with the result.

    This is an internal class only. Users
    of the Date formatting functions don't
    need to mess with this.
    """
    def __init__(self, format):
        self.format_list = _match_elements(format)
	# perform a check for strftime equivalence.
	self.check_for_strftime()

    def check_for_strftime(self):
	strf = []
	# fse is shorthand
	fse = _format_strftime_equiv
        # for each element in list...
	for elt in self.format_list:
	    # if string, escape any % signs
	    if type(elt) == types.StringType:
	        strf.append( string.replace(elt, '%', '%%') )
	    # else _FormatElement...
	    else:
	        # if not lowercase, will not be in fse dict
		# if not in fse dict, bail
		lowerpart = string.lower(elt.part)
		if not fse.has_key(lowerpart): return
		strfmt, locsens, casesens = fse[lowerpart]
		# if casesensitive, use the fact that
		# casesens values correspond to boolean
		# attribute names in _FormatElement
		if casesens and not getattr(elt, casesens): return
		# append value in _format_strftime_equiv
		strf.append( strfmt )

        # if we got here, the format has a strftime equivalent.
	# put the strftime format in the object
	self.strftime = string.join(strf, '')

    # RENDERING METHOD
    #
    # Function takes a list of _FormatElements and filler strings,
    # plus a date object, plus optional locale and timezone objects,
    # and constructs a string representation of the date in the locale
    # and timezone according to the _FormatElements and filler strings.

    def format(self, date, locale=Locales.English):
        """
        Function takes a list of _FormatElements and filler strings,
        plus a date object, plus optional locale and timezone objects,
        and constructs a string representation of the date in the locale
        and timezone according to the _FormatElements and filler strings.
        """
	# strftime shortcut, if locale is English
	if locale == Locales.English and hasattr(self, 'strftime'):
	    return time.strftime(self.strftime, date.tuple())
	result = []
	for elt in self.format_list:
	    if type(elt) == types.StringType: result.append(elt)
	    else: result.append( elt.format(date, locale) )

	return string.join(result, '')

# since _DateFormatter objects are more or less immutable,
# it's best to make only one instance per unique format string.
# The dict below caches _DateFormatter objects for easy use
# by _MakeDateFormat().

_FormatterCache = {}

# the format factory; use to make your own formatter libraries

def _MakeDateFormat(format):
    """the format factory; use to make your own formatter libraries"""
    if type(format) != types.StringType:
	raise 'DateFormatStringIsNotStringError', format
    if not _FormatterCache.has_key(format):
        fmter = _DateFormatter(format)
	_FormatterCache[format] = fmter
	return fmter
    else: return _FormatterCache[format]

# the default iso format

_iso_format = _MakeDateFormat('yyyy-mm-dd hh24:mi:ss')

DEFAULT_FORMAT = 'yyyy-mm-dd hh24:mi:ss'


# the format function used by Date module as DateString

def DateString(date, format=_iso_format, lang='eng'):
    """
    Function accepts a DateTime object in date, and a 
    date format string in format. format
    defaults to an ISO standard format "yyyy-mm-dd hh:mi:ss".

    The string may contain any combination of the 
    following format elements. Anything not recognized 
    as a format is included in the output as static text:
    
    Element      Meaning
    ----------   --------------
    yyyy         four-digit year
    yy           two-digit year
    mm           two-digit month
    dd           two-digit day
    hh24         24-hour hour
    hh12         12-hour hour
    hh           equivalent to hh24
    mi or min    minutes
    SS           seconds

    For all of the above, leading zeroes are included 
    as necessary: "01" instead of 1, etc. However, 
    if the format element is in UPPERCASE, leading zeroes 
    are not included: "MM" -> "1", "mm" -> "01".
    
    Element    Meaning
    ---------  ------------------------
    mon        abbreviated name of month
    month      full name of month
    dy         abbreviated weekday name
    day        full weekday name
    am or pm   whether time is AM or PM
    
    For all of the above, if the element is in UPPERCASE, 
    the result will be in ALL CAPS: "MONTH" -> "JANUARY". 
    If the element is Initcap, the result will be initcapped: 
    "Month" -> "January". Any other combination of case will 
    be considered lowercase: "month" or "moNth" -> "january".
    """
    if not isDateTime(date):
	raise 'CannotDateFormatNonDateError', date

    elif not isinstance(format, _DateFormatter):
	if type(format) != types.StringType:
	    raise 'DateFormatStringIsNotStringError', format
        format = _MakeDateFormat(format)

    locale = Locales.lang_lookup(lang)

    return format.format(date, locale)

#
# A helper function to return date in RFC 1123 format, suitable
# for using in 'Last-Modified' like fields
#
# XXX Modified to return a string, and take seconds only - for performance
# considerations inside AED
def HTTPDate ( secs ):
    """
    Returns a DateString object with format set to RFC 1123,
    for use by code needing to return dates in the format expected
    in email, web, or other net-based formats. This format corresponds
    to the Unix strftime format: 
    '%a, %d %b %Y %H:%M:%S GMT'
    This function is used by the SkunkWeb server to make
    date strings extra quickly.
    """
    return time.strftime ('%a, %d %b %Y %H:%M:%S GMT' , time.gmtime ( secs ))
