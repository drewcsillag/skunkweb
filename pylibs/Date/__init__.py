#  
#  Copyright (C) 2001 Andrew T. Csillag <drew_csillag@geocities.com>
#  
#      You may distribute under the terms of either the GNU General
#      Public License or the SkunkWeb License, as specified in the
#      README file.
#   
"""A bunch of operations, based on the mxDateTime Date object"""
# setup of module namespace
try:
    from mx import DateTime
except:
    import DateTime

try:
    from mx.DateTime import ISO
except:
    import DateTime.ISO

from Date import LocalDate, UTCDate, GMTDate
from Date import DateTruncate, DateTrunc, DateRound, trunc, round
from Format import DateString, isDateTime, HTTPDate, DEFAULT_FORMAT
from Timezone import Convert, isDST, isDaylight, get_timezone

# now clobber the Date submodule
from Date import Date

