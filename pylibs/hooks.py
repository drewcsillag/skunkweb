# Time-stamp: <03/03/06 13:47:12 smulloni>
# $Id: hooks.py,v 1.3 2003/03/06 18:55:08 smulloni Exp $

########################################################################
#  
#  Copyright (C) 2001, 2002 Andrew T. Csillag <drew_csillag@geocities.com>,
#                           Jacob Smullyan <smulloni@smullyan.org>
#  
#      You may distribute under the terms of either the GNU General
#      Public License or the SkunkWeb License, as specified in the
#      README file.
#   
########################################################################

try:
    object
except NameError:
    from UserList import UserList as _list
else:
    _list=list
from fnmatch import fnmatchcase

class Hook(_list):
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

