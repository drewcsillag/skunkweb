/*  
  Copyright (C) 2001 Andrew T. Csillag <drew_csillag@geocities.com>
  
      You may distribute under the terms of either the GNU General
      Public License or the SkunkWeb License, as specified in the
      README file.
*/

/* 
 *  $Id: mod_skunkweb.c,v 1.10 2003/05/01 20:45:56 drew_csillag Exp $
 *
 *
 * Configuration:
 * SkunkWebSocketAddress - socket address of where SkunkWeb is listening - is either
 *                    host:port or /path_to_unix_socket
 * SkunkWebRetries     - the number of times to try to connect to the daemon
 * SkunkWebErrorDoc    - the page to display when a critical error occurs
 * SkunkWebErrorEmails - the list of emails to notify on error
 * SkunkWebExclude     - list of uri prefixes for which mod_SkunkWeb should not 
 *                    intervene
 * SkunkWebFailoverHosts - space delimited list of socket addresses to try if 
 *                      connecting to primary one fails
 * SkunkWebConnectTimeout - number of milliseconds to wait for a connect to 
 *                    succeed before retrying
 *
 * 
 * If a hostname start with a '/', it is assumed to be for a unix-domain 
 * socket.  If SkunkWebHost is a unix socket, SkunkWebPort will be the default
 * port for TCP sockets in SkunkWebFailoverHosts. 
 * 
 * swapache protocol is the following:
 * 
 * us to SkunkWeb
 * -----------
 * space-padded length (%10d) of message
 * python format marshalled dict of stdin:string and environment dict, 
 * as well as the HTTP headers found in the request
 *
 *          { 
 *            'stdin': 'blahblah...',
 *            'environ': { 'this':'that',....},
 *            'headers': { 'name': 'value', ....} 
 *          }
 *
 *  SkunkWeb to us
 *  -----------
 *  space-padded length (%10d) of message
 * string containing header and body of return message
 *
 * ==== Latest protocol description
 *
 * The current protocol between client and server is such: (client starts
 * with C: and server starts with S:)
 * 
 * C: connect to server
 * 
 * S: send a handshake byte
 * 
 * C: get handshake byte, if not, go back to beginning
 * 
 * #the handshake byte is to overcome a race condition.  What happens is
 * that the server blocks SIGTERM once it gets a connection, although,
 * sometimes (during a server restart) it gets SIGTERM after it gets the
 * connection, but before it blocks it so the server process exits, but if
 * you get the handshake byte from the server, you know that SIGTERM is
 * blocked, and that everything is good to go.
 * 
 * C: construct request as marshalled dictionary of {'environ': <envdict>,
 * 'stdin': <text of stdin>, 'headers' : <headers dict>} and send to server 
 * as '%10s%s' % (len(request), request)
 * 
 * #at first it may seem baroque to have to send the length, but trust me,
 * you need it or sometimes weird shit can happen.
 * 
 * S: get request, demarshal, process request
 * 
 * S: send textual response as '%10s%s' % (len(response), response)
 * 
 * C: get response
 * 
 * S, C: close connection
 *====
 *
 * TODO: make sure this will continue to work when apache becomes
 * multithreaded, will need to add locks if necessary
 *
 * Originally written by Drew, modified by Roman
 */

/* Standard includes */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>
#include <unistd.h>

#include <sys/types.h>
#include <sys/socket.h>
#include <sys/un.h>
#include <netinet/in.h>
#include <sys/time.h>
#include <sys/syslog.h>

/* Apache includes */
#include "httpd.h"
#include "http_core.h"
#include "http_main.h"
#include "http_config.h"
#include "http_log.h"
#include "http_protocol.h"
#include "http_request.h"
#include "util_script.h"

/* when apache 2.0 becomes common usage, delete stuff between
   #if APACHEV1 and the #else and leave stuff between #else and #endif
*/
#ifdef APACHE_RELEASE
#if APACHE_RELEASE < 20000000
#define APACHEV1 1

#define SK_AP_RERROR1(mark, level, req, str) ap_log_rerror(mark, level, req, str)
#define SK_AP_RERROR2(mark, level, req, str, arg1) ap_log_rerror(mark, level, req, str, arg1)
#define SK_AP_RERROR3(mark, level, req, str, arg1, arg2) ap_log_rerror(mark, level, req, str, arg1, arg2)
#define SK_AP_RERROR4(mark, level, req, str, arg1, arg2, arg3) ap_log_rerror(mark, level, req, str, arg1, arg2, arg3)
#endif
#endif

#ifndef APACHEV1
/*OK, APACHE 2.0*/
#include <netdb.h>
#include <apr_strings.h>
#define ap_push_array apr_array_push
#define ap_make_array apr_array_make
#define ap_table_entry_t apr_table_entry_t
#define ap_table_get apr_table_get
#define ap_table_set apr_table_set
#define ap_file_t apr_file_t
#define ap_finfo_t apr_finfo_t
#define ap_stat apr_stat
#define ap_open apr_file_open 
#define ap_palloc apr_palloc
#define ap_array_header_t apr_array_header_t
#define ap_table_elts apr_table_elts
#define ap_array_pstrcat apr_array_pstrcat

#define ap_psprintf apr_psprintf
#define ap_pstrndup apr_pstrndup
#define ap_pstrdup apr_pstrdup
#define SK_AP_RERROR1(mark, level, req, str) ap_log_rerror(mark, level, 0, req, str)
#define SK_AP_RERROR2(mark, level, req, str, arg1) ap_log_rerror(mark, level, 0, req, str, arg1)
#define SK_AP_RERROR3(mark, level, req, str, arg1, arg2) ap_log_rerror(mark, level, 0, req, str, arg1, arg2)
#define SK_AP_RERROR4(mark, level, req, str, arg1, arg2, arg3) ap_log_rerror(mark, level, 0, req, str, arg1, arg2, arg3)

#endif


/*
   This is the marshalling component of the SkunkWeb apache module. The code
   here is based on the code in <PYTHON_SRC>/Python/marshal.c. It shouldn't 
   change frequently, and there is a significant performance gain from 
   generating the python objects on the server side. 
 */

/* 
   Binary buffer stuff to do stuff with strings with length as opposed to
   NULL terminated strings
 */
typedef struct binbuffer
{
    char *buf;
    size_t len;
} binbuffer;

/*create a new buffer object*/
static binbuffer* buffer_new(request_rec *r, char* buf, int len)
{
    binbuffer* b=ap_palloc(r->pool, sizeof(binbuffer));
    b->buf=buf;
    b->len=len;
    return b;
}

/*creates a new bin buffer from the "sum" of first and second*/
static binbuffer* buffer_cat(request_rec* r, const binbuffer *first, 
			     const binbuffer *second)
{
    char *x = ap_palloc(r->pool, first->len+second->len);
    memcpy(x, first->buf, first->len);
    memcpy(x+first->len, second->buf, second->len);

    return buffer_new(r, x, first->len+second->len);
}

/*
 * Marshalling routines, based on the code found in 
 * <PYTHON_SRC>/Python/marshal.c
 */

