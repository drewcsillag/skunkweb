# Time-stamp: <02/11/22 17:29:36 smulloni>
# $Id: hooks.py,v 1.1 2002/02/14 02:58:25 smulloni Exp $

########################################################################
#  
#  Copyright (C) 2001, 2002 Andrew T. Csillag <drew_csillag@geocities.com>,
#                           Jacob Smullyan <smulloni@smullyan.org>
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
########################################################################

try:
    list
except NameError:
    from UserList import UserList as list
from fnmatch import fnmatchcase

class Hook(list):
    def __call__(self, *args, **kw):
        for i in self:
            ret = i(*args, **kw)
            if ret is not None:
                return ret

########################################################################

class KeyedHook:
    def __init__(self):
        self.pairList=SearchablePairList()
        self.__memoDict={}

    def __getitem__(self, jobName):
        if self.has_key(jobName):
            return self._getFuncList(jobName)
        raise KeyError, jobName

    def __setitem__(self, key, value):
        self.addFunction(value, key)

    def has_key(self, key):
        return not not self.pairList.keyMatches(key)

    def _clearCache(self, jobName):
        for key in self.__memoDict.keys():
            if key.startswith(jobName):
                self.__memoDict.remove(key)

    def addFunction(self, func, jobName='*', index=None):
        if not callable(func):
            raise TypeError, "%s not callable" % func
        self._clearCache(jobName)
        self.pairList.addPair(jobName, func, index)

    def _getFuncList(self, jobName):
        if self.__memoDict.has_key(jobName):
            return self.__memoDict[jobName]        
        funcList=[x[1] for x in self.pairList.getMatchList(jobName)]
        self.__memoDict[jobName]=funcList
        return funcList

    def __call__(self, jobName, *args, **kw):
        for f in self._getFuncList(jobName):
            retVal=f(*args, **kw)
            if retVal is not None:
                return retVal


class SearchablePairList:

    def __init__(self):
        self.orderedPairs=[] 

    def getMatchList(self, key):

        return filter(lambda pair, key=key: fnmatchcase(str(key),
                                                        pair[0]),
                      self.orderedPairs)

    def keyMatches(self, key):
        # rather than returning 1 and 0 here, return a tuple
        # of the indexes int the pairlist of the matches.
        matches=[]
        i=0
        for pair in self.orderedPairs:
            if fnmatchcase(str(key), pair[0]):
                matches.append(i)
            i+=1
        return tuple(matches)

    def addPair(self, key, value, index=None):
        if index==None:
            self.orderedPairs.append((key, value))
        else:
            self.orderedPairs.insert(index, (key, value))

########################################################################
# $Log: hooks.py,v $
# Revision 1.1  2002/02/14 02:58:25  smulloni
# moved hooks into a pylib; added some logging to templating handler, and minor fix
# to web service.
#
########################################################################
