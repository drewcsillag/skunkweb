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

"""
This module is deprecated, as it is very slow; use the faster 'scopeable' package.
"""

import fnmatch
import types
import re

class Scopeable:
    
    def __init__(self, dict={}):
        self.__dictList=[dict]
        self.matchers=[]
        self.__currentScopes={}

    def mergeDefaults(self, *args, **kw):
        """
        passed either a dictionary (or multiple dictionaries, which will
        be evaluated in order) or keyword arguments, will fold the key/value
        pairs therein into the dictionary of defaults without deleting any
        values that already exist there.  Equivalent to:
            newDict.update(defaultDict)
            defaultDict=newDict
        """
        for dict in args:
            if type(dict)==types.DictType:
                self.__mergeDefaults(dict)
            else:
                raise TypeError, "expected a DictType argument, got %s" \
                      % type(dict)
        self.__mergeDefaults(kw)

    def __mergeDefaults(self, dict):
        dict.update(self.__dictList[-1])
        self.__dictList[-1]=dict

    def __getattr__(self, attr):
        if attr == '__all__':
            return self._mash().keys()        
        for d in self.__dictList:
            if d.has_key(attr):
                return d[attr]
        raise AttributeError, attr

    def defaults(self):
        """
        this isn't a copy.  Use, do not abuse, etc.
        """
        return self.__dictList[-1]                            

    def mash(self):
        nd={}
        dlCopy=self.__dictList[:]
        dlCopy.reverse()
        map(nd.update, dlCopy)
        return nd
    
    def update(self, dict):
        self.__dictList[-1].update(dict)

    def push(self, dict):
        self.__dictList.insert(0, dict)

    def pop(self):
        return self.__dictList.pop()

    def trim(self):
        del self.__dictList[:-1]    

    def mashSelf(self):
        self.__dictList=[self.mash()]

    def addScopeMatchers(self, *paramMatchers):
        """
        paramMatcher is a ScopeMatcher instance.
        """
        self.matchers.extend(paramMatchers)
        self.matchers.sort()

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


########################################################################
# $Log: scope.py,v $
# Revision 1.1.1.1  2001/08/05 15:00:26  drew_csillag
# take 2 of import
#
#
# Revision 1.7  2001/07/30 16:07:29  smulloni
# made scope.Scopeable's "__matchers" field public: "matchers", and
# fixed two references to it, in ae_component and pars services.
#
# Revision 1.6  2001/07/09 20:38:41  drew
# added licence comments
#
# Revision 1.5  2001/05/04 18:38:53  smullyan
# architectural overhaul, possibly a reductio ad absurdum of the current
# config overlay technique.
#
# Revision 1.4  2001/05/03 16:15:00  smullyan
# modifications for scoping.
#
# Revision 1.3  2001/05/01 23:03:40  smullyan
# added support for name-based virtual hosts.
#
# Revision 1.2  2001/05/01 21:46:29  smullyan
# introduced the use of scope.Scopeable to replace the the ConfigLoader.Config
# object.
#
# Revision 1.1  2001/05/01 17:34:18  smullyan
# slightly more general configuration object.
#
########################################################################


