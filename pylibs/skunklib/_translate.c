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
/*
 * This is the C implementation of pathtranslate function - we use it rather
 * often in our code
 *
 * $Id: _translate.c,v 1.5 2001/07/09 20:38:41 drew Exp $
 */

#include "Python.h"

#include <ctype.h>

PyObject *_translate_pathtranslate ( PyObject *self, PyObject *args,
                                     PyObject *kwargs )
/*
 * Usage: translate ( path, map, sep = "/." )
 */
{
    char *path = NULL, *sep = "/.";
    PyObject *ret, *dict, *val;
    
    /* Variable length buffer */
    size_t i, j = 0, now = 0, end = BUFSIZ;
    char *out = malloc ( end ), *s, *ourpath;
    char delim;

    /* The argument list */
    static char *kwlist[] = { "path", "map", "sep", NULL };

    if ( !PyArg_ParseTupleAndKeywords ( args, kwargs, "sO!|s", kwlist, 
                                        &path, &PyDict_Type, &dict, &sep ) )
        return NULL;

    /* Path is mutated in process - make a copy */
    ourpath = strdup( path );

    for ( i = strcspn ( ourpath + j, sep ); i + j <= strlen(path); 
          i = strcspn ( ourpath + j, sep ))
    {
        /* Get the separator character */
        if ( (delim = ourpath[i+j]) != '\0' )
            ourpath[i+j] = '\0';

        /* The segment is from path + j to i */
        if ( (val = PyDict_GetItemString ( dict, ourpath + j )) )
        {
            /* Translate and copy */
            if ( !(PyString_Check(val)) )
            {
                PyErr_SetString ( PyExc_ValueError, "mapping should contain "
                                                    "string values only" );
                return NULL;
            }

            s = PyString_AS_STRING(val);
        }
        else
        {
            /* No translation, plain copy */
            s = ourpath + j;
        }

        /* Reallocate if necessary */
        while ( now + strlen(s) + 2 > end )
            out = realloc ( out, (end = end + BUFSIZ) );

        /* Copy the new value */
        strcpy ( out + now, s );

        now += strlen(s);
        out[now++] = delim;           /* Add the separator or '\0'*/

        /* Increment j */
        j += i + 1;
    }

    /* Create the return value */
    ret = PyString_FromString ( out );

    free ( out );
    free ( ourpath );

    return ret;
}

/*
 * Define our methods 
 */
static PyMethodDef _translate_methods[] = {
    { "pathtranslate", (PyCFunction) _translate_pathtranslate, 
                                  METH_VARARGS|METH_KEYWORDS },
    { NULL, NULL }
};

void init_translate(void)
{
    Py_InitModule ( "_translate", _translate_methods );
}
