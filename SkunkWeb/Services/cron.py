# Time-stamp: <03/06/03 16:24:00 smulloni>
# $Id$

########################################################################
#  
#  Copyright (C) 2003, Jacob Smullyan <smulloni@smullyan.org>
#  
#      You may distribute under the terms of either the GNU General
#      Public License or the SkunkWeb License, as specified in the
#      README file.
#   
########################################################################

import SkunkWeb.Configuration as _C
import cronjob
import os
from templating.MailServices import sendmail

class SkunkMailLogger(cronjob.CronLogger):
    def __init__(self,
                 from_addr=None,
                 to_addrs=[]):
        self.from_addr=from_addr
        self.to_addrs=to_addrs 

    def out(self, msg, job):
        self.send(msg, 'SkunkWeb Cron Output: %s' % str(job.jobFunc))

    def err(self, msg, job):
        self.send(msg, "SkunkWeb Cron Error: %s" % str(job.jobFunc))

    def send(self, msg,subject):
        to_addrs=self.to_addrs or _C.CronToAddrs
        from_addr=self.from_addr or _C.CronFromAddress or _C.FromAddress
        sendmail(to_addrs,
                 subject,
                 msg,
                 from_addr=from_addr)        

_C.mergeDefaults(CronJobs=[],
                 CronLogger=SkunkMailLogger(),
                 CronFromAddress=None,
                 CronToAddrs=None)


CronTab=cronjob.CronTab(logger=_C.CronLogger,
                        cronjobs=_C.CronJobs)


__all__=['CronTab', 'SkunkMailLogger']
