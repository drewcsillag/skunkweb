/*  
  Copyright (C) 2001 Andrew T. Csillag <drew_csillag@geocities.com>
  
      This program is free software; you can redistribute it and/or modify
      it under the terms of the GNU General Public License as published by
      the Free Software Foundation; either version 2 of the License, or
      (at your option) any later version.
  
      This program is distributed in the hope that it will be useful,
      but WITHOUT ANY WARRANTY; without even the implied warranty of
      MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
      GNU General Public License for more details.
  
      You should have received a copy of the GNU General Public License
      along with this program; if not, write to the Free Software
      Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111, USA.
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
    
