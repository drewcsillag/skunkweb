# -*- coding: iso-8859-1 -*-
#  
#  Copyright (C) 2001 Andrew T. Csillag <drew_csillag@geocities.com>
#  
#      You may distribute under the terms of either the GNU General
#      Public License or the SkunkWeb License, as specified in the
#      README file.
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


class German(_DateLocale):
    """The german date locale"""
    Weekday = ('Montag','Dienstag','Mittwoch','Donnerstag',
              'Freitag','Samstag','Sonntag')

    Day = _make_day_lookup(Weekday)

    WeekdayAbbr = ('Mo', 'Di', 'Mi', 'Do', 'Fr', 'Sa', 'So')

    DayAbbr = _make_day_lookup(WeekdayAbbr)

    Month = (None,
	     'Januar','Februar','März','April','Mai','Juni',
	     'Juli','August','September','Oktober','November','Dezember')

    MonthAbbr = (None,
		'Jan', 'Feb', 'Mär', 'Apr', 'Mai', 'Jun',
		'Jul', 'Aug', 'Sep', 'Okt', 'Nov', 'Dez')

    YourTime = 'ihre lokale Zeit'

German = German()


###

_langs = {'eng': English,
          'esp': Spanish,
	  # backward compatibility
          'spa': Spanish,
	  'por': Portuguese,
          'deu': German}

def lang_lookup(lang='eng'):
    """get locale by 3 letter iso code"""
    if _langs.has_key(lang):
	return _langs[lang]
    else:
	return _langs['eng']
