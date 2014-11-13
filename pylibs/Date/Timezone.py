#  
#  Copyright (C) 2001 Andrew T. Csillag <drew_csillag@geocities.com>
#  
#      You may distribute under the terms of either the GNU General
#      Public License or the SkunkWeb License, as specified in the
#      README file.
#   
"""
This module provides "timezone" objects 
which the Date module can use
when converting DateTime objects from one
time zone to another.

Timezone objects are used by Date.Convert 
to convert date/times between different timezones on Earth. 
Computers have had many different ways to specify 
timezone values; our Date module tries to 
accommodate them all.

First of all, let's start with the simplest 
kind of timezone, the offset: a number of 
hours/minutes ahead or behind of Universal Coordinated Time 
(UTC/GMT). These kinds of timezones are specified as strings, 
with the number of hours-then-minutes and a "-" for behind 
of UTC and a "+" (or nothing) for ahead of UTC:

"-0400" - 4 hours behind UTC
"+0100" - 1 hour ahead of UTC
"0230" - 2 hours, 30 minutes ahead of UTC
"-0000" or "+0000" - UTC

You can use strings like this with 
Date.Convert:

Date.Convert(date, to_zone="-0400", from_zone="-0000")

will add four hours to the DateTime object you pass in.

The other kind of timezone is the timezone object. 
It's not just an offset from UTC; it represents a set 
of rules on when to use daylight saving time and when not 
to use it. These timezones are actually Python objects, 
with methods available to determine if a date/time 
is in daylight savings or not, etc.

These timezone objects can be used directly, but it's more
common to specify them to Date.Convert by their name 
strings. A timezone object has many name strings, which
try to provide easy and expected names for the timezone
in all of the languages and naming systems we use. For example,
the timezone object for United States Eastern Time can be
identified by the following names:

'ET'
'Eastern'
'US/Eastern'
'USA Eastern'
'EEUU Este' 
'EUA Leste'
'us.fl'
'us.ny'

There is one "special" timezone name, and that is "LOCAL". 
If you specify the string "LOCAL" as the timezone, 
the Date module takes that to mean the machine's local 
timezone. (This may not be the same as your own personal 
local timezone, so be aware of which timezone your 
machine is set to.) "LOCAL" identifies a special LocalTimezone
object in the Timezone module, which handles conversions
gracefully to and from local machine time.

Daylight Savings Time

This module's timezone objects do support daylight savings
time, with some important restrictions. Daylight savings "rules"
are implemented in each TimezoneDST object, but there's only one set
of rules in each object, the most recent rules adopted by the timezone.
In the United States, the rules have been the same since the 1960s;
so the US-based timezone objects will handle daylight savings correctly
for any DateTime objects more recent than 1960 or so. Other timezones
have made recent changes to their rules or, worse yet, they change
their rules every year!

What this means to you, the practical programmer, is that 
this module guarantees correct daylight savings behavior only
for the current date/time on the machine. For other times, correct
behavior depends on when the timezone's rules have changed. Here is
a short guide to "daylight savings dependability" for different timezones:

USA timezones: all dates from Jan 1, 1970
Mexico timezones: all dates from Jan 1, 1990
Brazil timezones: all dates from Jan 1, 1998
Other Latin American timezones: all dates from Jan 1, 2000
"""

import types
try:
    from mx.DateTime import DateTimeDelta, RelativeDateTime, utc2local, local2utc, oneHour
except:
    from DateTime import DateTimeDelta, RelativeDateTime, utc2local, local2utc, oneHour
    
# "offset" handling functions
#
# offsets are the strings like "-0400" that are used
# in ISO date formats.
#
# It's not worth making Timezone objects for these,
# so we're using a regex instead, and Convert() does
# the heavy lifting.


import re
#from DateTime import oneHour

_offset_regex = re.compile(r'([+-]?)([01][0-9]|2[0-3])([0-5][0-9])')

# helper function for Convert, which takes the parts
# of the matched offset regex and makes a delta

def _make_offset_delta(tup):
    delta = DateTimeDelta(0, int(tup[1]), int(tup[2]))
    if tup[0] == '-': delta =  -1 * delta
    return delta