/* These are all the types which could be marshalled, the ones uncommented 
 * are the ones we're using 
 */
#define TYPE_NULL	"0"
#define TYPE_LONG	"l"
#define TYPE_DICT	"{"
#define TYPE_STRING	"s"

/*#define TYPE_NONE	'N'
#define TYPE_ELLIPSIS   '.'
#define TYPE_INT	'i'
#define TYPE_INT64	'I'
#define TYPE_FLOAT	'f'
#define TYPE_COMPLEX	'x'
#define TYPE_TUPLE	'('
#define TYPE_LIST	'['
#define TYPE_CODE	'c'
#define TYPE_UNKNOWN	'?'*/

	
/* marshalls a long
 * XXX - this may have to change when we go to long > 64 bits */
static binbuffer *marshal_long(long x, request_rec *r)
{
    char *area = ap_palloc(r->pool, 4);
    
    area[0]=( x      & 0xff);
    area[1]=((x>> 8) & 0xff);
    area[2]=((x>>16) & 0xff);
    area[3]=((x>>24) & 0xff);

    return buffer_new(r, area, 4);
}

/*marshalls a string with length*/
static binbuffer *marshal_string_l(const char *s, size_t n, 
                                        request_rec *r)
{
    char *area;

    area=ap_palloc(r->pool, 5+n);
    area[0] = TYPE_STRING[0];
    memcpy ( area+1, marshal_long(n,r)->buf, 4);
    memcpy ( area+5, s, n);
    return buffer_new(r, area, n+5);
}

/*marshalls a string*/
static binbuffer *marshal_string(const char *s, request_rec *r)
{
    return marshal_string_l(s, strlen(s), r);
}

/*marshalls a null object (needed for marshalling a dict*/
static binbuffer* marshal_null(request_rec* r)
{
    return buffer_new(r, TYPE_NULL, 1);
}

/* Begin a dictionary - returns a beginning of a dictionary */
static binbuffer *start_dict(request_rec *r)
{
    return buffer_new(r, TYPE_DICT, 1);
}

/* End a dictionary - write a last element to a dictionary */
static binbuffer *end_dict(request_rec *r, binbuffer *dict)
{
    return buffer_cat(r, dict, marshal_null(r) );
}

/* Add an object to a dictionary. */
static binbuffer *add_to_dict(request_rec *r, const binbuffer *dict,
                              const binbuffer *key, const binbuffer *val)
{
    return buffer_cat ( r, dict, buffer_cat ( r, key, val ) );
}

#ifdef APACHEV1
#define ap_array_header_t array_header
#define ap_table_entry_t table_entry
#endif

/* 
 * This routine marshalls everything and returns the string which could
 * be loaded in python with marshal.loads(). It is a dictionary in the form
 * { 'stdin' : '....', 'environ' : { 'key' : 'value', .... } }
 */
static binbuffer *marshal_all(request_rec* r, const binbuffer *stdin_buf)
{
    const char *env_name = "environ";
    const char *stdin_name = "stdin";
    const char *headers_name = "headers";
    binbuffer *dict, *env_dict, *headers_dict;
    int i;

    /* Setup the environment table for access */
    const ap_array_header_t *env_arr = ap_table_elts ( r->subprocess_env );
    ap_table_entry_t *env_elts = (ap_table_entry_t *)env_arr->elts;  /* iterator */

    /* Setup the headers-in for access */
    const ap_array_header_t *hdr_arr = ap_table_elts ( r->headers_in );
    ap_table_entry_t *hdr_elts = (ap_table_entry_t *)hdr_arr->elts;  /* iterator */

    /* Begin outer dictionary */
    dict = start_dict(r);

    /* Add stdin string */
    dict = add_to_dict ( r, dict, marshal_string(stdin_name, r),
                                  marshal_string_l(stdin_buf->buf,
                                                   stdin_buf->len, r) );

    /* Construct the environment dictionary */
    env_dict = start_dict(r);

    for ( i=0; i< env_arr->nelts; i++)
        if (env_elts[i].key)
            env_dict = add_to_dict ( r, env_dict, 
                                     marshal_string ( env_elts[i].key, r ),
                                     marshal_string ( env_elts[i].val, r ) );

    /* End the environment dictionary */
    env_dict = end_dict ( r, env_dict );

    dict = add_to_dict ( r, dict, marshal_string(env_name, r),
                         env_dict );

    /* Construct the headers dictionary - just pass the headers_in as is */
    headers_dict = start_dict ( r );

    for ( i=0; i < hdr_arr->nelts; i++ )
        if (hdr_elts[i].key)
            headers_dict = add_to_dict ( r, headers_dict, 
                                     marshal_string ( hdr_elts[i].key, r ),
                                     marshal_string ( hdr_elts[i].val, r ) );

    headers_dict = end_dict ( r, headers_dict );

    /* Add headers to the dictionary */
    dict = add_to_dict ( r, dict, marshal_string(headers_name, r),
                         headers_dict );

    dict = end_dict ( r, dict );

    return dict;
}

/*
 * This is the part that deals with Apache module stuff 
 */
#define DEFAULT_RETRIES 3               /* if not configured, the retries */
#define DEFAULT_ADDR  "localhost:9888"
#define DEFAULT_ERROR_DOC      NULL     /* the name of file to display */

/* This is hardcoded */
#define RETRY_DELAY     1               /* seconds to sleep between retries */
#define FACILITY        LOG_LOCAL0      /* syslog facility to use for logging */
#define PRIORITY        LOG_ERR         /* priority for our error conditions */

module skunkweb_module;                    /* Define our module */

/*the SkunkWeb server configuration structure*/
typedef struct skunkweb_server_config
{
    char *aedsockaddr;
    int retries;
    char *error_doc;
    int timeout;
    char expose; /*whether or not to add the SkunkWeb/VV str to Server header*/
    ap_array_header_t *emails;
    ap_array_header_t *excludes;
    ap_array_header_t *failover_hosts;
} skunkweb_server_config;

/* log a message to the syslog at given priority */
static void do_syslog ( int pri, const char *msg )
{
    static int _initted = 0;

    /* XXX this may conflict with apache syslog logging if that's 
     * enabled, we have to look into that */
    if ( !_initted )
    {
        openlog ( "skunkweb_module", 0, FACILITY );
        _initted++;
    }

    syslog ( pri, msg );

    return ;
}

/* send the email about critical condition */
static void send_email ( request_rec *r, const char *msg, ap_array_header_t *to )
{
    char *cmd, *emails;
    int ret;

    /* Get the list of emails, should be non empty if we got here */
    emails = ap_array_pstrcat ( r->pool, to, ' ' );

    /* Create the command to execute */
    cmd = ap_psprintf ( r->pool, "echo 'Subject: SkunkWeb critical error, "
                                 "host %s\n%s' | mail %s", 
                                 r->server->server_hostname, msg, emails );

    if ( (ret = system ( cmd )) )
        do_syslog ( PRIORITY, ap_psprintf ( r->pool, 
                    "SkunkWeb: error running command '%s', returned %d", cmd,ret));
    else
        do_syslog ( PRIORITY, ap_psprintf ( r->pool,
                    "SkunkWeb: sent error email(s) to '%s'", emails ));

    return ;
}

