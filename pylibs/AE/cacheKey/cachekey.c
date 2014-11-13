/*  
  Copyright (C) 2001 Andrew T. Csillag <drew_csillag@geocities.com>
  
      You may distribute under the terms of either the GNU General
      Public License or the SkunkWeb License, as specified in the
      README file.
   
*/
/*
 * This is C implementation of the cache key generation and lookup algorithm 
 * used by SkunkWeb. We have moved this to C due to the fact that it is used 
 * extensively for virtually every request, and speedup here will be noticeable
 * on overall performance.
 *
 * Roman
 *
 * $Id: cachekey.c 1755 2006-05-22 19:23:01Z smulloni $
 */

#include "Python.h"

#define CVT_BUFSIZE 1024

static PyObject* encodeSingle(PyObject*);

static PyObject *encodeInstance(PyObject *obj)
{
    PyObject *class;
    PyObject *className;
    int has_cachekeymethod;
    int has_hashmethod;
    PyObject *ret;
    PyObject *methval;
    PyObject *methvalstr;

    has_cachekeymethod = PyObject_HasAttrString(obj, "__cachekey__");
    has_hashmethod = PyObject_HasAttrString(obj, "__hash__");
    if (!has_cachekeymethod && !has_hashmethod)
    {
	PyObject *terrstr;
	terrstr = PyObject_Str(obj);
	PyErr_Format(PyExc_ValueError, "each object used in a cache key "
		     "must define either a __cachekey__ or __hash__ method. "
		     "Got %s", PyString_AsString(terrstr));
	Py_DECREF(terrstr);
	/*  2.7ish
	PyErr_SetString(PyExc_ValueError, "each object used in a cache key"
			"must define either a __cachekey__ or __hash__ method"
			);
	*/
	return NULL;
    }
    class = PyObject_GetAttrString(obj, "__class__");
    className = PyObject_GetAttrString(class, "__name__");
    Py_DECREF(class);
    ret = PyString_InternFromString("Instance:");
    PyString_ConcatAndDel(&ret, className);
    PyString_ConcatAndDel(&ret, PyString_InternFromString("("));

    /* make a function which does the common bits here */
    if (has_cachekeymethod)
    {
	methval = PyObject_CallMethod(obj, "__cachekey__", NULL);
	if (!methval)
	{
	    Py_DECREF(ret);
	    return NULL;
	}
	if (methval == Py_None)
	{
	    PyErr_SetString(PyExc_ValueError, "__cachekey__ method returned"
			    " None!");
	    Py_DECREF(methval);
	    Py_DECREF(ret);
	    return NULL;
	}
	methvalstr = encodeSingle(methval);
	Py_DECREF(methval);
    }
    else /* has_hashmethod is 1 */
    {
	methval = PyObject_CallMethod(obj, "__hash__", NULL);
	if (!methval)
	{
	    Py_DECREF(ret);
	    return NULL;
	}
	methvalstr = encodeSingle(methval);
	Py_DECREF(methval);
    }
    PyString_ConcatAndDel(&ret, methvalstr);
    PyString_ConcatAndDel(&ret, PyString_InternFromString(")"));    
    return ret;
}