# Conversion function
#
# to_zone and from_zone accept either strings or 
# Timezone instances. IF strings, it checks if string
# is a GMT offset like '-0400'. If so, it handles it
# as a falt offset from GMT. If not, it looks it up
# with get_timezone(). get_timezone will throw
# a ValueError if it can't find the timezone at that point.
# 'LOCAL' will always find the special LocalTimezone object.

def Convert(date, to_zone='LOCAL', from_zone='LOCAL'):
    """
    Accepts a DateTime object in date, 
    converts it from the timezone indicated in 
    from_zone to the timezone indicated 
    in to_zone, and returns the converted 
    DateTime object. Note that from_zone 
    and to_zone default to the local timezone. 
    If you do this:

    Date.Convert(date)
    
    then no conversion will take place, and you will 
    receive the DateTime object unchanged.

    from_zone and to_zone 
    accept "timezone values" (see below), 
    which are any values that can accurately 
    describe a timezone. Note the special timezone values:

    "UTC" or "GMT": the UTC timezone
    "LOCAL": the local timezone
    
    Please read the Timezone documentation 
    about timezone objects!
    """
    # check if from_zone is an offset string
    # if so, set the conversion func to conv_from_offset.
    if type(from_zone) == types.StringType:
	mt =  _offset_regex.match(from_zone)
	if mt:
	    first = date - _make_offset_delta(mt.groups())
	else:
	    from_zone = get_timezone(from_zone)
	    first = from_zone.to_utc(date)
    else: first = from_zone.to_utc(date)

    if type(to_zone) == types.StringType:
	mt =  _offset_regex.match(to_zone)
	if mt:
	    second = first + _make_offset_delta(mt.groups())
	else:
	    to_zone = get_timezone(to_zone)
	    second = to_zone.from_utc(first)
    else: second = to_zone.from_utc(first)

    return second

# Daylight check function

def isDST(date, zone='LOCAL'):
    """
    Given a DateTime object in date, 
    and a timezone name, offset, or object in 
    zone, returns 1 or 0, whether 
    the date falls in daylight saving time 
    for that timezone.
    """
    if type(zone) == types.StringType:
	zone = get_timezone(zone)
    return zone.localdate_is_dst(date)

isDaylight = isDST

# timezone lookup dictionary

_tzdict = {}

# timezone lookup function
#
# Timezone objects aren't put in the module namespace,
# but are instead indexed bt strings in _tzdict.
# get_timezone(name) queries _tzdict, and raises
# its own, more meaningful error to the user if tz doesn't exist.

def get_timezone(name):
    """
    Given a timezone name, returns the corresponding
    Timezone object. If no object is available
    under this name, a ValueError is raised.
    """
    if not _tzdict.has_key(name):
	raise ValueError, "Timezone %s not valid" % repr(name)
    return _tzdict[name]

# timezone factory 
#
# instantiates Timezone objects and installs them in _tzdict.

def _make_timezone(klass, names, *dummy, **kwargs):
    tzobj = apply(klass, dummy, kwargs)
    for n in names: _tzdict[n] = tzobj

# ------------------------------------------------------
# TIMEZONE CLASSES
#
# these classes normalize the structure and interface
# of timezones. 

