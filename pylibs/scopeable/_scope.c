/* 
 * $Id: _scope.c,v 1.3 2001/09/04 17:23:55 smulloni Exp $ 
 * Time-stamp: <01/09/04 13:51:16 smulloni>
 */

/***********************************************************************
 *
 *  Copyright (C) 2001 Jacob Smullyan <smulloni@smullyan.org> 
 *                     and Drew Csillag <drew_csillag@geocities.com>
 *  
 *      This program is free software; you can redistribute it and/or modify
 *     it under the terms of the GNU General Public License as published by
 *     the Free Software Foundation; either version 2 of the License, or
 *     (at your option) any later version.
 *  
 *     This program is distributed in the hope that it will be useful,
 *      but WITHOUT ANY WARRANTY; without even the implied warranty of
 *      MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *      GNU General Public License for more details.
 *  
 *      You should have received a copy of the GNU General Public License
 *      along with this program; if not, write to the Free Software
 *      Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111, USA.
 *
 ***********************************************************************/
   
/*
 *  an object that transforms itself depending on its environment.
 */


#include <Python.h>

/* #define MYDEBUG  */

#define DICTLIST "_Scopeable__dictList"
#define CURRENT_SCOPES "_Scopeable__currentScopes"
#define MASH "_Scopeable__mash"
#define MATCHERS "matchers"
#define GET_DICTLIST(self) (PyMapping_GetItemString(((PyInstanceObject *)self)->in_dict, DICTLIST))

/* 
 * lifted from Frederik Lundh's exceptions.c;
 * he says: "Use this for *args signatures, otherwise just 
 * use PyArg_ParseTuple()"
 */
static PyObject *getSelf(PyObject *args) {
    PyObject *self = PyTuple_GetItem(args, 0);
    if (!self) {
	/* Watch out for being called to early in the bootstrapping process */
	if (PyExc_TypeError) {
	    PyErr_SetString(PyExc_TypeError,
	     "unbound method must be called with instance as first argument");
	}
        return NULL;
    }
    return self;
}

static PyObject  *Scopeable_init(PyObject *self, PyObject *args) {
  PyObject *dict=NULL;
  PyObject *dictList=PyList_New(0);
  PyObject *matchers=PyList_New(0);
  PyObject *currentScopes=PyDict_New();
  PyArg_ParseTuple(args, "O|O", &self, &dict);
  if (dict == NULL) {
    dict=PyDict_New();
    Py_INCREF(dict);
  }
  else if (!PyDict_Check(dict)) {
    PyErr_SetString(PyExc_TypeError, "a dictionary was expected");
    return NULL;
  }
  PyList_Append(dictList, dict);

  Py_INCREF(dictList);
  Py_INCREF(matchers);
  Py_INCREF(currentScopes);
  PyObject_SetAttrString(self, DICTLIST, dictList);
  PyObject_SetAttrString(self, MATCHERS, matchers);
  PyObject_SetAttrString(self, CURRENT_SCOPES, currentScopes);
  Py_INCREF(Py_None);
  PyObject_SetAttrString(self, MASH, Py_None);
  Py_INCREF(Py_None);
  return Py_None;
}

static void _mergeDefaults(PyObject *self, PyObject *dict) {
  PyObject *dictList=PyObject_GetAttrString(self, DICTLIST);
  PyObject *lastDict;
  PyObject *key, *value;
  int len, lastIndex;
  int pos=0;
  if (!PyList_Check(dictList)) {
    PyErr_SetString(PyExc_TypeError, "dictList is supposed to be a list!");
    return;
  }
#ifdef MYDEBUG
  printf("in _mergeDefaults\n");
#endif
  if (!(len=PyList_GET_SIZE(dictList))){
    PyObject *newDict=PyDict_New();
    Py_INCREF(newDict);
    PyList_Append(dictList, newDict);
    len++;
  }
  lastIndex=len-1;
  lastDict=PyList_GET_ITEM(dictList, lastIndex);
  assert(PyDict_Check(lastDict));
  assert(PyDict_Check(dict));
  while (PyDict_Next(lastDict, &pos, &key, &value)) {
    PyDict_SetItem(dict, key, value);
  }
  PyList_SetItem(dictList, lastIndex, dict);
  Py_INCREF(dict);
  Py_INCREF(dictList);
}

