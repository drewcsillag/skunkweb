#  
#  Copyright (C) 2003 Jacob Smullyan <smulloni@smullyan.org>
#  
#      You may distribute under the terms of either the GNU General
#      Public License or the SkunkWeb License, as specified in the
#      README file.
#   
# Time-stamp: <03/06/03 09:40:37 smulloni>
# $Id: cronjob.py,v 1.1 2003/06/03 13:24:28 smulloni Exp $

"""
a simple cron implementation.  

"""

import mx.DateTime as M
import re
import os
import signal
import sys
import time
import traceback
import cStringIO

_second_zero=M.RelativeDateTime(second=0)

class CronJob(object):
    """
    a function or eval-able thing (string or code object)
    bundled with a cron specification indicating when the
    code is to be executed.
    """
    def __init__(self,
                 minutes,
                 hours,
                 days_of_month,
                 months,
                 days_of_week,
                 jobFunc):
        self.minutes=minutes
        self.hours=hours
        self.days_of_month=days_of_month
        self.months=months
        self.days_of_week=days_of_week
        self.jobFunc=jobFunc
        self.last_ran=None

    def from_spec(kls, spec, jobFunc=None):
        """
        generates a CronJob instance from a cron specification
        in the classic format:

        MINUTES HOURS MONTHS DAYS_OF_MONTH DAYS_OF_WEEK

        In addition to numbers, three-letter english abbreviations
        are acceptable for days and months; for all fields, * wildcards,
        lists of values separated by commas, ranges separated by dashes,
        and the step indicator */n are acceptable.  For example:

        1,11,21,*/5 3-5,8 1,feb,aug-oct * mon,thu

        is a legal cron spec.

        The job to be performed can either be a string indicated as
        the last field in the spec string, or a function passed as
        jobFunc.
        """
        mins, hrs, mds, mons, wds, job=parse_cron(spec)
        if jobFunc is not None and job is not None:
            raise ValueError, "can't specify job both in spec and in function"
        jobFunc=jobFunc or job
        if not jobFunc:
            raise ValueError, "must specify job"
        return kls(mins, hrs, mds, mons, wds, jobFunc)
    
    from_spec=classmethod(from_spec)

    def matchTime(self, dt=None):
        """
        returns a boolean value indicating whether
        the cron specification matches the given time
        (or, if no time is given, the current time)
        """
        if dt is None: dt=M.now()
        elif isinstance(dt, int):
            dt=M.DateTimeFromTicks(dt)
        # otherwise assume it is an mx.DateTime
        (mis,
         hs,
         mos,
         dms,
         dws)=(self.minutes,
               self.hours,
               self.months,
               self.days_of_month,
               self.days_of_week)
        return (mis and dt.minute in mis) \
               and (hs and dt.hour in hs) \
               and (dms and dt.day in dms) \
               and (mos and dt.month in mos) \
               and (dws and dt.day_of_week in dws)

    def timesForRange(self, start=None, end=None, grain=1):
        """
        returns a list of times where the spec matches within the
        range from start to end, stepped through by grain.
        """
        if start is None:
            start=M.now() + _second_zero
        elif isinstance(start, int):
            start=M.DateTimeFromTicks(start)
        if end is None:
            end=start+M.oneDay
        elif isinstance(end, int):
            end=M.DateTimeFromTicks(end)
        if start > end:
            raise ValueError, "start time %s greater than end time %s" % \
                  (start.asctime(), end.asctime())
        if grain<1:
            raise ValueError, "grain must be at least one minute"
        incr=M.RelativeDateTime(minutes=grain)
        times=[]
        while start<=end:
            if self.matchTime(start):
                times.append(start)
            start=start+incr
        return times
        
    def __call__(self,
                 locals=None,
                 globals=None,
                 *args,
                 **kwargs):
        if callable(self.jobFunc):
            ret=self.jobFunc(*args, **kwargs)
        else:
            if locals is None:
                locals=globals()
            if globals is None:
                globals=globals()
            ret=eval(self.jobFunc, globals, locals)
        return ret

class CronLogger(object):
    """
    interface for logging the output from cron jobs.
    """
    def out(msg):
        pass

    def err(msg):
        pass

class StreamLogger(CronLogger):
    """
    the simplest possible implementation of CronLogger.
    """
    def __init__(self, out=sys.stdout, err=sys.stderr):
        self._out=out
        self._err=err
    def out(msg):
        self._out.write(msg)
        self._out.flush()
    def err(msg):
        self._err.write(msg)
        self._err.flush()