class Timezone:
    """Represents a "basic" timezone which does not implement
       daylight saving time. It still provides daylight-checking
       methods, however, which return 0."""

    def __init__(self, *dummy, **kwargs):
        """
        Timezone objects should only be instantiated
        by the Timezone module itself. Use the
        get_timezone function to get
        timezone objects.
        """
	for k, v in kwargs.items(): self.__dict__[k] = v

    def __setattr__(self, item, value):
	raise AttributeError, "Timezone objects are immutable"

    # attributes of any Timezone instance are not
    # publicly accessible. Use the method interface always.
    def __getattr__(self, item):
	raise AttributeError, item

    # timezones are equivalent iff their instance
    # dictionary's items() are equivalent. This is 
    # a shortcut (though not really a hack) that
    # allows for future changes to the attribute namespace
    # of Timezone instances. By design, Timezone instance
    # attributes are restricted to objects which determine
    # the timezone settings, nothing else. Thus this cmp
    # method woks like a charm.

    def __cmp__(self, other):
	# must be another Timezone instance
	if not isinstance(other, Timezone):
	    raise TypeError, \
	    "Timezone object %s can only be compared to other Timezone objects" \
	    % repr(self)
        # get both instance dicts items(), sorted.
	selfdict = self.__dict__.items()
	selfdict.sort()
	otherdict = other.__dict__.items()
	otherdict.sort()
	return cmp(selfdict, otherdict)

    def localdate_is_dst(self, date): 
        """
	Given a DateTime object, returns 1 or 0
	whether the date, if it were in the timezone
	in question, is daylight saving time.
	"""
        return 0
    def utcdate_is_dst(self, date): 
	"""
	Given a DateTime object, returns 1 or 0
	whether the date, expressed as a UTC date,
	would correspond to a date in this timezone
	which is daylight saving time.
	"""
	return 0
    def find_offset(self, date): 
	"""
	Returns a string with the offset from UTC
	for the DateTime object passed in date.
	Yes, this method obeys daylight saving time, and
	considers the date object passed to be expressed
	in the timezone in question.
	"""
	return self.__dict__['offset']
    def from_utc(self, date): 
	"""
	Given a DateTime object, it considers that
	date to be in UTC. Returns a DateTime object
	that is the UTC date converted to this timezone.
	"""
	return date + self.__dict__['offset_delta']
    def to_utc(self, date): 
	"""
	Given a DateTime object expressed as a date
	in this timezone, returns a DateTime object
	that is that date converted to UTC.
	"""
	return date - self.__dict__['offset_delta']

class TimezoneDST(Timezone):
    """
    Represents a timezone which implements daylight 
    saving time. Has the same interface as the
    Timezone class.
    """

    def localdate_is_dst(self, date):
        """
	Given a DateTime object, returns 1 or 0
	whether the date, if it were in the timezone
	in question, is daylight saving time.
	"""
	forward = date + self.__dict__['dst_forward'] + oneHour
	back = date + self.__dict__['dst_back'] - oneHour
	south = (forward > back)
	if south: return (date >= forward or date < back)
	else: return (date >= forward and date < back)

    def utcdate_is_dst(self, date):
	"""
	Given a DateTime object, returns 1 or 0
	whether the date, expressed as a UTC date,
	would correspond to a date in this timezone
	which is daylight saving time.
	"""
	forward = date - self.__dict__['offset_delta'] \
                  + self.__dict__['dst_forward'] #+ oneHour
	back = date - self.__dict__['dst_delta'] \
               + self.__dict__['dst_back'] #- oneHour
	# since we just subtracted offsets, 
	# the south rule is reversed
	south = (forward > back)
	if south: return (date >= forward or date < back)
	else: return (date >= forward and date < back)

    def find_offset(self, date):
	"""
	Returns a string with the offset from UTC
	for the DateTime object passed in date.
	Yes, this method obeys daylight saving time, and
	considers the date object passed to be expressed
	in the timezone in question.
	"""
	if self.localdate_is_dst(date): return self.__dict__['dst_offset']
	else: return self.__dict__['offset']

    def from_utc(self, date):
	"""
	Given a DateTime object, it considers that
	date to be in UTC. Returns a DateTime object
	that is the UTC date converted to this timezone.
	"""
	if not self.utcdate_is_dst(date):
	    return date + self.__dict__['offset_delta']
        else: return date + self.__dict__['dst_delta']

    def to_utc(self, date):
	"""
	Given a DateTime object expressed as a date
	in this timezone, returns a DateTime object
	that is that date converted to UTC.
	"""
	if not self.localdate_is_dst(date):
	    return date - self.__dict__['offset_delta']
        else: return date - self.__dict__['dst_delta']

