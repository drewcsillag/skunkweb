#  Copyright (C) 2001, 2003 Andrew T. Csillag <drew_csillag@geocities.com>,
#      Jacob Smullyan <smulloni@smullyan.org>
#  
#      You may distribute under the terms of either the GNU General
#      Public License or the SkunkWeb License, as specified in the
#      README file.
   
"""miscellaneous time routines.  This module is an update of
   Date.TimeUtil for Python 2.2 or later.  mx.DateTime is no longer
   required, but if available it will correctly process DateTime
   objects.  dateutil relativedelta objects are also accepted.  The
   facilities of dateutil and mx.DateTime are used, if available, in
   that order of preference, and implementions solely in terms of the
   time module are also available."""


try:
    from mx import DateTime
    _have_mx=1
except ImportError:
    _have_mx=0

try:
    import datetime
    _have_datetime=1
except ImportError:
    _have_datetime=0
    _have_dateutil=0
else:
    try:
        import dateutil
        from dateutil.relativedelta import relativedelta
        from dateutil.parser import parse as _parse_dateutil
        _have_dateutil=1
    except ImportError:
        _have_dateutil=0

try:
    basestring
except NameError:
    _have_basestring=0
else:
    _have_basestring=1

def _is_stringish(s):
    if _have_basestring:
        return isinstance(s, basestring)
    else:
        return isinstance(s, str) or isinstance(s, unicode)

import sys
import time

import re

class TimeException(Exception):
    pass

class PastTimeException(TimeException):
    pass

def _is_mx_DateTime(x):
    return _have_mx and isinstance(x, DateTime.DateTimeType)

def _is_mx_RelativeDateTime(x):
    return _have_mx and isinstance(x, DateTime.RelativeDateTime)

def _is_dateutil_relativedelta(x):
    return _have_dateutil and isinstance(x, relativedelta)

def _is_datetime_datetime(x):
    return _have_datetime and isinstance(x, datetime.datetime)

def _to_ticks(x):
    if x is None:
        return time.time()
    if isinstance(x, int) or isinstance(x, float):
        return x
    if _is_mx_DateTime(x):
        return x.ticks()
    if _is_datetime_datetime(x):
        return time.mktime(x.timetuple())
    raise ValueError, "unrecognized type: %s" % x

def convertDuration(duration, curdate=None):
    """
    >>> import time; t=time.time()
    >>> convertDuration("1h", t)==t+3600
    True
    """
    return timeConv(duration) + _to_ticks(curdate)

def convertUntil(until, curdate=None):
    curdate=_to_ticks(curdate)

    # if until is a DateTime object, consider it to be in local server
    # time, and return the ticks.
    if _is_mx_DateTime(until):
        result = until.ticks()
        
    # elif a RelativeDateTime, add it to the current date
    elif _is_mx_RelativeDateTime(until):
	result = (DateTime.DateTimeFromTicks(curdate)+until).ticks()

    # elif a dateutil relativedelta, add to current date
    elif _have_dateutil and isinstance(until, relativedelta):
        result = time.mktime((until+datetime.datetime.fromtimestamp(curdate)).timetuple())
        
    # elif until is a single string, let untilString handle it.
    elif _is_stringish(until):
	result = untilString(until, curdate)
        
    # elif a list or tuple of items, run convertUntil on each, take
    # the minimum value in the result list, and return that.
    elif isinstance(until, list) or isinstance(until, tuple):
	lowres = None
	for i in until:
	    thisone = convertUntil(i, curdate)
	    if lowres is None or thisone < lowres:
		lowres = thisone
        result = lowres

    else:
        raise TimeException, until

    if result < curdate:
        raise PastTimeException, until
    return result

# helper re's for untilString

_min_after_hour = re.compile(r'^:\d{2}$')
_timespec       = re.compile(r'^\d{2}:\d{2}(:\d{2})?$')
_old_datespec   = re.compile(r'^\d{2}/\d{2}/\d{4} \d{2}:\d{2}:\d{2}$')
_nice_datespec  = re.compile(r'^\d{4}-\d{2}-\d{2}( \d{2}:\d{2}(:\d{2})?)?$')

_digits = '0123456789'

