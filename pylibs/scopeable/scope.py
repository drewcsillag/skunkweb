# Time-stamp: <01/09/03 19:05:09 smulloni>
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
# an object that transforms itself depending on its environment.
# $Id: scope.py,v 1.1.1.1 2001/08/05 15:00:26 drew_csillag Exp $
# Time-stamp: <01/05/04 11:01:26 smulloni>
########################################################################

import fnmatch
import types
import re
import _scope

class Scopeable(_scope.Scopeable):
    def scope(self, param=None):
        """
        param should be one of the following:
        1. None (the default), in which case all the current scopes will be
           returned;
        2. a string (a param name), in which case all the current top-level
           scopes for that parameter will be returned;         
        3. a dictionary of values {param = paramValue}, in which case the 
           Scopeable will be scoped according to those values.
        """
        if param==None:
            return self.__currentScopes
        elif type(param)!=types.DictType:
            # treat this as a accessor method          
                if self.__currentScopes.has_key(param):
                    return self.__currentScopes[param]
                else:
                    return None
        else:
            # treat as a mutator
            # store the current scope
            self.__currentScopes.update(param)
            scopedDict={}
            for matcher in self.matchers:
                self.__processMatcher(matcher, scopedDict, param)                
            if scopedDict:
                self.push(scopedDict)

    def __processMatcher(self, matcher, scopedDict, scopeValDict):
        """
        recursively processes a matcher.
        """
        if scopeValDict.has_key(matcher.param) and \
           matcher.match(scopeValDict):
            if matcher.overlayDict:
                scopedDict.update(matcher.overlayDict)
            for kid in matcher.children():
                self.__processMatcher(kid, scopedDict, scopeValDict)

    def __str__(self):
        return str(self.mash())


class ScopeMatcher:
    def __init__(self, param, matchObj, overlayDict, children=None):
        self.param=param
        self.matchObj=matchObj
        self.overlayDict=overlayDict
        self.__children=children or []
        self._hashString="%s%s" % (self.param, self.matchObj)

    def _match(self, other):
        """
        subclasses should implement this.
        """
        raise NotImplementedError

    def match(self, paramDict):
        return self._match(paramDict.get(self.param, None))

    def children(self):
        """
        this gives you a COPY of the matcher's list of children.
        You don't get the original, because it needs to be kept
        sorted, and I don't want to have to perform the sort
        redundantly, for safety, every time a match is performed.
        Use addChildren to add matchers to the list and the sort will
        be performed then, automagical-like.
        """
        return self.__children[:]

    def addChildren(self, *kids):
        """
        adds ScopeMatcher(s) to the list of children,
        and then sorts the list.
        """
        for kid in kids:            
            if not isinstance(kid, ScopeMatcher):           
                raise TypeError, "child matcher must be instance " \
                      "of ScopeMatcher"
        self.__children.extend(kids)
        self.__children.sort()

    def __str__(self):
        return "%s : %s (%s %s)" % (self.param,
                                   self.matchObj,
                                   self.overlayDict,
                                   self.__children)

    def __repr__(self):
        return "<%s.%s instance: %s>" % (self.__class__.__module__,
                                         self.__class__.__name__,
                                         self)

    def __hash__(self):
        return hash(self.__hashString)

    def __cmp__(self, other):
        if isinstance(other, ScopeMatcher):
            # I don't want two different matchers whose top level is
            # identical to exist in the same dictionary, regardless of
            # their match type.
            return cmp(self._hashString, other._hashString)
        else:
            # who cares
            return cmp(str(self), str(other))


class StrictMatcher(ScopeMatcher):

    def _match(self, other):
        return self.matchObj==other

class SimpleStringMatcher(ScopeMatcher):
    
    def _match(self, other):
        return type(other)==types.StringType \
               and other.startswith(self.matchObj)

class GlobMatcher(ScopeMatcher):
    
    def _match(self, other):
        return type(other)==types.StringType \
               and fnmatch.fnmatchcase(other, self.matchObj)

class RegexMatcher(ScopeMatcher):

    def __init__(self, matchObj, overlay, children=[]):
        ScopeMatcher.__init__(self, matchObj, overlay, children)
        self.__compiledRegex=re.compile(self.matchObj)

    def _match(self, other):
        return type(other)==types.StringType \
               and self.__compiledRegex.match(other)


def test1(**kw):
    vals={'foo':0, 'bar':1, 'spam':2, 'cheese':3, 'fjord':4, 'parrot':5}
    env={'port':80, 'location':'/', 'host':'localhost'}
    env.update(kw)
    locMatcher1=SimpleStringMatcher('location',
                                    '/',
                                    {'spam':6, 'newt':7})
    locMatcher2=SimpleStringMatcher('location',
                                    '/foo',
                                    {'cheese':8, 'viking':9})
    hostMatcher=StrictMatcher('host',
                              'localhost',
                              None,
                              [locMatcher1, locMatcher2])
    config=Scopeable(vals)
    print config
    print '*'*40
    config.addScopeMatchers(hostMatcher)
    config.scope(env)
    print config
    del locMatcher1
    del locMatcher2
    del hostMatcher
    del config

def test2(**kw):
    vals={'foo':0, 'bar':1, 'spam':2, 'cheese':3, 'fjord':4, 'parrot':5}
    env={'port':80, 'location':'/', 'host':'localhost'}
    env.update(kw)
    locMatcher1=SimpleStringMatcher('location', '/', {'spam':6, 'newt':7})
    locMatcher2=SimpleStringMatcher('location',
                                    '/foo',
                                    {'cheese':8, 'viking':9})
    hostMatcher=StrictMatcher('host', 'localhost', None)
    hostMatcher.addChildren(locMatcher1, locMatcher2)
    hostMatcher2=StrictMatcher('host',
                               'localhost',
                               None,
                               [locMatcher1, locMatcher2])
    print hostMatcher2.children()
    config=Scopeable(vals)
    print config
    print '*'*40
    config.addScopeMatchers(hostMatcher)
    config.scope(env)
    print config    
##    del locMatcher1
##    del locMatcher2
##    del hostMatcher
##    del hostMatcher2    
##    del config