class LocalTimezone(Timezone):
    """
    A special class, only to be instantiated once,
    which provides the Timezone structure and interface
    to the machine's local timezone. The methods
    merely pass through to localtime and other
    basic DateTime functions.

    The LocalTimezone instance will faithfully reflect
    changes that you make to the local timezone at 
    run-time, e.g. changing the TZ environment variable
    in Unix. Since the offset and dst_offset attributes
    are not directly accessible by the user, we don't
    have to set offset and dst_offset at __init__ time,
    as we do with all other Timezone instances.
    """

    def __init__(self, *ignore, **ignorekw): pass

    def localdate_is_dst(self, date):
        """
	Given a DateTime object, returns 1 or 0
	whether the date, if it were in the timezone
	in question, is daylight saving time.
	"""
	# get the ticks, then run it back through localtime()
	t = date.ticks()
	r = localtime(t).dst
	# if local time is DST-ignorant, the answer is false
	if r != -1: return r
	else: return 0

    def utcdate_is_dst(self, date):
	"""
	Given a DateTime object, returns 1 or 0
	whether the date, expressed as a UTC date,
	would correspond to a date in this timezone
	which is daylight saving time.
	"""
	# convert utc to local
	return self.localdate_is_dst( utc2local(date) )

    def find_offset(self, date): 
	"""
	Returns a string with the offset from UTC
	for the DateTime object passed in date.
	Yes, this method obeys daylight saving time, and
	considers the date object passed to be expressed
	in the timezone in question.
	"""
	# (Is this really necessary?)
	t = date.ticks()
	r = localtime(t).gmtoffset()
	# format the sucker
	return "%+03d%02d" % (r.hour, r.minute)

    def from_utc(self, date): 
	"""
	Given a DateTime object, it considers that
	date to be in UTC. Returns a DateTime object
	that is the UTC date converted to this timezone.
	"""
	return utc2local(date)

    def to_utc(self, date): 
	"""
	Given a DateTime object expressed as a date
	in this timezone, returns a DateTime object
	that is that date converted to UTC.
	"""
	return local2utc(date)

# the special *local* timezone. It's not a real timezone object.
# Instead, if someone specifies 'LOCAL' as the timezone in question,
# the top level functions in Date.py (Convert, isDST) play games
# with DateTime.localtime and such. See the Date.py file for details.

_make_timezone(
    LocalTimezone, ('LOCAL',),
)

# -------------------------------------------------
# STANDARD (NON-DAYLIGHT) TIMEZONES
# 
# The following timezones do not implement daylight
# saving time. Thus they are Timezone instances,
# and not TimezoneDST instances.

# good old UTC
_make_timezone(
    Timezone, ('UTC', 'GMT', 'UCT', 'Universal', 'Greenwich'),
    offset='-0000',
    offset_delta=DateTimeDelta(0,0,0)
)

# Argentina and Uruguay (GMT-3)
_make_timezone(
    Timezone, 
    ('Argentina', 'ar',
     'Uruguay', 'Uruguai', 'uy', 
    ),
    offset='-0300',
    offset_delta=DateTimeDelta(0,0,-180)
)

# GMT-4 for LatAms
_make_timezone(
    Timezone, 
    ('Bolivia', 'Bol\355via', 'bo',
     'Venezuela', 've',
     'Puerto Rico', 'Porto Rico', 'pr',
     # oh what the hell
     'USVI', 'vi',
    # 2000.12.05: DR gov, in face of protests, repealed
    # daylight time after just two months in effect 
    # (biz guys hated it). Back to -0400 GMT year round.
    'Dominican Republic', 'Rep\372blica Dominicana', 'do',
    ),
    offset='-0400',
    offset_delta=DateTimeDelta(0,0,-240)
)

# GMT-5 for LatAms
_make_timezone(
    Timezone, 
    ('Colombia', 'Col\364mbia', 'co',
     'Ecuador', 'Equador', 'ec',
     'Panama', 'Panam\341', 'pa',
     'Peru', 'Per\372', 'pe',
    ),
    offset='-0500',
    offset_delta=DateTimeDelta(0,0,-300)
)

# GMT-6 for LatAms
_make_timezone(
    Timezone, 
    ('Nicaragua', 'Nic\341ragua', 'ni', 
     'Costa Rica', 'cr',
     'El Salvador', 'sv',
     'Guatemala', 'gt',
     'Honduras', 'hn',
    ),
    offset='-0600',
    offset_delta=DateTimeDelta(0,0,-360)
)

