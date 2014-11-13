# Time-stamp: <03/07/17 23:25:30 smulloni>

########################################################################
#  
#  Copyright (C) 2001-2003 Andrew T. Csillag <drew_csillag@geocities.com>,
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
            
    def oneshot(self, func, index=None):
        if not index:
            index=len(self)
        self.insert(index, _oneshot(self, func))

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

    def _clearCache(self, jobGlob):
        for key in self.__memoDict.keys():
            if fnmatchcase(key, jobGlob):
                del self.__memoDict[key]

    def addFunction(self, func, jobGlob='*', index=None):
        if not callable(func):
            raise TypeError, "%s not callable" % func
        self._clearCache(jobGlob)
        self.pairList.addPair(jobGlob, func, index)

    def removeFunction(self, func, jobGlob="*"):
        self.pairList.orderedPairs.remove((jobGlob, func))
        self._clearCache(jobGlob)

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

    def oneshot(self, func, jobGlob, index=None):
        self.addFunction(_oneshot(self, func, jobGlob), jobGlob, index)
        
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


class _oneshot:
    def __init__(self, hook, func, jobGlob=None):
        self.hook=hook
        self.func=func
        self.jobGlob=jobGlob

    def __call__(self, *args, **kwargs):
        try:
            self.func(*args, **kwargs)
        finally:
            try:
                self.hook.removeFunction(self, self.jobGlob)
            except AttributeError:
                self.hook.remove(self)
