#  
#  Copyright (C) 2001 Andrew T. Csillag <drew_csillag@geocities.com>
#  
#      You may distribute under the terms of either the GNU General
#      Public License or the SkunkWeb License, as specified in the
#      README file.
#   
"""
Tag date - description???
"""

from CommonStuff import *
try: 
    from mx import DateTime
except:
    import DateTime
    
from Date import TimeUtil
import Date
import types

class DateTag(DTTag):
    def __init__(self):
        DTTag.__init__ ( self, 'date', isempty=1, 
                         modules = [ DateTime, TimeUtil, Date, types ] )

    def genCode(self, indent, codeout, tagreg, tag):
        DTCompilerUtil.tagDebug(indent, codeout, tag)
        args=DTUtil.tagCall(tag, [
            ('fmt', Date.DEFAULT_FORMAT), 
            ('date', 'None'), 
	    ('lang', 'None'), 
            ('timezone', 'None'),
            ('srctimezone', 'None'),
            # new names for timezone and srctimezone;
            # old ones still valid
            ('to_zone', 'None'),
            ('from_zone', 'None'),
            ])
        args=DTCompilerUtil.pyifyArgs(tag, args)
        date=DTCompilerUtil.getTempName()
        tz=DTCompilerUtil.getTempName()
        from_tz=DTCompilerUtil.getTempName()

	# play some dosido with timezone args.
	if args['to_zone'] == None and args['timezone'] != None:
	    args['to_zone'] = args['timezone']
	if args['from_zone'] == None and args['srctimezone'] != None:
	    args['from_zone'] = args['srctimezone']

        if args['date'] == 'None':
            codeout.write(indent, '%s = __h.DateTime.now()' % date)
        else:
            codeout.write(indent, '%s = (%s)' % (date, args['date']))
            codeout.write(indent, '%s = (%s) or __h.DateTime.now()' % (
                date, date))
            codeout.write(indent, 'if not __h.Date.isDateTime(%s):' % date)
            codeout.write(indent+4, 'raise TypeError, "date argument must be a '
			  'DateTime object: %%s" %% %s' % date)
        lang=DTCompilerUtil.getTempName()

        # Try to lookup lang in local / global namespace
        codeout.write(indent, '%s = (%s) or locals().get("lang", None) ' 
                              'or globals().get("lang", "eng")' 
                              % (lang, args['lang']) )

        # Convert timezone
        codeout.write(indent, 'if %s or %s:' % (args['to_zone'], args['from_zone']))
        codeout.write(indent+4, '%s = %s or "LOCAL"' % (tz, args['to_zone']))
        codeout.write(indent+4, '%s = %s or "LOCAL"' % (from_tz, args['from_zone']))
        codeout.write(indent+4, '%s = __h.Date.Convert ( %s, to_zone=%s,'
				'from_zone=%s)' % (date, date, tz, from_tz))
        codeout.write(indent+4, 'del %s, %s' % (tz, from_tz))
        codeout.write(indent, '__h.OUTPUT.write(__h.Date.DateString(%s,'
			       '%s, lang=%s))' % (date, args['fmt'], lang))
        codeout.write(indent, 'del %s, %s' % (lang, date))
