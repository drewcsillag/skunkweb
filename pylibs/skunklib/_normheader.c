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
#include "Python.h"
#include <ctype.h>

static PyObject* 
normheader(PyObject *self, PyObject *args)
{
    char *nstr;
    int nlen;
    char *newstr;
    int upflag = 1;
    int i;
    PyObject* ret;

    if (!PyArg_ParseTuple(args, "s#", &nstr, &nlen))
	return NULL;

    newstr = malloc(nlen+1);
    for (i = 0; i<nlen; i++)
    {
	if (upflag) 
	{
	    newstr[i] = toupper(nstr[i]);
	    upflag=0;
	}
	else
	{
	    newstr[i] = tolower(nstr[i]);
	    if (nstr[i] == '-')
		upflag = 1;
	}

    }
    ret = PyString_FromStringAndSize(newstr,nlen);
    free(newstr);
    return ret; 
}

static PyMethodDef normheader_methods[] = {
    {"normheader", normheader, METH_VARARGS},
    {NULL, NULL}
};

void init_normheader(void)
{
    Py_InitModule("_normheader", normheader_methods );
}