static PyObject *Scopeable_mergeDefaults(PyObject *self, 
					 PyObject *args, 
					 PyObject *kwargs) {
  int len, i;
  len=PyTuple_Size(args);
  if (!(self=getSelf(args))) {
    return NULL;
  }
  for (i=1;i<len;i++) {
    
    PyObject *dict=PySequence_GetItem(args, i);
    if (!PyDict_Check(dict)) {
      PyErr_SetString(PyExc_TypeError, 
		      "Scopeable.mergeDefaults: expected a dictionary");
      return NULL;
    }
    Py_INCREF(dict);
    _mergeDefaults(self, dict);

  }
  if (kwargs && PyObject_IsTrue(kwargs)) {
    _mergeDefaults(self, kwargs);
  }
  Py_INCREF(Py_None);
  return Py_None;
}

static void _resetMash(PyObject *self) {
  PyObject *d=PyDict_New();
  Py_INCREF(d);
  PyObject_SetAttrString(self, MASH, d);
}

static PyObject *Scopeable_mash(PyObject *self, PyObject *args) {
  PyObject *nd, *dictList, *dlCopy;
  int i,len;
  if (!(self=getSelf(args))) {
    return NULL;
  }
#ifdef MYDEBUG
  printf("in mash()\n");
#endif
  nd=PyDict_New();
  Py_INCREF(nd);
  dictList=PyObject_GetAttrString(self, DICTLIST);
  len=PyList_Size(dictList);
  dlCopy=PyList_GetSlice(dictList, 0, len);
  Py_INCREF(dlCopy);

  for (i=len-1;i>=0;i--) {
    PyObject *d, *key, *value;
    int pos=0;
    d=PyList_GetItem(dlCopy, i);
    if (!PyDict_Check(d)) {
      PyErr_SetString(PyExc_TypeError, "dictionary expected inside dictList");
      return NULL;
    }
    Py_INCREF(d);
    while (PyDict_Next(d, &pos, &key, &value)) {
      PyDict_SetItem(nd, key, value);
      Py_INCREF(key);
      Py_INCREF(value);
    }
    Py_DECREF(d);
  }
  Py_DECREF(dlCopy);
  return nd;
}

static PyObject *Scopeable_saveMash(PyObject *self, PyObject *args) {
  if (!(self=getSelf(args))) {
    return NULL;
  }
  PyObject_SetAttrString(self, MASH, Scopeable_mash(self, args));
  Py_INCREF(Py_None);
  return Py_None;
}

static PyObject *Scopeable__getattr__(PyObject *self, PyObject *args) {
  char *attrname;
  PyObject *realSelf, *val=NULL, *inDict, *masher;
  if (!PyArg_ParseTuple(args, "Os", &realSelf, &attrname)) {
    printf("oops!\n");
    return NULL;
  }
#ifdef MYDEBUG
  printf("in getattr\n");
#endif
  inDict=((PyInstanceObject *)realSelf)->in_dict;
  masher=PyMapping_GetItemString(inDict, MASH);

  if (PyObject_IsTrue(masher) 
      && PyMapping_HasKeyString(masher, attrname)) {
    val=PyMapping_GetItemString(masher, attrname);
  } 
  else {
    PyObject *dictList;
    int len, i;

    dictList=PyMapping_GetItemString(inDict, DICTLIST);    
    len=PyList_Size(dictList);

    for (i=0;i<len;i++) {
      PyObject *d=PyList_GetItem(dictList, i);
      if (PyMapping_HasKeyString(d, attrname)) {
	val=PyMapping_GetItemString(d, attrname);
	break;
      }
    }
  }  
  if (val==NULL) {
    /* check for special attribute "__all__" */
    char *allattr="__all__";
    if (!strncmp(attrname, allattr, strlen(allattr))) {
      PyObject *newargs=PyTuple_New(1);
      PyTuple_SetItem(newargs, 0, realSelf);
      PyObject *mashed=Scopeable_mash(self, newargs);
      PyObject *keys=PyMapping_Keys(mashed);
      Py_DECREF(mashed);
      val=keys;
    } else {
      PyErr_SetString(PyExc_AttributeError, attrname);
    }
  }
  if (val)
    Py_INCREF(val);
  return val;
}

