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
static PyObject*
normpath(PyObject* self, PyObject* arg)
{
    char* path;
    int len;
    struct part {
	char* start;
	int len;
    };
    struct part* parts;
    struct part* newparts;
    int i;
    int arused=0;
    int newpartsused=0;
    char *newout;
    int newoutoff = 0;
    PyObject* ret;

    if (!PyArg_ParseTuple(arg, "s#", &path, &len))
	return NULL;
    
    parts = (struct part*)malloc(sizeof(struct part) * len);
    newparts = (struct part*)malloc(sizeof(struct part) * len);
    newout = (char*)malloc(len);

    /*basically, do a string.split of path into parts[]*/
    if (path[0] != '/')
    {
	parts[arused++].start=path;
    }
    for (i = 0; i < len; i++)
    {
	if (path[i] == '/')
	{
	    parts[arused].start =  &path[i+1];
	    if (arused)
		parts[arused-1].len = (parts[arused].start - 
		    parts[arused-1].start) - 1;
	    arused++;
	}
    }
    parts[arused-1].len = ((path + len) - parts[arused-1].start);

    
    for (i = 0; i < arused; i++)
    {
	/*if just a slash or /., ignore */
	if (!strncmp("", parts[i].start, parts[i].len)
	    || !strncmp(".", parts[i].start, parts[i].len))
	    continue;
	/*if .., trim off the last one added*/
	if (!strncmp("..", parts[i].start, parts[i].len)
	    && newpartsused)
	    newpartsused--;
	else
	{
	    newparts[newpartsused].start = parts[i].start;
	    newparts[newpartsused++].len = parts[i].len;
	}
    }      

    if (path[0] == '/')
    {
	newoutoff = 1;
	newout[0] = '/';
    }

    /*build new path string*/
    for (i = 0; i < newpartsused; i++)
    {
	memcpy(newout + newoutoff, newparts[i].start, newparts[i].len);
	newoutoff += newparts[i].len;
	if (i < (newpartsused-1))
	{
	    memcpy(newout + newoutoff, "/", 1);
	    newoutoff++;
	}
    }
    newout[newoutoff] = '\0';
    ret = PyString_FromStringAndSize(newout, newoutoff);
    free(parts);
    free(newparts);
    free(newout);
    return ret;
}

static PyMethodDef normpath_methods[] = {
    {"normpath", normpath, METH_VARARGS},
    {NULL, NULL}
};

void init_normpath(void)
{
    Py_InitModule("_normpath", normpath_methods);
}