/* log a critical error condition and display a page if available */
static int critical_error ( request_rec *r, const char *desc )
{
#ifdef APACHEV1
    FILE *error_file;
    struct stat st;
#else
    apr_file_t *error_file;
    apr_finfo_t finfo;
#endif

    skunkweb_server_config *conf;
    char *buf;
    char vbuf[2048];

    /* The default error */
    const char *default_error = 
    "<html>\n"
    "<title>Apache / mod_skunkweb critical error</title>\n"
    "<body>\n"
    "<p>A critical error has occured in SkunkWeb module, and no error page "
    "was found. To set the error page, use the Apache configuration "
    "variable <i>SkunkWebErrorDoc</i></p>\n"
    "<p><b>Error: %s\n</b></p>"
    "<p>Please check the Apache error log for more information</p>"
    "</body>\n</html>\n";

    /* Log the error to syslog */
    do_syslog ( PRIORITY, desc );

    /* Log to apache logs */
    SK_AP_RERROR1 ( APLOG_MARK, APLOG_ERR|APLOG_NOERRNO, r, desc );

    /* Get the configuration */
    conf=ap_get_module_config(r->server->module_config, &skunkweb_module);

    /* Send the emails if necessary */
    if ( conf->emails->nelts )
        send_email ( r, desc, conf->emails );

    /* Display the error page if available */
    if ( conf->error_doc )
    {
#ifdef APACHEV1
        if ( (error_file = fopen ( conf->error_doc, "r" )) )	
#else
	if ( apr_file_open (&error_file, conf->error_doc, APR_READ, 0777, 
			    r->pool))
#endif
        {
#ifndef APACHEV1
	    int bytes_sent;
#endif
            /* Set the content type */
            r->content_type = "text/html";

            /* get the length of the content */
#ifdef APACHEV1
            fstat ( fileno ( error_file ), &st );
            ap_set_content_length ( r, st.st_size );
#else
	    apr_stat(&finfo, conf->error_doc, APR_FINFO_CSIZE, r->pool);
	    ap_set_content_length ( r, finfo.size );
#endif		

            /* Make sure the response is not cached in any way */
            ap_table_set ( r->headers_out, "Pragma", "no-cache" );
            ap_table_set ( r->headers_out, "Cache-Control", "no-cache" );

            /* Set the status, apache will expand properly */
            r->status = 500;

            /* send the headers */
#ifdef APACHEV1 /* appears that you don't need to do this in V2 */
            ap_send_http_header ( r );
#endif

            /* send the file */
#ifdef APACHEV1
            ap_send_fd ( error_file, r );
#else
	    ap_send_fd ( error_file, r, 0, finfo.size, &bytes_sent);
#endif

#ifdef APACHEV1
            fclose ( error_file );
#endif
            return OK;
        }
        else
        {
            /* log failure to open the file */
            buf = ap_psprintf ( r->pool, "SkunkWeb: cannot open error file '%s'",
                                conf->error_doc );

	    SK_AP_RERROR1 ( APLOG_MARK, APLOG_ERR, r, buf );
            do_syslog ( LOG_CRIT, buf );
        }
    }

    /* no error page available, display hardcoded one */
    sprintf ( vbuf, default_error, desc );

    /* Set the headers */
    r->content_type = "text/html";

    ap_set_content_length ( r, strlen ( vbuf ) );

    /* Make sure the response is not cached in any way */
    ap_table_set ( r->headers_out, "Pragma", "no-cache" );
    ap_table_set ( r->headers_out, "Cache-Control", "no-cache" );

    /* Set the status */
    r->status = 500;

    /* send the headers */
#ifdef APACHEV1 /*it appears that you don't need to do this in V2 */
    ap_send_http_header ( r );
#endif

    /* send the buffer */
    ap_rputs ( vbuf, r );

    return OK;
}

/* get content sent by the browser */
static binbuffer *get_stdin(request_rec* r)
{
    char argsbuffer[HUGE_STRING_LEN];
    int rsize, len_read, length, rpos = 0;
    char *buf;

    int ret = ap_setup_client_block(r, REQUEST_CHUNKED_ERROR);

    if (ret != OK)
    {
	
        SK_AP_RERROR2 ( APLOG_MARK, APLOG_NOTICE|APLOG_NOERRNO, r,
                        "SkunkWeb: ap_setup_client_block returned %d", ret );

        return NULL;
    }

    length = r->remaining;
    /* 
       this was at level APLOG_NOTICE, but it was getting
       logged even when the LogLevel was warn or error,
       at least in my installations (both Apache1 and Apache2).
       Therefore, I'm changing them to APLOG_DEBUG until
       the problem is understood.  The same applies to the next
       two log calls.  -- js Fri Jun 21 10:41:51 2002
    */
    SK_AP_RERROR2 ( APLOG_MARK, APLOG_DEBUG|APLOG_NOERRNO, r,
		    "SkunkWeb: number remaining %d", length);
    buf = (char *)ap_palloc(r->pool, r->remaining );

    /* Tell the client we're ready to receive */
    if ( !ap_should_client_block ( r ) )
    {
	SK_AP_RERROR1 ( APLOG_MARK, APLOG_DEBUG|APLOG_NOERRNO, r,
			"SkunkWeb: no client data");
        /* Client doesn't want to send anything */
        return buffer_new ( r, "", 0 );
    }
 
    SK_AP_RERROR1 ( APLOG_MARK, APLOG_DEBUG|APLOG_NOERRNO, r,
		    "SkunkWeb: reading client data");
    /* setup the hard timeout */
#ifdef APACHEV1
    ap_hard_timeout ( "until read", r );
#endif

    while ( (len_read = ap_get_client_block ( r, argsbuffer, 
                                             sizeof(argsbuffer))) > 0 )
    {
#ifdef DEBUG
	SK_AP_RERROR2(APLOG_MARK, APLOG_DEBUG|APLOG_NOERRNO, r,
		      "read %d bytes from client", len_read);
#endif /*DEBUG*/

#ifdef APACHEV1
        ap_reset_timeout ( r );
#endif

        /* make sure we don't read over declared length */
        rsize = (rpos + len_read) > length ? length - rpos : len_read;

        memcpy ( buf + rpos, argsbuffer, rsize );

        rpos += rsize;

        /* If read all, exit */
        if ( rpos == length )
            break ;
    }

    if (len_read < 0)
        return NULL;

    if ( rpos < length )
    {
	SK_AP_RERROR3( APLOG_MARK, APLOG_ERR|APLOG_NOERRNO, r,
		       "expected %d bytes from client, got %d", length, rpos );

        return NULL;
    }

#ifdef APACHEV1
    ap_kill_timeout (r);
#endif

    return buffer_new(r, buf, rpos);
}

/* writes all of data to socket, returns length of data sent or -1 on not
   all of it sent*/