def _until_timespec_dateutil(curticks, hr, min, sec):
    """
    >>> t=time.strptime('200212312359', '%Y%m%d%H%M')
    >>> u=_until_timespec_dateutil(time.mktime(t), 4, 20, 32)
    >>> time.ctime(u)
    'Wed Jan  1 04:20:32 2003'
    """
    reldate=relativedelta(hour=hr, minute=min, second=sec)
    curdate=datetime.datetime.fromtimestamp(curticks)
    huh=curdate+reldate
    if huh <= curdate:
        huh=huh+relativedelta(days=1)
    return time.mktime(huh.timetuple())

def _until_timespec_mx(curticks, hr, min, sec):
    """
    >>> t=time.strptime('200212312359', '%Y%m%d%H%M')
    >>> u=_until_timespec_mx(time.mktime(t), 4, 20, 32)
    >>> time.ctime(u)
    'Wed Jan  1 04:20:32 2003'
    """    
    reldate=DateTime.RelativeDateTime(hour=hr, minute=min, second=sec)
    curdate=DateTime.DateTimeFromTicks(curticks)
    huh=curdate+reldate
    if huh <= curdate:
        huh=huh+1
    return huh.ticks()    

def _until_timespec_vanilla(curticks, hr, min, sec):
    """
    >>> t=time.strptime('200212312359', '%Y%m%d%H%M')
    >>> u=_until_timespec_vanilla(time.mktime(t), 4, 20, 32)
    >>> time.ctime(u)
    'Wed Jan  1 04:20:32 2003'
    """    
    ttuple=time.localtime(curticks)
    ntuple=ttuple[:3] + (hr, min, sec) + ttuple[-3:]
    nt=time.mktime(ntuple)
    if nt > curticks:
        return nt
    else:
        # add a day, but the length of the day
        # depends on whether we are on the cusp
        # of a change in DST status.  
        dst1=ntuple[-1]
        # 24 hours later
        nextday=nt+86400
        nexttuple=time.localtime(nextday)
        dst2=nexttuple[-1]
        if dst1==dst2:
            # no change in dst
            return nextday
        elif dst1<dst2:
            # 23 hours
            return nt+82800
        else:
            # 25 hours
            return nt+90000
            
def _until_timespec(curticks, hr, min, sec):
    if _have_dateutil:
        return _until_timespec_dateutil(curticks, hr, min, sec)
    elif _have_mx:
        return _until_timespec_mx(curticks, hr, min, sec)
    else:
        return _until_timespec_mx(curticks, hr, min, sec)

def untilString(until, curdate=None):
    """\
    handles all cases where until argument is a string
    """
    curdate=_to_ticks(curdate)

    # if it looks like a "minutes after hour", return current date
    # slammed to next minutes.

    if until[0]== ':' and until[1] in _digits and until[2] in _digits:
	mins = int(until[1:])
        # we may need to roll over the hour, and I want to avoid using
        # mx or dateutil, hence the following arithmetic.  Leap
        # seconds be damned.
        curmin=time.localtime(curdate)[4]
        secs_to_add=((mins-curmin) % 60)* 60
        return curdate+secs_to_add
    
    # elif it looks like just a timespec, return current date with
    # time set to that.
    elif _timespec.search(until):
	parts = until.split(':')
	if len(parts) == 2:
            parts.append('00')
	hr, min, sec = map(int, parts)
        return _until_timespec(curdate, hr, min, sec)
    
    # elif it looks like an old-format datespec, just pass it to the
    # ugly function.
    elif _old_datespec.search(until):
	return datestrToSeconds(until)

    # elif it looks like a nice datespec/timespec, make a date.
    elif _nice_datespec.search(until):
        try:
            return _parse_ISO(until)
        except ValueError:
            raise TimeException, until

    # else boom
    else:
        raise TimeException, until

def timeConv(s):
    """convert a time like 9d20h10m15s to seconds"""
    tot=0
    lastind=0
    for i in range(len(s)):
        c=s[i]
        if c=='d':
            tot=tot+int(s[lastind:i])*86400
            lastind=i+1
        elif c=='h':
            tot=tot+int(s[lastind:i])*3600
            lastind=i+1
        elif c=='m':
            tot=tot+int(s[lastind:i])*60
            lastind=i+1
        elif c=='s':
            tot=tot+int(s[lastind:i])
            lastind=i+1
        elif c not in _digits:
            raise TimeException, s
    return tot 

