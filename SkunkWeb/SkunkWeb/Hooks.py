# Time-stamp: <01/08/11 19:38:04 smulloni>
# $Id$

########################################################################
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
########################################################################

from UserList import UserList
from fnmatch import fnmatchcase
from SkunkWeb.ServiceRegistry import CORE
from SkunkWeb.LogObj import DEBUG

class Hook(UserList):
    def __call__(self, *args, **kw):
        for i in self:
            ret = i(*args, **kw)
            if ret is not None:
                return ret

ChildStart = Hook()
ServerStart = Hook()

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
            DEBUG(CORE, "calling %s with args (%s, %s)" % (str(f),
                                                           str(args),
                                                           str(kw)))
            try:
                retVal=f(*args, **kw)
                if retVal is not None:
                    return retVal
            except:
                import sys, traceback, cStringIO
                x=cStringIO.StringIO()
                traceback.print_tb(sys.exc_info()[2], file = x)
                text=x.getvalue()
                DEBUG(CORE, "exception occurred")
                DEBUG(CORE, text)
                raise

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
# $Log: Hooks.py,v $
# Revision 1.1.1.1  2001/08/05 14:59:37  drew_csillag
# take 2 of import
#
#
# Revision 1.8  2001/07/09 20:38:40  drew
# added licence comments
#
# Revision 1.7  2001/04/10 22:48:30  smullyan
# some reorganization of the installation, affecting various
# makefiles/configure targets; modifications to debug system.
# There were numerous changes, and this is still quite unstable!
#
# Revision 1.6  2001/04/04 18:11:37  smullyan
# KeyedHooks now take glob as keys.  They are tested against job names with
# fnmatch.fnmatchcase.   The use of '?' is permitted, but discouraged (it is
# also pointless).  '*' is your friend.
#
# Revision 1.5  2001/04/04 14:46:31  smullyan
# moved KeyedHook into SkunkWeb.Hooks, and modified services to use it.
#
########################################################################