static PyObject *_defaults(PyObject *self) {
  PyObject *inDict, *dictList, *defaults;
  int len;
  inDict=((PyInstanceObject *)self)->in_dict;
  dictList=PyMapping_GetItemString(inDict, DICTLIST);
  if (!PyList_Check(dictList)) {
    return NULL;
  }
  len=PyList_Size(dictList);
  if (len) {
    defaults=PySequence_GetItem(dictList, len-1);
    Py_INCREF(defaults);
    return defaults;
  }
  Py_INCREF(Py_None);
  return Py_None;
}  

static PyObject *Scopeable_defaults(PyObject *self, PyObject *args) {

  if (!PyArg_ParseTuple(args, "O", &self)) {
    return NULL;
  }
  Py_INCREF(self);
  return _defaults(self);
}

static PyObject *Scopeable_update(PyObject *self, PyObject *args) {
  PyObject *newDict, *defaults, *key, *value;
  int pos;
  if (!PyArg_ParseTuple(args, "OO", &self, &newDict)) {
    return NULL;
  }
  if (!PyDict_Check(newDict)) {
    PyErr_SetString(PyExc_TypeError, "a dictionary is expected for update");
    return NULL;
  }
  defaults=_defaults(self);
  if (PyObject_IsTrue(defaults)) {
    pos=0;
    while (PyDict_Next(newDict, &pos, &key, &value)) {
      PyDict_SetItem(defaults, key, value);
    }
    _resetMash(self);
  }
  Py_DECREF(defaults);
  Py_INCREF(self);
  Py_INCREF(Py_None);
  return Py_None;
}

static PyObject *Scopeable_push(PyObject *self, PyObject *args) {
  PyObject *newDict, *dictList;
  if (!PyArg_ParseTuple(args, "OO", &self, &newDict)) {
    return NULL;
  }
  Py_INCREF(self);
  if (!PyDict_Check(newDict)) {
    PyErr_SetString(PyExc_TypeError, "push() requires a dictionary argument");
    return NULL;
  }
  dictList=PyMapping_GetItemString(((PyInstanceObject *)self)->in_dict, DICTLIST);
  if (!PyList_Check(dictList)) {
    PyErr_SetString(PyExc_TypeError, "expected list for dictList!");
    Py_XDECREF(dictList);
    return NULL;
  }
  PyList_Insert(dictList, 0, newDict);
  
  Py_INCREF(Py_None);
  return Py_None;
}

static PyObject *Scopeable_pop(PyObject *self, PyObject *args) {
  PyObject *dictList, *popped, *ndl;
  int len;
  if (!PyArg_ParseTuple(args, "O", &self)) {
    return NULL;
  }
  Py_INCREF(self);
  dictList=GET_DICTLIST(self);
  len=PyList_Size(dictList);
  if (len) {
    popped=PyList_GetItem(dictList, len-1);
    Py_INCREF(popped);
    ndl=PyList_GetSlice(dictList, 0, len-1);
    Py_INCREF(ndl);
    PyMapping_SetItemString(((PyInstanceObject *)self)->in_dict, DICTLIST, ndl);
    /*    Py_DECREF(dictList); */
    _resetMash(self);
    return popped;
  }
  PyErr_SetString(PyExc_IndexError, "pop from empty list");
  Py_DECREF(dictList); 
  return NULL;
  
}  

