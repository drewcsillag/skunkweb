#  
#  Copyright (C) 2001 Andrew T. Csillag <drew_csillag@geocities.com>
#  
#      This program is free software; you can redistribute it and/or modify
#      it under the terms of the GNU General Public License as published by
#      the Free Software Foundation; either version 2 of the License, or
#      (at your option) any later version.
#  
#      This program is distributed in the hope that it will be useful,
#      but WITHOUT ANY WARRANTY; without even the implied warranty of
#      MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#      GNU General Public License for more details.
#  
#      You should have received a copy of the GNU General Public License
#      along with this program; if not, write to the Free Software
#      Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111, USA.
#   
"""**
<p>This module provides services for sending electronic mail
from AED applications, especially from the <:sendmail:> STML
tag.</p>

<p>There are two different methods to send mail with this module:
<ul>
<li>By connecting to an SMTP server on port 25, which will relay all of
the sent mail to the proper destination; or</li>
<li>By executing the Unix <tt>sendmail</tt> utility (usually
<tt>/usr/lib/sendmail -t</tt>) and sending the mail message
via a pipe.</li>
</ul>
</p>

<p>You may choose which method your AED server uses in
the <tt>templating.conf</tt> configuration file:</p>

<ul>
<li>If you want to send all mail via the Unix <tt>sendmail</tt>
utility, set the variable <tt>MailMethod</tt> to <tt>'sendmail'</tt>
(or leave it alone, because it is <tt>'sendmail'</tt> by default).
Then the variable <tt>SendmailCommand</tt> will contain the
command line to execute the program. By default, it is 
<tt>'/usr/lib/sendmail -t'</tt>.</li>

<li>If you want to send all mail via a relaying SMTP server,
set the <tt>MailMethod</tt> variable to <tt>'relay'</tt>.
Then you may indicate the hostname of the SMTP server
in the <tt>MailHost</tt> variable. <tt>MailHost</tt> defaults
to <tt>'localhost'</tt>.</li>
</ul>

"""
# $Id: MailServices.py,v 1.3 2001/07/09 20:38:40 drew Exp $

import smtplib
import socket
import os, sys
import popen2

from SkunkExcept import *
from SkunkWeb.LogObj import *
from SkunkWeb import Configuration

# The mail error we're raising
class MailError ( SkunkRuntimeError ):
    """
    Error we raise when sendmail fails
    """
    pass

# Init some variables
Configuration._mergeDefaultsKw(
    MailMethod = 'sendmail',
    MailHost = 'localhost',
    SendmailCommand = 'sendmail -t',
    FromAddress = "root@localhost"
    )

# shows the mail method: 'sendmail' (default) or 'relay'
_method = Configuration.MailMethod
if _method not in ('sendmail', 'relay'): _method = 'sendmail'

# mailhost for relaying SMTP server (default localhost)
_mailhost = Configuration.MailHost

# sendmail command for utility (default '/usr/lib/sendmail -t')
_sendmail_cmd = Configuration.SendmailCommand


# The general-purpose sendmail function, which is called
# by the STML <:sendmail:> tag, or directly by Python code.

def sendmail ( to_addrs, subj, msg, 
               from_addr = Configuration.FromAddress ):
    """**
    <p>The general-purpose sendmail function, which is called
    by the STML &lt;:sendmail:&gt; tag, or directly by Python code.</p>
    <p><tt>to_addrs</tt> should be a list or tuple of email address
    strings. <tt>subj</tt> must be a string, although it may be empty.
    <tt>msg</tt> is a string containing the body of the message; it can
    be empty. <tt>from_addr</tt> is a single mail address string; it 
    defaults to the value of the <tt>FromAddress</tt> variable in 
    <tt>templating.conf</tt>.</p>
    <p>This function returns nothing on success, and raises a <code>MailError</code>
    on any mail failure.</p>
    """

    # if they supplied only a string as to_Addrs (i.e. one address),
    # make it a list
    if type(to_addrs) == type(''):
        to_addrs = [to_addrs]
    # dispatch to correct function based on method
    if _method == 'relay':
	sendmail_smtp(to_addrs, subj, msg, from_addr)
    else:
	sendmail_pipe(to_addrs, subj, msg, from_addr)

def sendmail_smtp ( to_addrs, subj, msg, 
                    from_addr = Configuration.FromAddress ):
    """**
    <p>Called by <code>sendmail</code> function, this function
    uses SMTP to send a mail message. Function raises a 
    <code>MailError</code> if it cannot connect to the SMTP
    server; any other errors are merely sent as warnings
    to the AED error log.</p>
    """
    try:
        conn = smtplib.SMTP ( _mailhost )
    except (socket.error, smtplib.SMTPException), val:
        WARN ( 'Cannot open smtp connection to %s: %s' % 
                  (_mailhost, str(val)) )
        raise MailError, 'cannot connect to %s: %s' % (_mailhost, str(val) )

    # add subject to the message
    msg = 'Subject: %s\n' % subj + msg

    try:
        try:
            errs = conn.sendmail ( from_addr, to_addrs, msg )
        except smtplib.SMTPException, val:
            # Log, in case the template catches the exception
            WARN ( 'URL %s: sendmail: %s' % 
                      ( AED._session._request.uri, str(val) ) )

            # Raise the error
            raise MailError, 'error while sending mail: %s' % str(val)
    finally:
        # Always close the connection
        conn.quit()

    if errs:
        # Not everyone received messages, just print an error
        WARN ( 'URL %s: sendmail: not all recepients received mail:' )
        for k, v in errs.items:
            WARN ( '---> %s: %s' % ( k, v ) )

    # All done!

def sendmail_pipe ( to_addrs, subj, msg, 
                    from_addr = Configuration.FromAddress ):
    """**
    <p>This function, called by the <code>sendmail</code> function,
    sends an email message by opening a pipe to the Unix <tt>sendmail</tt>
    utility. Function raises a <code>MailError</code> if it cannot
    create the pipe; any other errors returned by sendmail are
    recorded as warnings in the AED error log.</p>
    """

    try:
	pi = popen2.Popen3(_sendmail_cmd, capturestderr=1)
    except:
       raise MailError, "could not open pipe to sendmail utility %s: %s, %s" \
			% (repr(_sendmail_cmd), sys.exc_type, sys.exc_value)
    
    try:
	# write out the message.
	out = pi.tochild
        # write the From: header.
        out.write('From: %s\n' % from_addr)
	# write the To: header
	out.write('To: %s\n' % string.join(to_addrs, ', '))
	# write the subject header
	out.write('Subject: %s\n' % subj)
	# write the header end
	out.write('\n')
	# write the message body
	out.write(msg)
	# now close input and wait for child
	out.close()
	# holds return code
	status = pi.wait()
	errs = pi.childerr.readlines()

    except:
	raise MailError, "could not write message to sendmail utility %s" \
			 % repr(_sendmail_cmd)

    # if status is nonzero, there's some stuff in stderr.
    if status or errs:
	WARN("Error messages from sendmail %s: exit status %s" 
		% (_sendmail_cmd, status))
        for line in errs:
	    WARN("---> %s" % line)