def currentDate():
    """get current date -- duh!"""
    tt=time.localtime(time.time())
    return tuple(tt[:3])

def isDST():
    """are we in daylight saving time?"""
    return time.localtime(time.time())[-1]

def datestrToSeconds(timestr):
    """converts date strings like 10/20/1999 10:30:15 to a seconds since
    epoch value

    unfortunately, since there is no mktime for UCT, we have to fuck around
    with localtime and dealing with the timezone offset and DST"""

    #pull apart by /'s
    datestuff=timestr.split('/')
    if len(datestuff) == 1: #if no /'s use todays date
        y,mo,d=currentDate()
        timespec=timestr
    elif len(datestuff) != 3: #if some weird number of /'s barf
        raise TimeException, timestr
    else:
        parts=datestuff[2].split(' ') #isolate the year from the time
        mo=int(datestuff[0])
        d=int(datestuff[1])
        y=int(parts[0])
        #else, we might not be y2k compliant, all years must be 4 digits
        if y<100: 
            raise TimeException, timestr
        timespec=parts[-1]

    #pull apart at :'s
    timestuff=timespec.split(':')
    if len(timestuff) != 3: #some weird number of colons, barf
        raise TimeException, timestr
    h,m,s=map(int, timestuff)
    secs=time.mktime((y,mo,d,h,m,s,0,0,0)) #get seconds in local timezone
    return secs

def _parse_ISO_mx(datestr):
    """
    >>> _parse_ISO_mx('2003-10-21 15:30')
    1066764600.0
    >>> _parse_ISO_mx('2003-10-21')
    1066708800.0
    """    
    return DateTime.ISO.ParseDateTime(datestr).ticks()

def _parse_ISO_dateutil(datestr):
    """
    >>> _parse_ISO_dateutil('2003-10-21 15:30')
    1066764600.0
    >>> _parse_ISO_dateutil('2003-10-21')
    1066708800.0
    """
    return time.mktime(_parse_dateutil(datestr).timetuple())

def _parse_ISO_vanilla(datestr):
    """
    >>> _parse_ISO_vanilla('2003-10-21 15:30')
    1066764600.0
    >>> _parse_ISO_vanilla('2003-10-21')
    1066708800.0
    """
    formats=['%Y-%m-%d %H:%M:%S',
             '%Y-%m-%d %H:%M',
             '%Y-%m-%d',
             '%Y-%m']
    for f in formats:
        try:
            return time.mktime(time.strptime(datestr, f))
        except ValueError:
            continue
    raise ValueError, datestr
             
def _parse_ISO(datestr):
    if _have_dateutil:
        return _parse_ISO_dateutil(datestr)
    elif _have_mx:
        return _parse_ISO_mx(datestr)
    else:
        return _parse_ISO_vanilla(datestr)
    
def _old_test():
    print "testing old functions..."
    print timeConv('1h20m3s')
    print time.asctime(time.gmtime(datestrToSeconds('10:20:03')))
    print time.asctime(time.gmtime(datestrToSeconds('2/11/1999 10:20:03')))
    print currentDate()
    print "testing new functions..."
    cur = DateTime.now()
    print cur.ticks(), cur 
    for test in [
	':15',
	(':15', ':30', ':45', ':00', '06:00'),
	'00:15',
	'23:59',
	'23:59:59',
	'2007-05-06',
	'2007-05-06 23:59',
	'2007-05-06 23:59:59',
	cur+0.5,
	DateTime.RelativeDateTime(minute=15),
	DateTime.RelativeDateTime(minute=00),
    ]:
        scs = None
        try:
	   scs = convertUntil(test)
           status = 'good'
        except PastTimeException:
           status = 'time is past'
        except TimeException:
           status = 'bad argument'           
	print test
        print '-->', scs,
        if scs is not None:
            print DateTime.DateTimeFrom(scs),
        else:
            print "None",
        print status

def _doctest():
    import doctest, timeutil
    return doctest.testmod(timeutil)
