/*  
  Copyright (C) 2001 Andrew T. Csillag <drew_csillag@geocities.com>
  
      You may distribute under the terms of either the GNU General
      Public License or the SkunkWeb License, as specified in the
      README file.
*/   
#include "dav_opaquelock.h"
#include "Python.h"

static PyObject*
uuid_getuuid(PyObject* self, PyObject* args)
{
    PyObject* ret;
    char* lt;
    uuid_state st;
    uuid_t u;

    if (!PyArg_ParseTuple(args, ""))
	return NULL;
    
    dav_create_uuid_state(&st);
    dav_create_opaquelocktoken(&st, &u);
    lt = dav_format_opaquelocktoken(&u);
    ret = PyString_FromString(lt);
    free(lt);
    return ret;
}


static PyMethodDef uuid_methods[] = {
    {"uuid", uuid_getuuid, 1},
    {NULL, NULL},
};


void init_uuid(void)
{
    Py_InitModule("_uuid", uuid_methods);
}
    