static int write_data_to_socket(int sock, const char* data, int len)
{
    int sentlen=0;
    int sent;

    while (sentlen < len)
    {
	sent=send(sock, data+sentlen, len-sentlen, 0);

	if (sent == -1 || sent == 0)
	    return -1;

	sentlen+=sent;
    }

    return len;
}

/*reads length bytes from the socket if it can, otherwise returns -1*/
static int get_this_much(int sock, int length, char *data, request_rec* r)
{
    int gotlen=0;
    int thislen;
    
    while (gotlen < length)
    {
	thislen=recv(sock, data+gotlen, length-gotlen, 0);
	if (thislen == -1 || thislen == 0)
	{
            /* This deserves attention */
	    SK_AP_RERROR2( APLOG_MARK, APLOG_ERR, r,
			   "SkunkWeb: error reading from server, thislen=%d", 
			   thislen);

	    return -1;
	}
	gotlen+=thislen;
    }
    return length;
}

/*uses the protocol to get the response from the cgi server*/
static binbuffer *get_return_data ( int sock, request_rec* r)
{
    char len[11];
    char *data;
    int rc;
    int length;

    len[10]='\0';

#ifdef DEBUG

    SK_AP_RERROR1( APLOG_MARK, APLOG_DEBUG|APLOG_NOERRNO, r,
		   "getting length - 10 bytes");
#endif /*DEBUG*/

    rc = get_this_much(sock, 10, len, r);

#ifdef DEBUG
    SK_AP_RERROR3( APLOG_MARK, APLOG_DEBUG|APLOG_NOERRNO, r,
		   "got length - 10 bytes >%s< rc=%d", len, rc);
#endif /*DEBUG*/

    if (rc == -1)
	return NULL;

    length = atoi(len);
    data = ap_palloc(r->pool, length + 1);
    data[length] = '\0';

#ifdef DEBUG
    SK_AP_RERROR2( APLOG_MARK, APLOG_DEBUG|APLOG_NOERRNO, r,
		   "getting data - %d bytes", length);
#endif /*DEBUG*/

    rc = get_this_much(sock, length, data, r);

    if (rc == -1)
	return NULL;

#ifdef DEBUG
    SK_AP_RERROR2( APLOG_MARK, APLOG_DEBUG|APLOG_NOERRNO, r,
		   "got data - %d bytes", length);
#endif /*DEBUG*/

    return buffer_new(r, data, length);
}

/*finds the offset of the crlf pair in retdata*/
static int find_crlfcrlf(request_rec* r, binbuffer* retdata)
{
    /* XXX the offsets returned by two functions are different by 1, 
     * second function is 1 byte less, however it shouldn't make
     * any difference 
     */
#if HAVE_MEMMEM                 /* system has memmem() */
    int offset, len = 4;
    const char str[] = "\r\n\r\n";
    void *ptr;

    /* Try to get the same thing in a nicer fashion */
    if ( (ptr = memmem ( retdata->buf, retdata->len, str, len )) )
    {
        offset = ptr - (void *)retdata->buf + len;
        
	return offset;
    }
    else
	return retdata->len; /* no body, return hdrlength = length of buffer */
#else                                 /* Use Drew's state machine */
    int state=0;
    int offset=0;
    char c;

    while ((offset < retdata->len) && (state != 4))
    {
	c=retdata->buf[offset];

	switch(state) 
	{
	    case 0:
		if (c=='\r') state=1;
		if (c=='\n') state=5;
		break;
	    case 1:
		if (c=='\n') state=2;
		else state=0;
		break;
	    case 2:
		if (c=='\r') state=3;
		else state=0;
		break;
	    case 3:
		if (c=='\n') state=4;
		else state=0;
		break;
	    case 5:
		if (c=='\n') state=4;
		if (c=='\r') state=1;
		else state=0;
		break;
	}
	offset++;
    }

    offset--;

    if (state==4)
	return offset;
    else
	return retdata->len; /* no body, return hdrlength = length of buffer */
#endif  /* HAVE_MEMMEM */
}
				 
/*
  line buffered string like file thingy so that ap_scan_script_header_err_core
  can scan headers in a string
*/
typedef struct lineBufferedString
{
    int offset;
    char *data;
    int len;
} lineBufferedString;

/*creates a new lineBufferedString thing*/
static lineBufferedString* new_lbf(request_rec* r, binbuffer* d)
{
    lineBufferedString *l = ap_palloc(r->pool, sizeof (lineBufferedString));
    l->offset=0;
    l->data=d->buf;
    l->len=d->len;
    return l;
}

/*similar to fgets, but on a lineBufferedString*/
static int pseudo_FILE(char* buf, int len, void* lbs)
{
    lineBufferedString* l=(lineBufferedString*)lbs;
    int idx=l->offset;
    int start=l->offset;
    int cnt=0;

    for (;idx < start+len && idx < l->len; idx++)
    {
	if (l->data[idx]=='\n')
	{
	    buf[cnt]='\0';
	    break;
	}

	buf[cnt]=l->data[idx];

	if (l->data[idx] != '\r')
	    cnt++;
    }

    buf[cnt]='\0';
    l->offset=idx+1;

    return idx-start;
}

#ifdef DEBUG
/*a test function not actually used in the module*/
static void test_lbf(request_rec* r, binbuffer *b)
{
    lineBufferedString* l=new_lbf(r, b);

    char buf[2000];
    while (pseudo_FILE(buf, 2000, (void*)l))
    {
	SK_AP_RERROR2( APLOG_MARK, APLOG_DEBUG|APLOG_NOERRNO, r,
		       "line is >%s<", buf);
    }
}
#endif /*DEBUG*/

/* This processes the header, setting appropriate fields in the request 
 * record, and returns the body of the message suitable for sending */
static binbuffer *affect_headers(request_rec *r, binbuffer *retdata)
{
    int hdroff;
    int ret;
    char sbuf[MAX_STRING_LEN];
    char *hdr;
    const char *ptr;

#ifdef DEBUG
    SK_AP_RERROR1( APLOG_MARK, APLOG_DEBUG|APLOG_NOERRNO, r,
		   "looking for end of headers");
#endif /*DEBUG*/

    hdroff = find_crlfcrlf(r, retdata);
    if (hdroff == -1)
    {
	SK_AP_RERROR2( APLOG_MARK, APLOG_ERR|APLOG_NOERRNO, r,
		       "end of headers not found! hdroff=%d", hdroff);

	return NULL;
    }

    hdr = ap_pstrndup(r->pool, retdata->buf, hdroff);
    
#ifdef DEBUG
    SK_AP_RERROR2( APLOG_MARK, APLOG_DEBUG|APLOG_NOERRNO, r,
		   "headers were >%s<", hdr);
#endif /*DEBUG*/

    /* 
     * Set up the basic HTTP header, this includes things like 'Date' 
     * and 'Server' 
     */
    ret = ap_scan_script_header_err_core(r, sbuf, pseudo_FILE, 
					 new_lbf (r, 
                                         buffer_new(r, hdr, strlen(hdr))) );

#ifdef DEBUG
    SK_AP_RERROR2( APLOG_MARK, APLOG_DEBUG|APLOG_NOERRNO, r,
		   "ret of scan = %d", ret);
#endif /*DEBUG*/
    
    /* Now, to avoid all the BS, just use the content length we got from the
     * client to calculate the real length we need to send on 
     */
    if ( !(ptr = ap_table_get ( r->headers_out, "Content-Length" )) )
    {
        SK_AP_RERROR1 ( APLOG_MARK, APLOG_ERR|APLOG_NOERRNO, r,
                        "Error: Content-Length not set in request!" );

        return NULL;
    }

    hdroff = (retdata->len) - atoi( ptr );

    return buffer_new(r, (retdata->buf) + hdroff, (retdata->len)-hdroff);
}