class CronTab(object):
    """
    a collection of cronjobs, that share
    user, group, poll period, and a logger.
    """
    def __init__(self,
                 user=None,
                 group=None,
                 pollPeriod=5,
                 logger=None):

        self.cronjobs=[]
        self.user=user
        self.group=group
        self.pollPeriod=pollPeriod
        if logger is None:
            logger=StreamLogger()
        self.logger=logger

    def _handle_sigchld(self, signum, frame):
        try:
            os.waitpid(0, os.WNOHANG)
        except OSError:
            pass

    def run(self):
        """
        this method is used if you want the crontab
        to run in its own loop.  If you don't, you are
        responsible for killing off the zombies yourself.
        """
        if self.user is not None:
            os.setuid(self.user)
        if self.group is not None:
            os.setgid(self.group)
        signal.signal(signal.SIGCHLD, self._handle_sigchld)            
        while 1:
            try:
                time.sleep(self.pollPeriod)
                self.run_jobs()
            # this is for testing
            except KeyboardInterrupt:
                break
        signal.signal(signal.SIGCHLD, sig.SIG_IGN)
            
    def run_jobs(self, dt=None):
        """
        run any cronjobs that deserve to be run at the current time.
        A job can be run no more than once a minute.  When an error occurs,
        a traceback is printed to stderr.
        """
        if dt is None:
            dt=M.now()+_second_zero
        for j in self.cronjobs:
            lr=j.last_ran
            if (lr is None and j.matchTime(dt)) or  \
                   ((lr+_second_zero) != dt \
                    and j.matchTime(dt)):
                j.last_ran=dt
                pid=os.fork()
                if pid:
                    continue
                else:
                    newout=cStringIO.StringIO()
                    newerr=cStringIO.StringIO()
                    oldout=sys.stdout
                    olderr=sys.stderr
                    sys.stdout=newout
                    sys.stderr=newerr
                    error=0
                    try:
                        j()
                    except:
                        traceback.print_exc(file=newerr)
                        error=1
                    newout.flush()
                    newerr.flush()
                    sys.stdout=oldout
                    sys.stderr=olderr
                    self.logger.out(newout.getvalue())
                    self.logger.err(newerr.getvalue())
                    sys.exit(error)
                        
        
_rangeRE=re.compile(r'(\d{1,2})-(\d{1,2})')
_specRE=re.compile(r'\*(?:/(\d+))?')
_splitRE=re.compile(r'(\S+)\s+'*4+r'(\S+)(?:\s+(.+))?')

def parse_cron(cronspec):

    """
    format is the standard one for cron:

    MINUTES HOURS DAY_OF_MONTH MONTH DAY_OF_WEEK
    """
    
    (minutes,
     hours,
     days_of_month,
     months,
     days_of_week,
     job)=_splitRE.match(cronspec).groups()
    minutes=parse_minutes(minutes)
    hours=parse_hours(hours)
    days_of_month=parse_days_of_month(days_of_month)
    months=parse_months(months)
    days_of_week=parse_days_of_week(days_of_week)
    return minutes, hours, days_of_month, months, days_of_week, job

def _parse_spec(spec, limit, start=0):
    units=spec.split(',')
    res=[]
    for u in units:
        match=_rangeRE.match(u)
        if match:
            u1, u2=map(int, match.groups())
            # we want an inclusive range, so add one to u2
            if not start <= u1 < u2 <= limit:
                raise ValueError, "inappropriate range: %s" % u
            res.extend(range(u1, u2+1))
            continue
        try:
            i=int(u)
        except ValueError:
            match=_specRE.match(u)
            if match:
                divisor=match.group(1)
                if divisor is not None:
                    divisor=int(divisor)
                else:
                    divisor=1
                if divisor >=limit:
                    raise ValueError, "excessive divisor value: %s" % u
                res.extend(range(start, limit, divisor))
                continue
            else:
                raise ValueError, "cannot parse: %s" % u
        else:
            if start <= i < limit:
                res.append(i)
            else:
                raise ValueError, "out of range: %d" % i
    # guarantee uniqueness
    d={}
    for r in res:
        d[r]=None
    res=d.keys()
    res.sort()
    return res

def parse_minutes(spec):
    return _parse_spec(spec, 60, 0)

def parse_hours(spec):
    return _parse_spec(spec, 24, 0)

def parse_days_of_month(spec):
    return _parse_spec(spec, 32, 1)

_months=[(M.Month[x].lower()[:3], str(x)) for x in range(1, 13)]

def parse_months(spec):
    spec=spec.lower()
    for m, i in _months:
        spec=spec.replace(m, i)
    return _parse_spec(spec, 13, 1)

_days=[(M.Weekday[(x-1) % 7].lower()[:3], str(x)) for x in range(7)]

def parse_days_of_week(spec):
    spec=spec.lower().replace('7', '0')
    for d, i in _days:
        spec=spec.replace(d, i)
    # make it so the numbers match those used by
    # mx.DateTime for weekdays
    return [(x+1) % 7 for x in _parse_spec(spec, 7, 0)]


def test1():
    def foo():
        print "hi from foo()"
        raise "nougat"

    c=CronTab()
    c.cronjobs.append(CronJob.from_spec("* * * * *", foo))
    c.run()

__all__=['CronJob',
         'CronTab',
         'CronLogger',
         'StreamLogger',
         'parse_spec']