static PyObject *Scopeable_trim(PyObject *self, PyObject *args) {
  PyObject *dictList, *newList;
  int len;
  if (!PyArg_ParseTuple(args, "O", &self)) {
    return NULL;
  }
  Py_INCREF(self);
  dictList=GET_DICTLIST(self);
  len=PyList_Size(dictList);
  if (len>1) {
    newList=PyList_GetSlice(dictList, 0, len-1);
    Py_INCREF(newList);
    PyMapping_SetItemString(((PyInstanceObject *)self)->in_dict, DICTLIST, newList);
    _resetMash(self);
  }
  /*  Py_DECREF(dictList); */
  Py_INCREF(Py_None);
  return Py_None;
}

static PyObject *Scopeable_mashSelf(PyObject *self, PyObject *args) {
  PyObject *newList, *mashed;
  if (!PyArg_ParseTuple(args, "O", &self)) {
    return NULL;
  }
  Py_INCREF(self);
  mashed=Scopeable_mash(self, args);
  newList=PyList_New(1);
  PyList_SetItem(newList, 0, mashed);
  PyMapping_SetItemString(((PyInstanceObject *)self)->in_dict, DICTLIST, newList);
  Py_INCREF(Py_None);
  return Py_None;
}

static PyObject *Scopeable_addScopeMatchers(PyObject *self, PyObject *args) {
  PyObject *matchers;
  int len=PyTuple_Size(args)-1;
  int i;
  if (!(self=getSelf(args))) {
    return NULL;
  }
  matchers=PyObject_GetAttrString(self, MATCHERS);
  if (!PyList_Check(matchers)) {
    PyErr_SetString(PyExc_TypeError, "internal type error");
    Py_XDECREF(matchers);
    return NULL;
  }
  if (len) {
    for (i=0;i<len;i++) {
      PyObject *newMatcher=PySequence_GetItem(args, i+1);
      Py_INCREF(newMatcher);
      PyList_Append(matchers, newMatcher);
    }
    PyList_Sort(matchers);
  }
  Py_INCREF(Py_None);
  return Py_None;
}

/* static PyObject *Scopeable_processMatcher(PyObject *self,  */
/* 					  PyObject *args) { */
/*   PyErr_SetString(PyExc_NotImplementedError, "not implemented"); */
/*   return NULL; */
/* } */

/* static PyObject *Scopeable_scope(PyObject *self, PyObject *args) { */
/*   PyObject *param=NULL; */
/*   PyObject *curScopes=PyObject_GetAttrString(self, CURRENT_SCOPES); */
/*   if (!PyArg_ParseTuple(args, "O|O", &self, &param)) { */
/*     return NULL; */
/*   } */
/*   Py_INCREF(self); */
  /*  treat as an accessor for all the current scopes */ 
/*   if (param==NULL || param==Py_None) { */
/*     Py_INCREF(curScopes); */
/*     return curScopes; */
/*   } */
/*   else if (!PyDict_Check(param)) { */
    /* treat as accessor for the scope with key param */ 
/*     if (PyDict_HasKey(curScopes, param)) { */
/*       PyObject *val=PyDict_GetItem(curScopes, param); */
/*       Py_INCREF(val); */
/*       return val; */
/*     } */
/*     Py_INCREF(Py_None); */
/*     return Py_None; */
/*   } */
/*   else { */
     /* treat as mutator */
/*     PyObject *scopedDict, *matchers; */
/*     PyObject *key, *value; */
/*     int pos=0, matcherLen, i; */
/*     while (PyDict_Next(param, &pos, &key, &value)) { */
/*       PyDict_SetItem(curScopes, key, value); */
/*     } */
/*     scopedDict=PyDict_New(); */