static PyObject *encodeCObject(PyObject *obj)
{
    PyObject* ob_type;
    PyObject* ob_type_str_obj;
    PyObject* res;
    PyObject* hash_str;
    PyObject* hash_int;

    if (obj->ob_type->tp_hash == NULL)
    {
	PyErr_SetString(PyExc_ValueError, "Native Object is not hashable");
	return NULL;
    }

    ob_type = PyObject_Type(obj);
    ob_type_str_obj = PyObject_Str(ob_type);
    Py_DECREF(ob_type);

    res=PyString_InternFromString("CObject:");
    PyString_ConcatAndDel(&res, ob_type_str_obj);
    hash_int = PyInt_FromLong(PyObject_Hash(obj));
    hash_str = PyObject_Str(hash_int);
    Py_DECREF(hash_int);
    PyString_ConcatAndDel(&res, PyString_InternFromString("|"));
    PyString_ConcatAndDel(&res, hash_str);
    return res;
}
	
	
static PyObject *encodeSingle( PyObject *obj )
{
    PyObject *ret;
    char buf[CVT_BUFSIZE];

    if (PyInt_Check(obj))
    {
	/* 
	   1024 bytes will be plenty, but I'm still paranoid, even though
	   a 64 byte integer is <= 20 bytes long
	*/
	snprintf(buf, CVT_BUFSIZE, "Int:%ld", PyInt_AS_LONG(obj));
	return PyString_FromString(buf);
    }
    if (PyString_Check(obj))
    {
	char *tmpbuf;  /* we're ansi, let's declutter */
	/* ahh, the wonders of CSE... */
	/* len("String:")+1 = 8, hence magic #s 8 and 7 (no null included) */
	tmpbuf = (char*)malloc(PyString_GET_SIZE(obj)+8);
	strcpy(tmpbuf, "String:");
	memcpy(tmpbuf+7, PyString_AS_STRING(obj), PyString_GET_SIZE(obj));
	ret = PyString_FromStringAndSize(tmpbuf, PyString_GET_SIZE(obj)+7);
	free(tmpbuf);
	return ret;
    }
    if (obj == Py_None)
	return PyString_InternFromString("None");

    if (PyFloat_Check(obj))
    {
	/*
	  again, as with ints, we shouldn't see much more than around
	  18 bytes out of this, but you can never be too sure
	*/
	snprintf(buf, CVT_BUFSIZE, "Float:%.12g", PyFloat_AS_DOUBLE(obj));
	return PyString_FromString(buf);
    }
		 
    if (PyLong_Check(obj))
    {
	PyObject *longstr;
	ret = PyString_InternFromString("Long:");
	longstr = PyObject_Str(obj);
	PyString_ConcatAndDel(&ret, longstr);
	return ret;
    }

    if (PyList_Check(obj) || PyTuple_Check(obj))
    {
	int i;
	PyObject *cur;
	if (PyList_Check(obj))
	    ret = PyString_InternFromString("List:[");
	else
	    ret = PyString_InternFromString("Tuple:[");
	for (i=0; i < PyObject_Length(obj); i++)
	{
	    /* put a nice little delimiter */
	    if (i > 0)
                PyString_ConcatAndDel(&ret, PyString_InternFromString ( "|"));
	    cur = PySequence_GetItem(obj, i);
	    PyString_ConcatAndDel(&ret, encodeSingle(cur));
	    Py_DECREF(cur); 
	}
	if (PyList_Check(obj))
	    PyString_ConcatAndDel(&ret, PyString_InternFromString("]"));
	else
	    PyString_ConcatAndDel(&ret, PyString_InternFromString(")"));
	return ret;
    }

    if (PyDict_Check(obj) )
    {
	PyObject* items;
        /* Just get the items and sort them */
        items = PyDict_Items(obj);
        if (PyList_Sort(items) == -1)
	{
	    Py_DECREF(items);
            return NULL;
	}

        ret = PyString_InternFromString("Dict:{");
	/* just stringify the items list o' tuples */
        PyString_ConcatAndDel(&ret, encodeSingle(items));
        PyString_ConcatAndDel(&ret, PyString_InternFromString("}"));

        /* Deref the items */
        Py_DECREF(items);

        return ret;
    }
    
    /* NEW 3.x */
    if (!strcmp(obj->ob_type->tp_name, "DateTime")) /*if a datetime obj*/
    {
	PyObject *dtstr;
	ret = PyString_InternFromString("DateTime:");
	dtstr = PyObject_Str(obj);
	PyString_ConcatAndDel(&ret, dtstr);
	return ret;
    }

    if (PyInstance_Check(obj))
	return encodeInstance(obj);

    if (PyClass_Check(obj))
    {
	PyErr_SetString(PyExc_ValueError, "class objects cannot be used"
			" as cache keys");
	return NULL;
    }
    /* else is some other C type */
    return encodeCObject(obj);
}


/*
 * A wrapper around encodeSingle exposed to python
 */
