/*  
  Copyright (C) 2001 Andrew T. Csillag <drew_csillag@geocities.com>
  
      You may distribute under the terms of either the GNU General
      Public License or the SkunkWeb License, as specified in the
      README file.
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
