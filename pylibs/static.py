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
#cannot and won't allow overriding of __getattr__,__repr__, __str__ at
#class level
#cannot override __getattr__/__setattr__... yet
import types

def Sisinstance(obj, dataClass):
    """returns 1 if obj is an instance of dataClass"""
    if not isinstance(obj, instance):
        raise TypeError, 'object %s is not a static instance' % repr(obj)
    return Sissubclass(obj._klass, dataClass)

def Sissubclass(sub, super):
    """returns 1 if sub is a PyDO subclass of super"""
    if not isinstance(sub, _StaticBase):
        raise TypeError, "first arg isn't a data class"
    if not isinstance(super, _StaticBase):
        raise TypeError, "second arg isn't a data class"
    if sub._klass == super._klass: return 1
    for sc in sub._superClasses:
        return Sissubclass(sc, super)

class _method:
    def __init__(self, obj, meth):
        self.obj = obj
        self.meth = meth

    def __repr__(self):
        return '<%s %s of %s>' % (
            self.__class__.__name__, self.meth.func_name, self.obj._klass)
        
class _unboundmethod(_method):
    def __call__(self, *args, **kw):
        if len(args) == 0 or not Sisinstance(args[0], self.obj):
            raise TypeError, ('unbound method must be called with '
                              'instance of subclass of %s 1st argument' %
                              self.obj._klass)
        return apply(self.meth, args, kw)

class _boundmethod(_method):
    def __call__(self, *args, **kw):
        return apply(self.meth, (self.obj,) + args, kw)

def _findInheritanceRule(klass):
    if klass._staticMethods.has_key('__class_init__'):
        return klass.static___class_init__

    for sc in klass._superClasses:
        f = _findInheritanceRule(sc)
        if f:
            return f
        
class instance:
    def __init__(self, klass, *args, **kw):
        self.__dict__['_getattr_recur_list'] = []
        self.__dict__['_klass'] = klass
        if self.__dict__['_klass']._instanceMethods.has_key('__init__'):
            apply(self.__getattr__('__init__'), args, kw)
    
    def __getattr__(self, attr):
        if attr in ('__getstate__', '__setstate__'):
            raise AttributeError, attr
        
        if not self.__dict__.has_key('_klass'):
            raise AttributeError, attr

        #instance method?
        meth = self.__dict__['_klass']._instanceMethods.get(attr)
        if meth:
            return _boundmethod(self, meth)

        #proxy back to class attributes
        if hasattr(self.__dict__['_klass'], attr):
            return getattr(self.__dict__['_klass'], attr)

        #try __getattr__ method
        # are we __getattr__ hook recursing?  If so, raise Attribute Error
        if attr in self.__dict__['_getattr_recur_list']:
            raise AttributeError, attr

        # if the have a getattr method
        if self.__dict__['_klass']._instanceMethods.has_key('__getattr__'):
            try:
                try:
                    #put attr onto recur list
                    self.__dict__['_getattr_recur_list'].append(attr)
                    #call getattr
                    return _boundmethod(self, self.__dict__['_klass'].
                                        _instanceMethods['__getattr__'])(attr)
                except AttributeError:
                    pass
            finally:
                #make sure we pop current attribute off the recur list
                self.__dict__['_getattr_recur_list'].pop()

        #we didn't find anything, blow
        raise AttributeError, attr

    def __setattr__(self, attr, value):
        k = self.__dict__['_klass']
        #if they have a setattr hook, call it
        if k._instanceMethods.has_key('__setattr__'):
            _boundmethod(self, k._instanceMethods['__setattr__'])(attr, value)
        else: #otherwise, normal behavior
            self.__dict__[attr] = value
            
class _StaticBase:
    def __init__(self, klass = None, superClasses = (), dict = {}):
        self._modname = _getModName()
        self._klass = klass
        self._superClasses = superClasses
        self._dict = dict

        self._instanceMethods = {}
        self._staticMethods = {}
        self._classAttributes = {}
        for k, v in dict.items():
            if type(v) in (types.MethodType, types.FunctionType):
                if k[:7] == 'static_':
                    self._staticMethods[k[7:]] = v
                else:
                    self._instanceMethods[k] = v
            else:
                self._classAttributes[k] = v

        meth = _findInheritanceRule(self)
        if meth:
            meth(self)
        
    def __repr__(self):
        return '<static class %s at %x>' % (self._klass, id(self))

    def __str__(self):
        return repr(self)

    def __getattr__(self, attr):
        #try static method, bound
        meth = self._staticMethods.get(attr)
        if meth: return _boundmethod(self, meth)

        #try static method, unbound
        if attr[:7] == 'static_':
            meth = self._staticMethods.get(attr[7:])
            if meth: return meth

        #try unbound instance method
        if self._instanceMethods.has_key(attr):
            return _unboundmethod(self, self._instanceMethods[attr])

        #try class attribute
        if self._classAttributes.has_key(attr):
            return self._classAttributes[attr]
        raise AttributeError, attr

    def __getstate__(self):
        return {'_klass': self._klass, '_modname': self._modname}

    def __setstate__(self, arg):
        self._klass = arg['_klass']
        self._modname = arg['_modname']
        _updateMe(self)

def _getModName():
    S = "someexc"
    import sys
    try:
        raise S, S
    except:
        t, v, tb = sys.exc_info()
        return tb.tb_frame.f_back.f_back.f_globals['__name__']
        
def _updateMe(obj):
    import sys

    m = sys.modules.get(obj._modname)
    if not m:
        m = __import__(obj._modname, None, None, 1)

    if hasattr(m, obj._klass):
        co = getattr(m, obj._klass)
        if isinstance(co, _StaticBase):
            obj.__dict__.update(co.__dict__)
            return
    raise "static.error", 'cannot load static class %s' % obj._klass
                
            
_static = _StaticBase()

class static(_static):    
    def __repr__(self):
        return '<instance of static class %s at %x>' % (
            self._klass._klass, id(self))
    
    def static___call__(self, *args, **kw):
        return apply(instance, (self,) + args, kw)

    def static___class_init__(self):
        oldim = self._instanceMethods
        oldsm = self._staticMethods
        oldca = self._classAttributes
        
        self._instanceMethods = {}
        self._staticMethods = {}
        self._classAttributes = {}
        
        scs = list(self._superClasses)
        scs.reverse()

        for sc in scs:
            if not isinstance(sc, _StaticBase):
                raise TypeError, 'cannot inherit from non static base class'
            self._instanceMethods.update(sc._instanceMethods)
            self._staticMethods.update(sc._staticMethods)
            self._classAttributes.update(sc._classAttributes)
        self._instanceMethods.update(oldim)
        self._staticMethods.update(oldsm)
        self._classAttributes.update(oldca)

