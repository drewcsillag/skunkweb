import fnmatch
import re
import types

class Scopeable:

    """
    a class for storing configuration data that needs to vary
    according to some set of arbitrary conditions.

    This is how it is used:

    >> s=Scopeable()
    >> s.mergeDefaults(foo=1, bar=2, spam=3, eggs=4)
    >> m=SimpleStringMatcher('location',
                            '/salad',
                            {'foo' : 999,
                             'bar' : 1111})
    >> s.addScopeMatchers(m)
    >> s.foo
    1
    >> s.bar
    2
    >> s.spam
    3
    >> s.scope({'location' : '/salad/caesar'})
    >> s.foo
    999
    >> s.bar
    1111
    >> s.spam
    3
    >> s.trim()
    >> s.foo
    1
    """
    
    _fridge={}
    def __init__(self, defaults=None):
        if defaults is None:
            defaults={}
        Scopeable._fridge[self]={'dictlist' : [],
                                 'defaults' : defaults,
                                 'currentScopes' : {},
                                 'scopeMatchers' : []}
        self.__dict__.update(defaults)
        
    def mergeDefaults(self, *dicts, **kw):
        """
        passed either a dictionary (or multiple dictionaries,
        which will be evaluated in order) or keyword arguments, will
        fold the key/value pairs therein into the dictionary of
        defaults without deleting any values that already exist there.
        Equivalent to: newDict.update(defaultDict) defaultDict=newDict
        """
        fridge=self._get_fridge()
        tmp=fridge['defaults']
        for d in dicts:
            d.update(tmp)
            tmp=d
        kw.update(tmp)
        fridge['defaults']=kw
        self.__dict__.update(kw)

    def _lookup(self, attr):
        # not really intended to be used,
        # the old gettattr hook
        fridge=self._get_fridge()
        dictlist=fridge['dictlist'][:]
        dictlist.reverse()
        for d in dictlist:
            try:
                return d[attr]
            except KeyError:
                continue
        try:
            return dictlist['defaults'][attr]
        except KeyError:
            pass
        # need a better exception for this
        raise AttributeError, attr        

    def updateDefaults(self, d):
        self._get_fridge()['defaults'].update(d)
        self.__dict__=self.mash()
        
    def defaults(self):
        return self._get_fridge()['defaults'].copy()

    def currentScopes(self):
        return self._get_fridge()['currentScopes']

    def scopeMatchers(self):
        return self._get_fridge()['scopeMatchers']

    def _get_fridge(self):
        return Scopeable._fridge[self]

    def mash(self):
        fridge=self._get_fridge()
        nd=fridge['defaults'].copy()
        map(nd.update, fridge['dictlist'])
        return nd

    def push(self, d):
        self._get_fridge()['dictlist'].append(d)
        self.__dict__.update(d)

    def pop(self):
        fridge=self._get_fridge()
        popped=fridge['dictlist'].pop()
        dl=fridge['dictlist'][:]
        dl.reverse()
        D=self.__dict__
        defaults=fridge['defaults']
        for k in popped.keys():
            del D[k]
            for d in dl:
                try:
                    v=d[k]
                except KeyError:
                    continue
                else:
                    D[k]=v
                    break
            try:
                v=defaults[k]
            except KeyError:
                pass
            else:
                D.setdefault(k, v)
                

    def trim(self):
        fridge=self._get_fridge()
        del fridge['dictlist'][:]
        self.__dict__.clear()
        self.__dict__.update(fridge['defaults'])

    def addScopeMatchers(self, *paramMatchers):
        matchers=self.scopeMatchers()
        matchers.extend(paramMatchers)
        matchers.sort()
        
    def scope(self, d):
        # store the current scope
        current=self.currentScopes()
        current.update(d)
        scopedDict={}
        for m in self.scopeMatchers():
            self.__processMatcher(m, scopedDict, d)                
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


                