/*#define DEBUG_HEADERS   1*/

#ifdef DEBUG_HEADERS
static int show_headers ( void *r, const char *key, const char *val )
{
    SK_AP_RERROR3 ( APLOG_MARK, APLOG_DEBUG|APLOG_NOERRNO, (request_rec *)r,
                    "'%s' = '%s'", key, val);

    return 1;
}
#endif /*DEBUG_HEADERS*/ 

/* given a textual address form, create either a unix socket or a 
   TCP socket and the socket address 

The forms are:
   host:port for TCP
   /path/to/unix/socket
*/
static void make_socket(request_rec *r,
			const char *address,
			int *sock,
			struct sockaddr **saddr, 
			int *saddrlen)
{
    if (address[0] == '/') /* it's a unix socket */
    {
	struct sockaddr_un *unaddr;

	SK_AP_RERROR1 (APLOG_MARK, APLOG_DEBUG|APLOG_NOERRNO, r,
		       "making UNIX socket");

	unaddr = (struct sockaddr_un*)ap_palloc(r->pool,
						sizeof(struct sockaddr_un));
	strncpy(unaddr->sun_path, address, sizeof(unaddr->sun_path) - 2);
	unaddr->sun_path[sizeof(unaddr->sun_path) - 1] = '\0';
	unaddr->sun_family = AF_UNIX;
	*sock = socket(AF_UNIX, SOCK_STREAM, 0);
	*saddr = (struct sockaddr*)unaddr;
	*saddrlen = sizeof(struct sockaddr_un);
	SK_AP_RERROR1 (APLOG_MARK, APLOG_DEBUG|APLOG_NOERRNO, r,
		       "made UNIX socket");

    }
    else /* it's a TCP socket */
    {
	struct sockaddr_in *inaddr;
#ifdef APACHEV1
	struct hostent *hostaddr;
#endif
	int i;
	int coloff = -1;
	char *hostname;
	int port;

	SK_AP_RERROR1 (APLOG_MARK, APLOG_DEBUG|APLOG_NOERRNO, r,
		       "making TCP/IP socket");

	/* find colon in host spec */
	for (i=0; i < strlen(address); i++)
	    if (address[i] == ':')
	    {
		coloff = i;
		break;
	    }	
	if (coloff == -1) /* if no colon, barf! */
	{
	    SK_AP_RERROR2(APLOG_MARK, APLOG_ERR, r, 
			  "No port specified in %s, dumping core",
			  address);
	    abort();
	}
	inaddr = ap_palloc(r->pool, sizeof(struct sockaddr_in));
	port = inaddr->sin_port = htons(strtol(address+coloff+1, NULL, 10));
	/* if port is bogus, yell */
	if (errno == ERANGE)
	{
	    SK_AP_RERROR2(APLOG_MARK, APLOG_ERR|APLOG_NOERRNO, r,
			  "Port spec in %s is bogus, dumping core",
			  address);
	    abort();
	}
	inaddr->sin_family = AF_INET;
	hostname = ap_pstrdup(r->pool, address);
	hostname[coloff] = 0;

	SK_AP_RERROR2 (APLOG_MARK, APLOG_DEBUG|APLOG_NOERRNO, r,
		       "doing hostname lookup on %s", hostname);

#ifdef APACHEV1
	hostaddr = ap_pgethostbyname(r->pool, hostname);
	memcpy( (char*)&inaddr->sin_addr, hostaddr->h_addr, 
		hostaddr->h_length);
#else
	{
	    apr_sockaddr_t *sa;
	    apr_sockaddr_info_get(&sa, hostname, AF_INET, port, 0, r->pool);

	    /*apr_gethostname(&sa, hostname);*/
	    memcpy( (char*)&inaddr->sin_addr, &(sa->sa.sin.sin_addr),
		    sa->salen);
	}
#endif
	SK_AP_RERROR1 (APLOG_MARK, APLOG_DEBUG|APLOG_NOERRNO, r,
		       "lookup done");
	
	*saddrlen = sizeof(struct sockaddr_in);
	*sock = socket(AF_INET, SOCK_STREAM, 0);
	*saddr = (struct sockaddr*)inaddr;
	SK_AP_RERROR1 (APLOG_MARK, APLOG_DEBUG|APLOG_NOERRNO, r,
		       "made TCP/IP socket");

    }
    SK_AP_RERROR3(APLOG_MARK, APLOG_DEBUG|APLOG_NOERRNO, r,
		  "sock is %d  len is %d", *sock, *saddrlen);
}

/* we failed connecting previously, so pick a random host out of
   failover hosts and setup the addr struct as appropriate
*/
static void make_retry_sockaddr(request_rec *r,
				skunkweb_server_config *conf,	
				int *sock,
				struct sockaddr **saddr,
				int *addrlen)
{
    int choice;
    char *fail_host_str;
    char **elts;

    choice = ((unsigned long int)random()) % conf->failover_hosts->nelts;
    elts = (char**)conf->failover_hosts->elts;
    fail_host_str = elts[choice];

    SK_AP_RERROR2 (APLOG_MARK, APLOG_ERR|APLOG_NOERRNO, r,
		   "retrying with address: %s", fail_host_str);
    make_socket(r, fail_host_str, sock, saddr, addrlen);

}

/* as the function says, connect honoring a timeout so we don't have
   to wait the default which is 2 minutes */
static int connect_with_timeout( int sock, const struct sockaddr *addr,
				 int addr_size, skunkweb_server_config* conf,
				 request_rec* r)
{
    int oflags, flags;
    int rc;
    struct timeval timeout;

    timeout.tv_sec = 0;
    timeout.tv_usec = conf->timeout; 
    
    /* get and save current socket flags */
    oflags = flags = fcntl(sock, F_GETFL, 0);
    
    /* put socket into nonblocking mode */
    flags |= O_NDELAY;
    fcntl(sock, F_SETFL, flags);
    
    /* try to connect, this will likely fail */
    rc = connect(sock, addr, addr_size);

    /* if it's an ok error (connection isn't finished happening yet) */
    if (rc == -1 && (errno == EWOULDBLOCK || errno == EINPROGRESS))
    {
	fd_set rfds;

	FD_ZERO(&rfds);
	FD_SET(sock, &rfds);

	/* wait for something to happen or timeout */
	rc = select(sock+1, &rfds, NULL, NULL, &timeout);

	if (rc == 0) /* if we timed out */
	{
	    SK_AP_RERROR1 (APLOG_MARK, APLOG_ERR|APLOG_NOERRNO, r,
			  "timeout connecting.");
	    return -1;
	}

	/* we have to do this, and this too should fail */
	rc = connect(sock, addr, addr_size);

	/* if failure, but not the "OK" errors */
	if (rc == -1 && !(errno == EISCONN || errno == EALREADY))
	    return -1;

	/* reset us into blocking mode */
	fcntl(sock, F_SETFL, oflags);
	return 0;
    }
    /* 
       reset us into blocking mode, connect actually succeeded the first 
       time?
    */
    fcntl(sock, F_SETFL, oflags);
    return rc;
}

