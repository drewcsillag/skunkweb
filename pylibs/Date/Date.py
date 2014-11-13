#  
#  Copyright (C) 2001 Andrew T. Csillag <drew_csillag@geocities.com>
#  
#      You may distribute under the terms of either the GNU General
#      Public License or the SkunkWeb License, as specified in the
#      README file.
#   

import types
import string
import time

try:
    from mx import DateTime
except:
    import DateTime

try:
    from mx.DateTime import ISO
    _parseDate = ISO.ParseDateTime
except:
    import DateTime.ISO
    _parseDate = DateTime.ISO.ParseDateTime

from Format import isDateTime
from Format import DateString

# the date factory...

def _DateFactory(date=None, dtfunc=DateTime.localtime, convfunc=DateTime.utc2local):

    # shortcut for most common case, to minimize
    # time spent in this function...
    if date is None: return dtfunc()

    # else if an int or float, it's seconds since epoch.
    if type(date) in (types.IntType, types.FloatType):
	return dtfunc(date)
    
    # else if a DateTime, it's in the "wrong" (opposite)
    # timezone (local if we want UTC, and vice versa).
    # Use convfunc on it.
    elif isDateTime(date): return convfunc(date)

    # else we've got an ISO string on our hands. If a time
    # value is in string, it's assumed to be in GMT.
    # One may pass an offset a la +-0000 for conversion
    # of time value into GMT.

    elif type(date) == types.StringType:
	return _parseDate(date)

    # else date is garbage; ignore and return current date
    else: return dtfunc()

# Date generation functions
# for local time and for utc time

def LocalDate(date=None): 
    """
    This function returns a DateTime object 
    in UTC (GMT) time. You may pass the following 
    things as the date argument:
    
    a DateTime object: assumed to be a DateTime 
    object in local time. The function then 
    returns that date/time converted to UTC (GMT).

    a string specifying a date, like 
    '1999-11-14 23:43:01': 
    assumed to represent a UTC (GMT) date time 
    specification. 
    Function will parse the string into a UTC date, 
    and return that date. (That is, it won't do 
    any timezone conversion.) If the string does 
    not correspond to the ISO format 
    'YYYY-MM[-DD] [HH:MI[:SS]]', 
    a Date.DateFormatError exception 
    will be raised.

    an integer or float: assumed to be the Unix 
    "seconds since epoch" value. Function calls 
    DateTime.gmtime with this value, 
    which means that the int/float will be turned 
    into a DateTime object reflecting the UTC time.

    anything else: function ignores it, and 
    returns the current UTC (GMT) time as a 
    DateTime object.

    Please note that Date.UTCDate does not 
    accept timezone arguments for timezone conversion. 
    See the Date.Convert function to do 
    any timezone work.
    """
    """Date generation function for local time"""
    return _DateFactory(date)
Date = LocalDate

def UTCDate(date=None):
    """
    This function returns a DateTime object 
    in local time. You may pass the following things 
    as the date argument:

    a DateTime object: assumed to be a DateTime object in 
    UTC/GMT time. The function then returns that date/time 
    converted to machine local time.

    a string specifying a date, like 
    '1999-11-14 23:43:01': 
    assumed to represent a date time specification in 
    LOCAL time. (That is, it won't do any timezone conversion.) 
    Function will parse the string into a date in local time, 
    and return that date as a DateTime object. If the string 
    does not correspond to the format 
    'YYYY-MM[-DD] [HH:MI[:SS]]', 
    a Date.DateFormatError exception 
    will be thrown.

    an integer or float: assumed to be the Unix 
    "seconds since epoch" value (which is always in "UTC", 
    although you don't care). Function calls 
    DateTime.localtime with this value, 
    which means that the int/float will be turned into 
    a DateTime object in local time. If you want to take 
    the seconds since epoch value and turn it into a 
    UTC DateTime object, use UTCDate.

    anything else: function ignores it and returns 
    the current machine local time as a DateTime object.

    Please note that Date.LocalDate does not accept 
    timezone arguments for timezone conversion. 
    See Date.Convert instead.
    """
    return _DateFactory(date, DateTime.gmtime, DateTime.local2utc)

GMTDate = UTCDate

# the date formatter function is in
# DateFormat, but is imported into this namespace above.

# RelativeDateTimes to help trunc and round

_rd = DateTime.RelativeDateTime # name binding

_trunc_helpers = {
    'mi': _rd(second=0),
    'hh': _rd(minute=0, second=0),
    'dd': _rd(hour=0, minute=0, second=0),
    'mm': _rd(day=1, hour=0, minute=0, second=0),
    'yy': _rd(month=1, day=1, hour=0, minute=0, second=0)
}
_trunc_helpers['yyyy'] = _trunc_helpers['yy']

_round_helpers = {
    'mi': _rd(minutes=+1, second=0),
    'hh': _rd(hours=+1, minute=0, second=0),
    'dd': _rd(days=+1, hour=0, minute=0, second=0),
    'mm': _rd(months=+1, day=1, hour=0, minute=0, second=0),
    'yy': _rd(years=+1, month=1, day=1, hour=0, minute=0, second=0)
}
_round_helpers['yyyy'] = _round_helpers['yy']

_round_bounds = {
    'mi': ('second', 30), 
    'hh': ('minute', 30),
    'dd': ('hour', 12),
    'mm': ('day', 16), # cheesy Oracle bound for month-rounding
    'yy': ('month', 7),
    'yyyy' : ('month', 7)
}

# trunc()

def DateTruncate(date, unit='dd'):
    """
    Given a DateTime object, and a unit to truncate the
    date object to, a string that is one of:

    'mm', 'dd', 'yy', 'yyyy', 'hh', 'mi'
    
    it returns a new date object with the original
    date object's values "truncated" to the unit
    specified:
    
    trunc(Date('1999-03-24', 'mm') == Date('1999-03-01')
    
    unit is case-insensitive.
    """
    if not isDateTime(date):
	raise TypeError, "date %s is not a DateTime object" % date

    unit = string.lower(unit)

    # we handle 'ss' in this code...
    if unit != 'ss' and not _trunc_helpers.has_key(unit):
	raise ValueError, "Cannot truncate date to unit %s" % repr(unit)

    if unit == 'ss':
	return DateTime.DateTime(
		   date.year, date.month, date.day,
		   date.hour, date.minute, int(date.second)
	       )
    else:
        return date + _trunc_helpers[unit]

trunc = DateTruncate
DateTrunc = DateTruncate

# round()

def DateRound(date, unit='dd'):
    """
    Just like DateTruncate, but instead 
    "rounds" the date to the date unit specified.
    
    For compatibility with Oracle, month-rounding is handled
    in this abritrary manner:
    
    If the day is greater than the 15th, date rounds up.
    otherwise, date rounds down.
    
    Year-rounding is also Oracle-like: if month is less
    than 7, year rounds down.
    
    As with DateTruncate, the value of
    unit is case-sensitive.
    """
    if not isDateTime(date):
	raise TypeError, "Date %s is not a DateTime object" % date

    unit = string.lower(unit)

    # we handle 'ss' in this code...
    if not _trunc_helpers.has_key(unit):
	raise ValueError, "Cannot round date to unit %s" % repr(unit)

    if unit == 'ss':
	newsecs = int(date.second + .5)
	return DateTime.DateTime(
		   date.year, date.month, date.day,
		   date.hour, date.minute, newsecs
	       )

    else:
	bounder = _round_bounds[unit]
	if getattr(date, bounder[0]) < bounder[1]:
	    return date + _trunc_helpers[unit]
	else:
	    return date + _round_helpers[unit]

round = DateRound