# USA Arizona 
#
# (dumb, but I'm from Arizona, so I get to include it)

_make_timezone(
    Timezone, ('USA Arizona', 'EEUU Arizona', 'EUA Arizona', 'us.az'),
    offset='-0700',
    offset_delta=DateTimeDelta(0,0,-420)
)


# -------------------------------------------------
# DAYLIGHT SAVING TIMEZONES
#
# The following timezones implement daylight saving time.
# Their political DST rules are in the RelativeDateTime objects
# in dst_forward and dst_back.

# USA/Mexico Central
# 
# The "default" Mexico timezone.

_make_timezone(
    TimezoneDST, 
    ('CT', 'Central', 'US/Central', 'USA Central', 'EEUU Central', 
     'EUA Central', 'us.tx', 'us.il',
     'Mexico', 'M\351xico', 'Mexico Central', 
     'M\351xico Central', 'mx'),
    offset='-0600',
    offset_delta=DateTimeDelta(0,0,-360),
    dst_offset='-0500',
    dst_delta=DateTimeDelta(0,0,-300),
    dst_forward=RelativeDateTime(hour=2, minute=0, month=4, second=0, weekday=(6, 1)),
    dst_back=RelativeDateTime(hour=2, minute=0, month=10, second=0, weekday=(6, -1))
)



# USA Eastern

_make_timezone(
    TimezoneDST, 
    ('ET', 'Eastern', 'US/Eastern', 'USA Eastern', 'EEUU Este', 
     'EUA Leste', 'us.fl', 'us.ny'),
    offset='-0500',
    offset_delta=DateTimeDelta(0,0,-300),
    dst_offset='-0400',
    dst_delta=DateTimeDelta(0,0,-240),
    dst_forward=RelativeDateTime(hour=2, minute=0, month=4, second=0, weekday=(6, 1)),
    dst_back=RelativeDateTime(hour=2, minute=0, month=10, second=0, weekday=(6, -1))
)

# USA Mountain
# 
# Also Baja Sur in Mexico.

_make_timezone(
    TimezoneDST, 
    ('MT', 'Mountain', 'US/Mountain', 'USA Mountain', 
     'EEUU Monta\361a', 'EUA Montanha', 
     'Mexico BajaSur', 'M\351xico BajaSur', 'BajaSur',
     'Mexico Mountain', 'M\351xico Monta\361a'),
    offset='-0700',
    offset_delta=DateTimeDelta(0,0,-420),
    dst_offset='-0600',
    dst_delta=DateTimeDelta(0,0,-360),
    dst_forward=RelativeDateTime(hour=2, minute=0, month=4, second=0, weekday=(6, 1)),
    dst_back=RelativeDateTime(hour=2, minute=0, month=10, second=0, weekday=(6, -1))
)



# USA Pacific
#
# also includes Baja Norte in Mexico.

_make_timezone(
    TimezoneDST, 
    ('PT', 'Pacific', 'US/Pacific', 'USA Pacific', 'EEUU Pac\355fico', 
     'EUA Pacifico', 'us.ca', 
     'Mexico BajaNorte', 'M\351xico BajaNorte', 'BajaNorte',
     'Mexico Pacific', 'M\351xico Pac\355fico',),
    offset='-0800',
    offset_delta=DateTimeDelta(0,0,-480),
    dst_offset='-0700',
    dst_delta=DateTimeDelta(0,0,-420),
    dst_forward=RelativeDateTime(hour=2, minute=0, month=4, second=0, weekday=(6, 1)),
    dst_back=RelativeDateTime(hour=2, minute=0, month=10, second=0, weekday=(6, -1))
)

# Brazil
# 
# Brasil has other timezones, but nobody with a computer lives there. :)
# The country also hasn't fixed its DST rules, but instead "decrees" them
# every year. For 1999/2000, however, they have decreed Oct 3 and Feb 27,
# which happen to be the first Sunday and last Sunday of those months.
# So I'm going to guess that Brazil gets its act together and sticks
# with this rule in the future.