static int do_request ( request_rec* r, const binbuffer *stdin_buf, 
			char **resp)
{
    int sock = -1;      /* avoid uninitted warnings */
    struct sockaddr *addr;
    int rc, sent=0;
    binbuffer *output, *lenbuf, *returndata;
    char len[11];
    int retries;
    int addrlen;

    /*get module config*/
    skunkweb_server_config *conf=ap_get_module_config(r->server->module_config, 
						   &skunkweb_module);

    
    /* make the client socket */
    make_socket(r, conf->aedsockaddr, &sock, &addr, &addrlen);

    SK_AP_RERROR3(APLOG_MARK, APLOG_DEBUG|APLOG_NOERRNO, r,
		  "sock is %d  len is %d", sock, addrlen);

    /* Connect to server, attempting to retry a number of times */
    for (retries = conf->retries; retries > 0; retries--)
    {
	/* if not first time around and there are failover hosts,
	   try one of them */
	if (retries != conf->retries)
	{
	    if (conf->failover_hosts->nelts)
		make_retry_sockaddr(r, conf, &sock, &addr, &addrlen);
	    else
		make_socket(r, conf->aedsockaddr, &sock, &addr, &addrlen);
	}
        /*connect*/
#ifdef DEBUG
        SK_AP_RERROR1 ( APLOG_MARK, APLOG_DEBUG|APLOG_NOERRNO, r,
			"connecting");
#endif /*DEBUG*/
	rc = connect_with_timeout(sock, addr, addrlen, conf, r);

        if (rc == -1)
        {
            /* Retry again */
	    SK_AP_RERROR1( APLOG_MARK, APLOG_INFO, r,
			   "SkunkWeb: cannot connect to SkunkWeb daemon, retrying...");

            close ( sock );
            sleep ( RETRY_DELAY );

            continue;
        }

        /* Read the handshake byte */
        if ( get_this_much ( sock, 1, len, r ) == -1 )
        {
            /* Retry also */
            SK_AP_RERROR1 ( APLOG_MARK, APLOG_INFO, r,
		   "SkunkWeb: didn't get handshake from SkunkWeb daemon, retrying...");

            close ( sock );
            sleep ( RETRY_DELAY );

            continue;
        }
        
        /* Connection established! */
        if ( retries < conf->retries )
            SK_AP_RERROR2 ( APLOG_MARK, APLOG_INFO|APLOG_NOERRNO, r,
                      "SkunkWeb: connection to SkunkWeb daemon established "
                      "after %d retries", conf->retries - retries );
        break;
    }

    if ( !retries )
        return critical_error ( r, ap_psprintf ( r->pool, 
               "SkunkWeb: cannot connect to SkunkWeb daemon at %s",
               conf->aedsockaddr) );          

    /* Marshall everything and send to the server */
#ifdef DEBUG
    SK_AP_RERROR1( APLOG_MARK, APLOG_DEBUG|APLOG_NOERRNO, r,
		   "marshalling stuff" );
#endif /*DEBUG*/
    output = marshal_all ( r, stdin_buf );

    sprintf(len, "%10d", output->len);
    lenbuf=buffer_new(r, len, 10);
    output=buffer_cat(r, lenbuf, output);

    /*write it out to the socket*/
#ifdef DEBUG
    SK_AP_RERROR1( APLOG_MARK, APLOG_DEBUG|APLOG_NOERRNO, r,
		   "writing data back to daemon" );
#endif /*DEBUG*/

    rc = write_data_to_socket ( sock, output->buf, output->len);

    if (rc == -1)
	return critical_error ( r, "SkunkWeb: error when writing data to daemon" ); 

    /*read shit from socket*/
#ifdef DEBUG
    SK_AP_RERROR1 ( APLOG_MARK, APLOG_DEBUG|APLOG_NOERRNO, r,
		    "getting return data");
#endif /*DEBUG*/

    returndata = get_return_data(sock, r);

    if (returndata == NULL)
	return critical_error ( r, "SkunkWeb: error reading data from daemon" ); 

    close(sock);

    /*parse/set headers*/
    returndata = affect_headers(r, returndata); 

    if (returndata == NULL)
	return critical_error ( r, "SkunkWeb: error parsing headers!" );

    /*set content length*/
    ap_set_content_length ( r, returndata->len );

    /* This is needed because Linux Netscape client will screw up 
     * sometimes otherwise. Instead of parsing incoming headers 
     * determining client type, just add this stuff 
     */
    /* ap_table_set ( r->headers_out, "X-Pad", "avoid browser bug" ); */

#ifdef DEBUG_HEADERS
    /* Headers out before send responce */
    SK_AP_RERROR1 ( APLOG_MARK, APLOG_DEBUG|APLOG_NOERRNO, r, 
                    "Headers-out before ap_send_http_header:" );
    ap_table_do ( show_headers, (void *)r, r->headers_out, NULL ); 
#endif /*DEBUG_HEADERS*/

#ifdef APACHEV1 /*only req'd for 1.x */
    /*send response*/
    ap_send_http_header(r);
#endif

    /* adding support for HEAD Mon Apr 23 16:59:08 2001 js*/
    if (!r->header_only && returndata->len)
    {
	sent = ap_rwrite(returndata->buf, returndata->len, r);
	ap_rflush ( r );
    }
#ifdef DEBUG
    SK_AP_RERROR3 ( APLOG_MARK, LOG_DEBUG|APLOG_NOERRNO, r,
                    "done talking to SkunkWeb daemon on socket %s; "
                    "got %d bytes and sent them on",
                    conf->aedsockaddr, sent );
#endif /*DEBUG*/

    return OK;
}

