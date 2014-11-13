/*  
  Copyright (C) 2001 Andrew T. Csillag <drew_csillag@geocities.com>
  
      You may distribute under the terms of either the GNU General
      Public License or the SkunkWeb License, as specified in the
      README file.
*/   
/*
 * Move the urlencode() out of urllib - we use it too much
 *
 * $Id: _urllib.c 1795 2007-08-27 21:04:08Z smulloni $
 */

#include "Python.h"

#include <ctype.h>

static char * _quote_plus ( const char *s, const char *safe )
{
    const char *always_safe = "_,.-";
    const char *ptr, *end;
    char *outptr, *out;

    /* Allocate enough to hold the longest conversion */
    outptr = out = malloc ( strlen(s) * 3 + 1 );

    /* Ok, now we have the arguments - encode them */
    for ( ptr = s, end = s + strlen(s); ptr < end; ptr++ )
    {
        /* Check if it is safe */
        if ( isalnum ( *ptr ) || 
             strchr ( always_safe, *ptr ) || 
	     (safe && strchr ( safe, *ptr )) 
	   )
            *(outptr++) = *ptr;
        /* Convert spaces to '+' */
	else if ( *ptr == ' ' )
            *(outptr++) = '+';
	/* Not safe - convert */
	else
	    outptr += sprintf ( outptr, "%%%02x", *ptr ); /*outptr+=3*/
    }

    /* Terminate the string */
    *outptr = '\0';

    /* Need to be freed() afterwards!!! */
    return out;
}

static PyObject *_urllib_quote_plus ( PyObject *self, 
                                      PyObject *args, PyObject *kwargs )
{
    char *s = NULL, *safe = "/", *out;
    PyObject *ret;

    /* Implementation of the urllib's quote_plus function */
    static char *kwlist[] = { "s", "safe", NULL };

    if ( !PyArg_ParseTupleAndKeywords ( args, kwargs, "s|s", kwlist, 
                                         &s, &safe ) )
        return NULL;

    out = _quote_plus ( s, safe );

    /* Convert the output to python and return it */
    ret = PyString_FromString ( out );

    free ( out );

    return ret;
}

PyObject *_urllib_urlencode ( PyObject *self, PyObject *args )
{
    PyObject *k, *v, *ks, *vs=NULL;
    PyObject *dict, *ret;
    int i, koutlen, voutlen;
    size_t now = 0, end = BUFSIZ;
    char *kout, *vout, *out = malloc(end);

    /* Get the dict argument */
    if ( !PyArg_ParseTuple ( args, "O!", &PyDict_Type, &dict ) )
	return NULL;
    
    for ( i = 0; PyDict_Next ( dict, &i, &k, &v ); )
    {
	/* Get the string representations */
	if ( !(ks = PyObject_Str ( k )) || !(vs = PyObject_Str ( v )) )
        {
	    Py_XDECREF ( ks ); Py_XDECREF ( vs );
	    return NULL;
        }

	/* Get the encoded values */
	kout = _quote_plus ( PyString_AS_STRING (ks), "/" );
	vout = _quote_plus ( PyString_AS_STRING (vs), "/" );

	/* Free the strings */
	Py_DECREF ( ks ); Py_DECREF ( vs );

	koutlen = strlen( kout );
	voutlen = strlen( vout );
	/* Construct the output, reallocating array if needed */
	while ( now + koutlen + voutlen + 3 > end )
	    out = realloc ( out, (end += BUFSIZ) );

	now += snprintf ( out + now, end - now, "&%s=%s", kout, vout );

	/* Free the vars */
	free ( kout ); free ( vout );
    }

    /* NULL terminate */
    out[now] = '\0';

    /* Replace first '&' with '?' */
    if (out[0])  /* first char isn't null -- empty string */
	out[0] = '?';

    ret = PyString_FromString ( out );

    free ( out );

    return ret;
}

/*
 * Define our methods 
 */
static PyMethodDef _urllib_methods[] = {
    { "quote_plus", (PyCFunction) _urllib_quote_plus, 
                                  METH_VARARGS|METH_KEYWORDS },
    { "urlencode", _urllib_urlencode, METH_VARARGS },
    { NULL, NULL }
};

void init_urllib(void)
{
    Py_InitModule ( "_urllib", _urllib_methods );
}
