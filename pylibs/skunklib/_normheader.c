/*  
  Copyright (C) 2001 Andrew T. Csillag <drew_csillag@geocities.com>
  
      You may distribute under the terms of either the GNU General
      Public License or the SkunkWeb License, as specified in the
      README file.
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