/* the request handler */
static int skunkweb_handler(request_rec* r)
{
    char *resp;
    int retcode;
    binbuffer *stdin_buf;
    skunkweb_server_config *conf;

#ifndef APACHEV1
    if (strcmp(r->handler,"skunkweb-handler"))
    {
	/*#ifdef DEBUG
        SK_AP_RERROR3(APLOG_MARK, APLOG_DEBUG|APLOG_NOERRNO, r,
		      "handler for <%s> is %s", r->uri, r->handler);
	#endif*/
	return DECLINED;
    }
#endif
    /* Get the configuration */
    conf=ap_get_module_config(r->server->module_config, &skunkweb_module);

    /* are there any exclusions? */
    if (conf->excludes->nelts) 
    {
	int i;
	char **elts;
	int l;

#ifdef DEBUG
	SK_AP_RERROR2(APLOG_MARK, APLOG_DEBUG|APLOG_NOERRNO, r,
		      "scanning exclude list for match of %s", r->uri);
#endif /* DEBUG */
	elts = (char**)conf->excludes->elts;
	/* 
	   loop through the table and if a table entry matches
	   a prefix, decline
	*/
	for (i=0;i<conf->excludes->nelts;i++)
	{
	    l = strlen(elts[i]);
	    if (!strncmp(elts[i], r->uri, l))
	    {
#ifdef DEBUG
		SK_AP_RERROR3(APLOG_MARK, APLOG_DEBUG|APLOG_NOERRNO, r,
			      "matched exclude <%s>: <%s>", elts[i], r->uri);
#endif /* DEBUG */
		return DECLINED;
	    }
	}
#ifdef DEBUG
	SK_AP_RERROR1(APLOG_MARK, APLOG_DEBUG|APLOG_NOERRNO, r,
		      "no exclusions matched");
#endif /* DEBUG */
    }

#ifdef DEBUG
    SK_AP_RERROR2 ( APLOG_MARK, APLOG_DEBUG|APLOG_NOERRNO, r,
		    "SkunkWeb handler entered, request is '%s'", r->the_request );
#endif /*DEBUG*/

    /*sets up the "cgi environment"*/
    ap_add_common_vars(r);
    ap_add_cgi_vars(r);
	
#ifdef DEBUG
    SK_AP_RERROR1 ( APLOG_MARK, APLOG_DEBUG|APLOG_NOERRNO, r,
		    "cgi env vars done" );
#endif /*DEBUG*/

    /*get sent browser data*/
    if ( !(stdin_buf = get_stdin(r)) )
        return critical_error ( r, "SkunkWeb: error reading stdin from client" );

#ifdef DEBUG
    if ( stdin_buf->len )
        SK_AP_RERROR2 ( APLOG_MARK, APLOG_DEBUG|APLOG_NOERRNO, r,
			"got stdin, len=%d", stdin_buf->len );
#endif /*DEBUG*/

    /*send/process the request to the server*/
    retcode = do_request ( r, stdin_buf, &resp);

#ifdef DEBUG_HEADERS
    SK_AP_RERROR2 ( APLOG_MARK, APLOG_DEBUG|APLOG_NOERRNO, r,
		    "Content-type: %s", r->content_type );

    SK_AP_RERROR2 ( APLOG_MARK, APLOG_DEBUG|APLOG_NOERRNO, r,
		    "Content-length: %ld", r->clength );

    SK_AP_RERROR2 ( APLOG_MARK, APLOG_DEBUG|APLOG_NOERRNO, r,
		    "Content-length from client: %ld", r->read_length );

    ap_table_do ( show_headers, (void *)r, r->headers_in, NULL); 
    SK_AP_RERROR1 ( APLOG_MARK, APLOG_DEBUG|APLOG_NOERRNO, r, 
		    "Headers-in:" );

    SK_AP_RERROR1 ( APLOG_MARK, APLOG_DEBUG|APLOG_NOERRNO, r, 
		    "Headers-out:" );
    ap_table_do ( show_headers, (void *)r, r->headers_out, NULL ); 
#endif /*DEBUG_HEADERS*/

#ifdef DEBUG
    SK_AP_RERROR2 ( APLOG_MARK, APLOG_DEBUG|APLOG_NOERRNO, r,
		    "did request, return code is %d", retcode);
#endif /*DEBUG*/

    return retcode;
}

/*
  apache config stuff
*/

/*sets retries in server config*/
static const char* set_skunkweb_retries ( cmd_parms *parms, void *dummy, const char *arg)
{
    server_rec *s = parms->server;
    skunkweb_server_config *conf;

    conf=(skunkweb_server_config *) ap_get_module_config(s->module_config, 
						      &skunkweb_module);
    conf->retries = atoi(arg);

    return NULL;
}


/*sets host in server config*/

static const char* set_skunkweb_addr(cmd_parms *parms, void *dummy, const char *arg)
{
    server_rec *s=parms->server;
    skunkweb_server_config *conf;

    conf=(skunkweb_server_config *)ap_get_module_config(s->module_config, 
						     &skunkweb_module);
    conf->aedsockaddr=ap_pstrdup(parms->pool, arg);

    return NULL;
}

/*sets error document in server config*/
static const char* set_skunkweb_error_doc(cmd_parms *parms, void *dummy, const char *arg)
{
    server_rec *s=parms->server;
    skunkweb_server_config *conf;

    conf=(skunkweb_server_config *)ap_get_module_config(s->module_config, 
						     &skunkweb_module);
    conf->error_doc = ap_pstrdup(parms->pool, arg);

    return NULL;
}

static const char* set_skunkweb_connect_timeout(cmd_parms *parms, void *dummy,
						const char *arg)
{
    server_rec *s=parms->server;
    skunkweb_server_config *conf;

    conf=(skunkweb_server_config *)ap_get_module_config(s->module_config, 
						     &skunkweb_module);
    conf->timeout = 1000*atoi(arg);
    return NULL;
}

/*sets error email in server config*/
static const char* set_skunkweb_error_email ( cmd_parms *parms, void *dummy,
					      const char *arg)
{
    server_rec *s=parms->server;
    skunkweb_server_config *conf;
    char **new_elmt;

    conf=(skunkweb_server_config *)ap_get_module_config(s->module_config, 
						     &skunkweb_module);

    new_elmt = (char **)ap_push_array ( conf->emails );
    *new_elmt = ap_pstrdup ( parms->pool, arg );

    return NULL;
}

static const char* set_skunkweb_excludes ( cmd_parms *parms, void *dummy,
					   const char *arg )
{
    server_rec *s = parms->server;
    skunkweb_server_config *conf;
    char **new_elmt;

    conf = (skunkweb_server_config *)ap_get_module_config(s->module_config, 
						       &skunkweb_module);
    new_elmt = (char **)ap_push_array ( conf->excludes );
    *new_elmt = ap_pstrdup ( parms->pool, arg );

    return NULL;
}

static const char* set_skunkweb_failover_hosts ( cmd_parms *parms, void *dummy,
						 const char *arg )
{
    server_rec *s = parms->server;
    skunkweb_server_config *conf;
    char **new_elmt;

    conf = (skunkweb_server_config *)ap_get_module_config(s->module_config, 
						       &skunkweb_module);
    new_elmt = (char **)ap_push_array ( conf->failover_hosts );
    *new_elmt = ap_pstrdup ( parms->pool, arg );

    return NULL;
}

static const char* set_skunkweb_expose ( cmd_parms *parms, void *dummy,
					 const char *arg )
{
    server_rec *s = parms->server;
    skunkweb_server_config *conf;

    conf = (skunkweb_server_config *)ap_get_module_config(s->module_config, 
							  &skunkweb_module);
    conf->expose = (int)arg;
    return NULL;
}