/*     matchers=PyObject_GetAttrString(self, MATCHERS); */
/*     if (!PyList_Check(matchers)) { */
/*       PyErr_SetString(PyExc_TypeError, "matchers should be a list"); */
/*       return NULL; */
/*     } */
/*     matcherLen=PyList_Size(matchers); */
/*     for (i=0;i<matcherLen;i++) { */
/*       PyObject *matcher=PyList_GET_ITEM(matchers, i); */
/*       PyObject *argTuple=PyTuple_New(4); */
/*       PyTuple_SET_ITEM(argTuple, 0, self); */
/*       PyTuple_SET_ITEM(argTuple, 1, matcher); */
/*       PyTuple_SET_ITEM(argTuple, 2, scopedDict); */
/*       PyTuple_SET_ITEM(argTuple, 3, param); */
/*       Scopeable_processMatcher(NULL, argTuple); */
/*     } */
/*     if (PyDict_Size(scopedDict)) { */
/*       Py_INCREF(scopedDict); */
/*       PyList_Insert(GET_DICTLIST(self), 0, scopedDict); */
/*     } */
/*     Py_INCREF(Py_None); */
/*     return Py_None; */
/*   } */
/* } */
    
static PyMethodDef ScopeableMethods[] = {
  {"__init__", Scopeable_init, METH_VARARGS, ""},
  {"mergeDefaults", Scopeable_mergeDefaults, METH_KEYWORDS, ""},
  {"__getattr__", Scopeable__getattr__, METH_VARARGS, ""},
  {"mash", Scopeable_mash, METH_VARARGS, ""},
  {"saveMash", Scopeable_saveMash, METH_VARARGS, ""},
  {"defaults", Scopeable_defaults, METH_VARARGS, ""},
  {"update", Scopeable_update, METH_VARARGS, ""},
  {"push", Scopeable_push, METH_VARARGS, ""},
  {"pop", Scopeable_pop, METH_VARARGS, ""},
  {"trim", Scopeable_trim, METH_VARARGS, ""},
  {"mashSelf", Scopeable_mashSelf, METH_VARARGS, ""},
  {"addScopeMatchers", Scopeable_addScopeMatchers, METH_VARARGS, ""},
  /*  {"scope", Scopeable_scope, METH_VARARGS, ""}, */
  {NULL},
};

static PyMethodDef ModuleMethods[] = { {NULL} };

void init_scope() {
  PyMethodDef *def;

  PyObject *module=Py_InitModule("_scope", ModuleMethods);
  PyObject *moduleDict=PyModule_GetDict(module);
  PyObject *classDict=PyDict_New();
  PyObject *className = PyString_FromString("Scopeable");
  PyObject *scopeableClass = PyClass_New(NULL, classDict, className);
  PyDict_SetItemString(moduleDict, "Scopeable", scopeableClass);
  Py_DECREF(classDict);
  Py_DECREF(className);
  Py_DECREF(scopeableClass);

  for (def = ScopeableMethods; def->ml_name != NULL; def++) {
    PyObject *func=PyCFunction_New(def, NULL);
    PyObject *method= PyMethod_New(func, NULL, scopeableClass);
    PyDict_SetItemString(classDict, def->ml_name, method);
    /* 
     * this would normally happen in PyClass_New() if the classDict
     * were already populated; but I'm passing it an empty dict
     */
    if (!strncmp(def->ml_name, "__getattr__", strlen("__getattr__"))) {
      ((PyClassObject *)scopeableClass)->cl_getattr=method;
    }
    Py_DECREF(func);
    Py_DECREF(method);
  }
}

/************************************************************************
 * $Log: _scope.c,v $
 * Revision 1.3  2001/09/04 17:23:55  smulloni
 * fix to mergeDefaults(), which was bombing out.
 *
 * Revision 1.2  2001/09/04 04:06:17  smulloni
 * removed segfault-producing Py_DECREF
 *
 * Revision 1.1  2001/09/03 23:08:32  smulloni
 * first draft of c version of scopeable object; raw, leaks like hog, if hogs
 * leak.
 *
 ************************************************************************/