static PyObject *cachekey_encodeSingle ( PyObject *self, PyObject *args )
{
    PyObject *ptr, *res;

    if ( !PyArg_ParseTuple ( args, "O", &ptr ) )
        return NULL;

    res = encodeSingle(ptr);

    return res;
}
/*
 * The genCacheKey ( argdict ) function.
 *
 * The function takes one argument - an argument dictionary, and returns 
 * a tuple ( cachekey, fullkey ), where the cachekey is the actual value of
 * the cache key, and fullkey is extra information which can be used to do 
 * by-value cache clearing
 */
static PyObject *cachekey_genCacheKey ( PyObject *self, PyObject *args )
{
    PyObject *items, *item, *key, *value, *out_list, *out_dict, *cachekey,
             *md5_mod, *ptr, *md5_obj, *argdict;
    char buf[BUFSIZ], buf2[BUFSIZ], *s;
    int i;

    /* Extract the argdict */
    if ( !PyArg_ParseTuple ( args, "O!", &PyDict_Type, &argdict ) )
        return NULL;

    /* Get the items of argdict */
    items = PyDict_Items ( argdict );
    if ( PyList_Sort ( items ) == -1 )
        return NULL;

    /* Create the list to store encoded values */
    if ( !(out_list = PyList_New(PyList_Size(items))) )
        return NULL;

    /* Encode the items */
    for ( i = 0; i < PyList_Size ( items ); i++ )
    {
	PyObject* key_obj;
	PyObject* val_obj;
        /* Item is borrowed, no need to decref! */
        item = PyList_GetItem ( items, i );

        /* Get k:v - this increments refcount */
        key = PyTuple_GetItem ( item, 0 );
        value = PyTuple_GetItem ( item, 1 );

        /* Encode key / value and add them to output tuple */
	key_obj = encodeSingle(key);
	val_obj = encodeSingle(value);
	if (PyErr_Occurred())
	{
	    Py_XDECREF(key_obj);
	    Py_XDECREF(val_obj);
	    return NULL;
	}
        if ( !(item = Py_BuildValue ( "(NN)", key_obj, val_obj)))
            return NULL;

        /* Add the new item to output list */
        PyList_SetItem ( out_list, i, item );
    }

    /* Clear items */
    Py_DECREF ( items );

    /* Now, create the string from the items and MD5 it */
    if ( !(md5_mod = PyImport_ImportModule ( "md5" )) )
        return NULL;

    /* Get the 'new' function */
    if (!(ptr = PyDict_GetItemString ( PyModule_GetDict ( md5_mod ), "new")))
        return NULL;

    if ( !(md5_obj = PyObject_CallFunction ( ptr, NULL )) )
        return NULL;

    /* Got the md5 object, update it with the string and get the result */
    if ( !(PyObject_CallMethod ( md5_obj, "update", "(N)",
                                          PyObject_Str ( out_list )) ) )
        return NULL;

    if ( !(cachekey = PyObject_CallMethod ( md5_obj, "digest", NULL )) )
        return NULL;

    /* Deref md5 object */
    Py_DECREF ( md5_obj );

    /* Create out dictionary */
    out_dict = PyDict_New ();

    /* Ok, we have the cachekey - now create the fullkey dictionary */
    for ( i = 0; i < PyList_Size ( out_list ); i++ )
    {
        item = PyList_GetItem ( out_list, i );

        PyDict_SetItem ( out_dict, PyTuple_GetItem ( item, 0 ),
                                   PyTuple_GetItem ( item, 1 ) );
    }

    /* Decref the out_list list */
    Py_DECREF ( out_list );

    s = PyString_AS_STRING ( cachekey );
    buf[0] = '\0';

    for ( i = 0; i < PyString_Size(cachekey); i++ )
    {
        sprintf ( buf2, "%02X", (s[i] & 0xFF) );
        strcat ( buf, buf2 );
    }

    Py_DECREF(cachekey);

    return Py_BuildValue ( "(NN)", PyString_FromString(buf), out_dict );
}

/*
 * Define our methods 
 */
static PyMethodDef cachekey_methods[] = {
    { "genCacheKey", cachekey_genCacheKey, METH_VARARGS },
    { "encodeSingle", cachekey_encodeSingle, METH_VARARGS },
    { NULL, NULL }
};

void initcachekey()
{
    Py_InitModule ( "cachekey", cachekey_methods );
}
