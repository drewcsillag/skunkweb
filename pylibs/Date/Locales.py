# -*- coding: iso-8859-1 -*-
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
# language lookup

def _make_day_lookup(days):
    d = {}
    for i in range(len(days)):
        d[days[i]] = i
        d[i] = days[i]
    return d

class _DateLocale:
    Weekday = ('Monday', 'Tuesday', 'Wednesday', 'Thursday',
	   'Friday', 'Saturday', 'Sunday')

    Day = _make_day_lookup(Weekday)

    Month = (None, 'January', 'February', 'March', 'April', 'May', 'June',
	     'July', 'August', 'September', 'October', 'November', 'December')

    WeekdayAbbr = ('Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun')

    DayAbbr = _make_day_lookup(WeekdayAbbr)

    MonthAbbr = (None, 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
		 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec')

    AmPm = ('am', 'pm')

    YourTime = 'your local time'

class English(_DateLocale):
    """The english date locale"""
    pass

English = English()

class Spanish(_DateLocale):
    """The Spanish date locale"""
    Weekday = ('lunes', 'martes','miércoles','jueves','viernes',
               'sábado','domingo')

    Day = _make_day_lookup(Weekday)

    WeekdayAbbr = ('lun', 'mar', 'mie', 'jue', 'vie', 'sab', 'dom')

    DayAbbr = _make_day_lookup(WeekdayAbbr)

    Month = (None,
	     'enero','febrero','marzo','abril','mayo','junio',
	     'julio','agosto','septiembre','octubre','noviembre','diciembre')

    MonthAbbr = (None,
		 'ene', 'feb', 'mar', 'abr', 'may', 'jun',
		 'jul', 'ago', 'sep', 'oct', 'nov', 'dic')

    YourTime = 'en su horario'

Spanish = Spanish()

class Portuguese(_DateLocale):
    """The portuguese date locale"""
    Weekday = ('segunda','ter','quarta','quinta',
              'sexta','sabado','domingo')

    Day = _make_day_lookup(Weekday)

    WeekdayAbbr = ('seg', 'ter', 'qua', 'qui', 'sex', 'sab', 'dom')

    DayAbbr = _make_day_lookup(WeekdayAbbr)

    Month = (None,
	     'janeiro','fevereiro','mar','abril','maio','junho',
	     'julho','agosto','septembro','outubro','novembro','dezembro')

    MonthAbbr = (None,
		'jan', 'fev', 'mar', 'abr', 'mai', 'jun',
		'jul', 'ago', 'sep', 'out', 'nov', 'dez')

    YourTime = 'en su horario'

Portuguese = Portuguese()

###

_langs = {'eng': English,
          'esp': Spanish,
	  # backward compatibility
          'spa': Spanish,
	  'por': Portuguese}

def lang_lookup(lang='eng'):
    """get locale by 3 letter iso code"""
    if _langs.has_key(lang):
	return _langs[lang]
    else:
	return _langs['eng']
