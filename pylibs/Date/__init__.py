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