/* create the server config */
#ifdef APACHEV1
static void* skunkweb_server_cfg_create(pool *p, server_rec *s)
#else
static void* skunkweb_server_cfg_create(apr_pool_t *p, server_rec *s)
#endif
{
    skunkweb_server_config *a;

    a = (skunkweb_server_config *)ap_palloc(p, sizeof(skunkweb_server_config));

    /*    a->hostname = DEFAULT_HOST; 
	  a->port = DEFAULT_PORT;*/
    a->expose = 1;
    a->aedsockaddr = DEFAULT_ADDR;
    a->retries = DEFAULT_RETRIES;
    a->error_doc = DEFAULT_ERROR_DOC;
    /* make empty arrays containing pointers to char */
    a->emails = ap_make_array ( p, 0, sizeof(char *) );
    a->excludes = ap_make_array ( p, 0, sizeof(char *) );
    a->failover_hosts = ap_make_array ( p, 0, sizeof(char *) );
    a->timeout = 1000000; /* 1 second */
    return (void *) a;
}
#ifdef APACHEV1
static void skunkweb_init_handler(server_rec *s, pool *p)
#else
static int skunkweb_init_handler(apr_pool_t *p, apr_pool_t *plog, 
				 apr_pool_t *ptemp, server_rec *s)
#endif
{
    skunkweb_server_config *conf;
    conf = (skunkweb_server_config *)ap_get_module_config(s->module_config, 
							  &skunkweb_module);
    if (conf->expose)
#ifdef APACHEV1
	ap_add_version_component("SkunkWeb/" SW_VERSION);
#else
        ap_add_version_component(p, "SkunkWeb/" SW_VERSION);
    return OK;
#endif
}
/*the module definition*/
#ifdef APACHEV1
/*the command registry*/
static command_rec skunkweb_cmds[] = 
{
    { "SkunkWebSocketAddress", set_skunkweb_addr, NULL, RSRC_CONF, TAKE1,
      "socket address of where SkunkWeb lives host:port for TCP sockets or "
      "/path_to_sock for UNIX domain sockets"},
    { "SkunkWebRetries", set_skunkweb_retries, NULL, RSRC_CONF, TAKE1,
      "the number of times to try to connect to SkunkWeb daemon before failing" },
    { "SkunkWebErrorDoc", set_skunkweb_error_doc, NULL, RSRC_CONF, TAKE1,
      "the html document to display when critical error occurs" },
    { "SkunkWebErrorEmails", set_skunkweb_error_email, NULL, RSRC_CONF, ITERATE,
      "the list of email addresses to notify on critical errors" },
    { "SkunkWebExclude", set_skunkweb_excludes, NULL, RSRC_CONF, ITERATE,
      "list of uri prefixes for which mod_SkunkWeb should not intervene" },
    { "SkunkWebFailoverHosts", set_skunkweb_failover_hosts, NULL, RSRC_CONF, ITERATE,
      "other host/ports (form of host:port) to try in the event of a "
      "connection failure to primary SkunkWebHost"},
    { "SkunkWebConnectTimeout", set_skunkweb_connect_timeout, NULL, RSRC_CONF, TAKE1,
      "number of milliseconds to wait for a connect to succeed before "
      "retrying"},
    { "SkunkWebExpose", set_skunkweb_expose, NULL, RSRC_CONF, FLAG,
      "whether or not to show the SkunkWeb version string in the Server "
      "header"},
    { NULL }
};

/*the handler registry*/
static handler_rec skunkweb_handlers[] = 
{
    { "skunkweb-handler", skunkweb_handler },
    { NULL }
};


module skunkweb_module = {
   STANDARD_MODULE_STUFF,
   skunkweb_init_handler,       /* initializer */
   NULL,                        /* dir config creater */
   NULL,                        /* dir merger --- default is to override */
   skunkweb_server_cfg_create,     /* server config */
   NULL,                        /* merge server config */
   skunkweb_cmds,          	/* command table */
   skunkweb_handlers,      	/* handlers */
   NULL,                        /* filename translation */
   NULL,                        /* check_user_id */
   NULL,                        /* check auth */
   NULL,                        /* check access */
   NULL,                        /* type_checker */
   NULL,                        /* fixups */
   NULL,                        /* logger */
   NULL                         /* header parser */
};
#else  /*APACHE V2*/
static const command_rec skunkweb_cmds[] = 
{
    AP_INIT_TAKE1("SkunkWebSocketAddress", set_skunkweb_addr, NULL, RSRC_CONF,
		  "socket address of where SkunkWeb lives host:port for TCP "
		  "sockets or /path_to_sock for UNIX domain sockets"),
    AP_INIT_TAKE1("SkunkWebRetries", set_skunkweb_retries, NULL, RSRC_CONF,
		  "the number of times to try to connect to SkunkWeb daemon before"
		  " failing"),
    AP_INIT_TAKE1("SkunkWebErrorDoc", set_skunkweb_error_doc, NULL, RSRC_CONF,
		  "the html document to display when critical error occurs"),
    AP_INIT_TAKE1("SkunkWebConnectTimeout", set_skunkweb_connect_timeout, 
		  NULL, RSRC_CONF, "number of milliseconds to wait for a "
		  "connect to succeed before retrying"),

    AP_INIT_ITERATE("SkunkWebErrorEmails", set_skunkweb_error_email, NULL, 
		    RSRC_CONF, "the list of email addresses to notify on "
		    "critical errors"),
    /*
    AP_INIT_ITERATE("SkunkWebExclude", set_skunkweb_excludes, NULL, RSRC_CONF,
		    "list of uri prefixes for which mod_SkunkWeb should not "
		    "intervene"),
    */
    AP_INIT_ITERATE("SkunkWebFailoverHosts", set_skunkweb_failover_hosts, NULL,
		    RSRC_CONF, "other host/ports (form of host:port) to try "
		    "in the event of a connection failure to primary "
		    "SkunkWebHost"),
    AP_INIT_FLAG("SkunkWebExpose", set_skunkweb_expose, NULL, RSRC_CONF,
		 "whether or not to show the SkunkWeb version string in the "
		 "Server header"),
    { NULL }
};

static void register_hooks(apr_pool_t *p)
{
    ap_hook_handler(skunkweb_handler, NULL, NULL, APR_HOOK_MIDDLE);
    ap_hook_post_config(skunkweb_init_handler, NULL, NULL, APR_HOOK_MIDDLE);
 
}

module skunkweb_module = {
   STANDARD20_MODULE_STUFF,
   NULL,                        /* dir config creater */
   NULL,                        /* dir merger --- default is to override */
   skunkweb_server_cfg_create,     /* server config */
   NULL,                        /* merge server config */
   skunkweb_cmds,          	/* command table */
   register_hooks,              /* hooks */
};
#endif
/*
 * MODULE-DEFINITION-START
Name: skunkweb
 * MODULE-DEFINITION-END
 */

 
