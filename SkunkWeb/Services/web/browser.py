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
# $Id: browser.py,v 1.2 2001/07/09 20:38:40 drew Exp $
# Time-stamp: <01/04/25 16:01:40 smulloni>

import string

class Browser:
    """A class that makes an attempt to parse the User-Agent string
    to produce various info"""
    def __init__(self, user_agent):
        if user_agent:
            self.getInfo(user_agent)
        else:
            #if no user agent string, can't do too much about it
            self.version = self.lang = self.name = ''

    def getInfo(self, user_agent):
        try:
            #find a space
            ind = string.find(user_agent, ' ')
            #get first thing in the ua string
            stuff = user_agent[:ind]
            #get name and version 
            self.name, self.version = string.split(stuff, '/')
            try:
                #try to get language
                if user_agent[ind + 1] == '[':
                    rest = user_agent[ind + 1:]
                    if rest[0] == '[':
                        self.lang = rest[1:string.find(rest, ']')]
                    else:
                        self.lang = ''
                else:
                    self.lang = ''

            except IndexError:
                self.lang = ''
        except: #if anything above blows up
            self.lang = self.name = self.version = ''

    def __str__(self):
        return '<Browser %s (v%s) [%s]>' % (self.name, self.version, self.lang)

########################################################################
# $Log: browser.py,v $
# Revision 1.2  2001/07/09 20:38:40  drew
# added licence comments
#
# Revision 1.1  2001/04/25 20:18:53  smullyan
# moved the "experimental" services (web_experimental and
# templating_experimental) back to web and templating.
#
########################################################################
