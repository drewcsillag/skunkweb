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
    char *path;
    int len;
    struct str {
	char *s;
	int len;
    };

    struct str *parts;
    int partslen = 0;

    struct str *newparts;
    int newpartslen = 0;

    char *newpath;
    int newpathlen = 0;

    int i;
    int lastpartstart = 0;

    PyObject *ret;
    if (!PyArg_ParseTuple(arg, "s#", &path, &len))
	return NULL;

#undef DEBUG
    parts = (struct str*)malloc( sizeof(struct str) * len );
    newparts = (struct str*)malloc( sizeof(struct str) * len );
    newpath = (char*)malloc( sizeof(char) * len + 1);
    
    /* do the string.split */
    for (i = 0; i < len; i++)
    {
	if (path[i] == '/')
	{
	    parts[partslen].s = path+lastpartstart;
	    parts[partslen].len = i - lastpartstart;
	    lastpartstart = i;
	    partslen++;
	}
    }
    parts[partslen].s = path+lastpartstart;
    parts[partslen].len = i - lastpartstart;
    partslen++;
#ifdef DEBUG
    {
	char temp[80];
	for (i = 0; i < partslen; i++)
	{
	    strncpy(temp, parts[i].s, parts[i].len);
	    temp[parts[i].len] = 0;
	    printf("len %d - %s\n", parts[i].len, temp);
	}
	puts("");
    }
#endif

    /* handle path stuff */
    for (i = 0; i < partslen; i++)
    {
	if (!strncmp(parts[i].s, "/", parts[i].len)
	    || !strncmp(parts[i].s, "/.", parts[i].len)
	    || !strncmp(parts[i].s, ".", parts[i].len))
	    continue;
	if (!strncmp(parts[i].s, "/..", parts[i].len)
	    || !strncmp(parts[i].s, "..", parts[i].len))
	{
	    if (newpartslen > 0)
		newpartslen--;
	    continue;
	}
	if (parts[i].s[0] == '/') /*trim off leading slashes*/
	{
	    newparts[newpartslen].s = parts[i].s+1;
	    newparts[newpartslen].len = parts[i].len-1;
	}
	else
	{
	    newparts[newpartslen].s = parts[i].s;
	    newparts[newpartslen].len = parts[i].len;
	}
	newpartslen++;
    }

#ifdef DEBUG
    {
	char temp[80];
	for (i = 0; i < newpartslen; i++)
	{
	    strncpy(temp, newparts[i].s, newparts[i].len);
	    temp[newparts[i].len] = 0;
	    printf("len %d - %s\n", newparts[i].len, temp);
	}
	puts("");
    }
#endif

    /* glue shit back together */
    /*if path had a leading slash, the new one should too */
    if (path[0] == '/') 
    {
	newpath[0] = '/';
	newpathlen = 1;
    }
    for (i = 0; i < newpartslen; i++)
    {
	memcpy(newpath + newpathlen, newparts[i].s, newparts[i].len);
	newpathlen += newparts[i].len;

	if (i < (newpartslen -1 ))
	{
	    memcpy(newpath + newpathlen, "/", 1);
	    newpathlen++;
	}

    }
    if (path[len-1] == '/')
    {
	memcpy(newpath + newpathlen, "/", 1);
	newpathlen++;
    }
    newpath[newpathlen] = 0;
#ifdef DEBUG
    printf("newpath=%s\n", newpath);
    printf("newpathlen = %d len = %d\n", newpathlen, len);
#endif 
    ret = PyString_FromStringAndSize(newpath, newpathlen);
    free(newpath);
    free(parts);
    free(newparts);
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
