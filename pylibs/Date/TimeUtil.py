#  
#  Copyright (C) 2001 Andrew T. Csillag <drew_csillag@geocities.com>
#  
#      You may distribute under the terms of either the GNU General
#      Public License or the SkunkWeb License, as specified in the
#      README file.
#   
"""miscellaneous time routines"""

try:
    from mx import DateTime
except:
    import DateTime
import sys
import time
import types
import string
import re
import Date
import Format
LocalDate= Date.LocalDate
RDT = DateTime.RelativeDateTime
isDateTime = Format.isDateTime

TimeException='TimeException: not a valid time'
PastTimeException='PastTimeException: cache "until" argument is in the past'

# high-level functions called by the generated code
# of the <:cache:> tag with its until or duration argument. 
# It sorts through all of the possible
# argument combinations:

def convertDuration(duration, curdate=None):
    if curdate is None:
        curdate = time.time()
    return timeConv(duration) + curdate

def convertUntil(until, curdate=None):
    if curdate is None:
        curdate = LocalDate()
    # if until is a DateTime object,
    # consider it to be in local server time,
    # and return the ticks.
    if isDateTime(until):
        result = until.ticks()
    # elif a RelativeDateTime,
    # add it to the current date and return
    elif isinstance(until, RDT):
	result = (curdate + until).ticks()
    # elif until is a single string,
    # let untilString handle it.
    elif type(until) == types.StringType:
	result = untilString(until, curdate)
    # elif a list or tuple of items,
    # run convertUntil on each, take
    # the minimum value in the result list, and return that.
    elif type(until) in (types.ListType, types.TupleType):
	lowres = None
	for i in until:
	    thisone = convertUntil(i, curdate)
	    if lowres is None or thisone < lowres:
		lowres = thisone
        result = lowres

    else:
        raise TimeException, until

    if result < curdate.ticks():
        raise PastTimeException, until
    return result

# helper re's for untilString

_min_after_hour = re.compile(r'^:\d{2}$')
_timespec       = re.compile(r'^\d{2}:\d{2}(:\d{2})?$')
_old_datespec   = re.compile(r'^\d{2}/\d{2}/\d{4} \d{2}:\d{2}:\d{2}$')
_nice_datespec  = re.compile(r'^\d{4}-\d{2}-\d{2}( \d{2}:\d{2}(:\d{2})?)?$')

_digits = '0123456789'

# handles all cases where until argument is a string

def untilString(until, curdate=None):
    if curdate is None:
        curdate = LocalDate()
    # if it looks like a "minutes after hour",
    # return current date slammed to next minutes.
    if until[0] == ':' and until[1] in _digits and until[2] in _digits:
	mins = int(until[1:])
	if curdate.minute < mins:
	    return (curdate + RDT(minute=mins, second=0)).ticks()
        else:
	    return (curdate + RDT(hours=1, minute=mins, second=0)).ticks()

    # elif it looks like just a timespec, return
    # current date with time set to that.
    elif _timespec.search(until):
	parts = string.split(until, ':')
	if len(parts) == 2: parts.append('00')
	hr, min, sec = map(int, parts)
	reldate = RDT(hour=hr, minute=min, second=sec)
	huh = curdate + reldate
	if huh <= curdate:
	    return (huh + 1).ticks()
        else:
	    return huh.ticks()

    # elif it looks like an old-format datespec,
    # just pass it to the ugly function.
    elif _old_datespec.search(until):
	return datestrToSeconds(until)

    # elif it looks like a nice datespec/timespec,
    # make a date.
    elif _nice_datespec.search(until):
       return LocalDate(until).ticks()

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
    datestuff=string.split(timestr,'/')
    if len(datestuff) == 1: #if no /'s use todays date
        y,mo,d=currentDate()
        timespec=timestr
    elif len(datestuff) != 3: #if some weird number of /'s barf
        raise TimeException, timestr
    else:
        parts=string.split(datestuff[2],' ') #isolate the year from the time
        mo=int(datestuff[0])
        d=int(datestuff[1])
        y=int(parts[0])
        #else, we might not be y2k compliant, all years must be 4 digits
        if y<100: 
            raise TimeException, timestr
        timespec=parts[-1]

    #pull apaprt at :'s
    timestuff=string.split(timespec,':')
    if len(timestuff) != 3: #some weird number of colons, barf
        raise TimeException, timestr
    h,m,s=map(int, timestuff)
    secs=time.mktime(y,mo,d,h,m,s,0,0,0) #get seconds in local timezone
    return secs

if __name__=='__main__':
    print "testing old functions..."
    print timeConv('1h20m3s')
    print time.asctime(time.gmtime(datestrToSeconds('10:20:03')))
    print time.asctime(time.gmtime(datestrToSeconds('2/11/1999 10:20:03')))
    print currentDate()
    print "testing new functions..."
    cur = LocalDate()
    print cur.ticks(), cur 
    for test in [
	':15',
	(':15', ':30', ':45', ':00', '06:00'),
	'00:15',
	'23:59',
	'23:59:59',
	'2003-05-06',
	'2003-05-06 23:59',
	'2003-05-06 23:59:59',
	LocalDate()+0.5,
	RDT(minute=15),
	RDT(minute=00),
    ]:
        scs = None
        try:
	   scs = convertUntil(test)
           status = 'good'
        except TimeException:
           status = 'bad argument'
        except PastTimeException:
           status = 'time is past'
	print test
        print '-->', scs, LocalDate(scs), status
