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
#include <Python.h>
#include <signal.h>

#define PY_FUNC(mname) static PyObject *mname(PyObject *self, PyObject *args)

PY_FUNC(blockTERM) {
    sigset_t set;
    int rc;

    if (!PyArg_ParseTuple(args, ""))
	return NULL;
    sigemptyset(&set);
    sigaddset(&set, SIGTERM);
    rc=sigprocmask(SIG_BLOCK, &set, NULL);
    if (rc == -1)
    {
	PyErr_SetString(PyExc_SystemError,
			"something went wrong doing sigprocmask");
	return NULL;
    }

    Py_INCREF(Py_None);
    return Py_None;
}

PY_FUNC(unblockTERM) {
    sigset_t set;
    int rc;

    if (!PyArg_ParseTuple(args, ""))
	return NULL;
    sigemptyset(&set);
    sigaddset(&set, SIGTERM);
    rc=sigprocmask(SIG_UNBLOCK, &set, NULL);
    if (rc == -1)
    {
	PyErr_SetString(PyExc_SystemError,
			"something went wrong doing sigprocmask");
	return NULL;
    }

    Py_INCREF(Py_None);
    return Py_None;
}

static PyMethodDef signal_plus_methods[] = {
    { "blockTERM", blockTERM, 1},
    { "unblockTERM", unblockTERM, 1},
    { NULL, NULL }
};

void initsignal_plus(void)
{
    Py_InitModule("signal_plus", signal_plus_methods);
}