_make_timezone(
    TimezoneDST, 
    ('Brazil', 'Brasil', 'br'),
    offset='-0300',
    offset_delta=DateTimeDelta(0,0,-180),
    dst_offset='-0200',
    dst_delta=DateTimeDelta(0,0,-120),
    dst_forward=RelativeDateTime(hour=0, minute=0, month=10, second=0, weekday=(6, 1)),
    dst_back=RelativeDateTime(hour=0, minute=0, month=2, second=0, weekday=(6, -1))
)

# Chile
_make_timezone(
    TimezoneDST, 
    ('Chile', 'cl'),
    offset='-0400',
    offset_delta=DateTimeDelta(0,0,-240),
    dst_offset='-0300',
    dst_delta=DateTimeDelta(0,0,-180),
    dst_forward=RelativeDateTime(day=15, hour=0, minute=0, month=10, second=0, weekday=(6, 0)),
    dst_back=RelativeDateTime(day=15, hour=0, minute=0, month=3, second=0, weekday=(6, 0))
)


# Cuba
_make_timezone(
    TimezoneDST, 
    ('Cuba', 'cu'),
    offset='-0500',
    offset_delta=DateTimeDelta(0,0,-300),
    dst_offset='-0400',
    dst_delta=DateTimeDelta(0,0,-240),
    dst_forward=RelativeDateTime(day=20, hour=0, minute=0, month=3, second=0, weekday=(6, 0)),
    dst_back=RelativeDateTime(day=14, hour=0, minute=0, month=10, second=0, weekday=(6, 0))
)


# Paraguay
_make_timezone(
    TimezoneDST, 
    ('Paraguay', 'Paraguai', 'py'),
    offset='-0400',
    offset_delta=DateTimeDelta(0,0,-240),
    dst_offset='-0300',
    dst_delta=DateTimeDelta(0,0,-180),
    dst_forward=RelativeDateTime(day=1, hour=0, minute=0, month=10, second=0),
    dst_back=RelativeDateTime(day=1, hour=0, minute=0, month=4, second=0)
)



# Portugal
_make_timezone(
    TimezoneDST, 
    ('Portugal', 'pt'),
    offset='-0000',
    offset_delta=DateTimeDelta(0,0,0),
    dst_offset='+0100',
    dst_delta=DateTimeDelta(0,0,60),
    dst_forward=RelativeDateTime(hour=1, minute=0, month=3, second=0, weekday=(6, -1)),
    dst_back=RelativeDateTime(hour=1, minute=0, month=10, second=0, weekday=(6, -1))
)



# Spain
_make_timezone(
    TimezoneDST, 
    ('Spain', 'Espa\361a', 'Espanha', 'es'),
    offset='+0100',
    offset_delta=DateTimeDelta(0,0,60),
    dst_offset='+0200',
    dst_delta=DateTimeDelta(0,0,120),
    dst_forward=RelativeDateTime(hour=1, minute=0, month=3, second=0, weekday=(6, -1)),
    dst_back=RelativeDateTime(hour=1, minute=0, month=10, second=0, weekday=(6, -1))
)

# silly timezone dumping function

def timezones():
    """
    A reporting function which will
    return a list of descriptions of each
    Timezone objects available in this module.
    Each item in the returned list is a dictionary
    with the following entries:
    
    "names": a list of name strings which can identify the timezone
    "offset": the offset from UTC when daylight saving time is not in effect
    "dst_offset": the offset from UTC when daylight saving is in effect
    
    """

    tl = []
    rd = {}
    # I'm exploiting that timezones have unique id()
    # in the interpreter
    for k, v in _tzdict.items():
	# skip the local timezone
	if isinstance(v, LocalTimezone): continue
	key = hash( id(v) )
	if not rd.has_key(key):
	    rd[key] = (v, [k])
	else:
	    rd[key][1].append(k)

    for tz, names in rd.values():
	o = tz.__dict__['offset']
	if tz.__dict__.has_key('dst_offset'):
	    do = tz.__dict__['dst_offset']
	else: do = None
	tl.append( {'offset': o, 'dst_offset': do, 'names': names} )

    return tl

