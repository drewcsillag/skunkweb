#  
#  Copyright (C) 2001, 2003 Andrew T. Csillag <drew_csillag@geocities.com>
#  
#      You may distribute under the terms of either the GNU General
#      Public License or the SkunkWeb License, as specified in the
#      README file.
#

"""**
<p>This module provides services for sending electronic mail
from SkunkWeb applications, especially from the <:sendmail:> STML
tag.</p>

<p>There are two different methods to send mail with this module:
<ul>
<li>By connecting to an SMTP server on port 25, which will relay all of
the sent mail to the proper destination; or</li>
<li>By executing the Unix <tt>sendmail</tt> utility (usually
<tt>/usr/lib/sendmail -t</tt>) and sending the mail message
via a pipe.</li>
<li>By executing the <tt>qmail-inject</tt> command (part
of the qmail MTA) and sending the mail message
via a pipe.</li>
</ul>
</p>

<p>You may choose which method your SkunkWeb server uses in
the <tt>templating.conf</tt> configuration file:</p>

<ul>
<li>If you want to send all mail via the Unix <tt>sendmail</tt>
utility, set the variable <tt>MailMethod</tt> to <tt>'sendmail'</tt>
(or leave it alone, because it is <tt>'sendmail'</tt> by default).
Then the variable <tt>SendmailCommand</tt> will contain the
command line to execute the program. By default, it is 
<tt>'/usr/lib/sendmail -t'</tt>.</li>

<li>If you want to send all mail via <tt>qmail</tt>, set the
variable <tt>MailMethod</tt> to <tt>'qmail'</tt>.
</li>

<li>If you want to send all mail via a relaying SMTP server,
set the <tt>MailMethod</tt> variable to <tt>'relay'</tt>.
Then you may indicate the hostname of the SMTP server
in the <tt>MailHost</tt> variable. <tt>MailHost</tt> defaults
to <tt>'localhost'</tt>.</li>
</ul>

"""

import rfc822, mimetools, mimify
import string
import smtplib
import socket
import os, sys
import popen2
import random
import time
from cStringIO import StringIO

from skunk.date.timeutil import arpa
from SkunkExcept import *
from SkunkWeb.LogObj import *
from SkunkWeb import Configuration


# The mail errors we're raising
class MailError ( SkunkRuntimeError ):
    """
    Error we raise when sendmail fails
    """
    pass

class AddressValidationError( MailError ):
    """
    Error if addresses are most likely not deliverable
    """
    def __init__(self, message, bad, good=None):
        MailError.__init__(self, message)
        self.bad = bad
        self.good = good or []
	self.message = message


# Init some variables
Configuration.mergeDefaults(
    MailMethod = 'sendmail',
    MailHost = 'localhost',
    SendmailCommand = '/usr/lib/sendmail',
    FromAddress = "root@localhost",
    QmailInject = "/var/qmail/bin/qmail-inject",
    AddressCheckLevel = 1
    )
# AddressCheckLevel
# 0 - no checks are done
# 1 - simple format check
# 2 - full syntax check (not implemented yet)

valid_charsets = ['iso-8859-1', 'us-ascii']

# shows the mail method: 'sendmail' (default) or 'relay' or 'qmail'
_method = Configuration.MailMethod

# mailhost for relaying SMTP server (default localhost)
_mailhost = Configuration.MailHost

# sendmail command for utility (default '/usr/lib/sendmail')
_sendmail_cmd = Configuration.SendmailCommand

# qmail-inject command (default '/var/qmail/bin/qmail-inject')
_qmailinject = Configuration.QmailInject

# address-check level (default 1)
_addresscheck_level = Configuration.AddressCheckLevel


# The general-purpose sendmail function, which is called
# by the STML <:sendmail:> tag, or directly by Python code.

def sendmail ( to_addrs, subj, msg, 
               from_addr = Configuration.FromAddress,
               **extended ):
    """**
    <p>The general-purpose sendmail function, which is called
    by the STML &lt;:sendmail:&gt; tag, or directly by Python code.</p>
    <p><tt>to_addrs</tt> should be a list or tuple of email address
    strings. <tt>subj</tt> must be a string, although it may be empty.
    <tt>msg</tt> is a string containing the body of the message; it can
    be empty. <tt>from_addr</tt> is a single mail address string; it 
    defaults to the value of the <tt>FromAddress</tt> variable in 
    <tt>templating.conf</tt>.</p>
    <p>This function returns nothing on success, and raises a
    <code>MailError</code> on any mail failure.</p>
    <p>
    The From: and To: headers are always built from supplied parameters.
    Cc: and Bcc: headers in the supplied mail text are not touched
    and not used.
    </p>
    <p>
    The sendmail function adds a correct Date: header, ensures that
    the From: header is set and generates a Message-Id: header if
    necessary. If the raw parameter is true, these headers are
    not touched.
    </p>

    <p>
    The extended parameter accepts the following parameters:
    </p>
    <dl>
     <dt>to_name='name'</dt>
     <dd>A name that may be used in the To: header
         directly. It's merged with to_addrs if the there is only one value for
         to_addrs. If there are multiple to_addrs, it is used
         literally and may then contain an address too.</dd>
     <dt>from_name</dt>
     <dd>A name that is merged with from_addr in the From: header.</dd>
     <dt>envelope_sender</dt>
     <dd>The sender address that is used in the SMTP dialogue. This
         address gets possible bounces.</dd>
     <dt>charset='charset-name'</dt>
     <dd>The character set that is used for encoding of headers
         and the message body. At the moment only <tt>iso-8859-1</tt>
         and <tt>us-ascii</tt> are supported because of limitations
         in the rfc822 module. The default is us-ascii</dd>
     <dt>encoding='encoding-type'</dt>
     <dd>The encoding type that is used for encoding of headers
         and the message body.<br />
         Possible values are <tt>base64</tt>, <tt>7bit</tt>,
         <tt>8bit</tt> and <tt>quoted-printable</tt><br />
         When 7bit is used, the MIME headers (Mime-Version,
         Content-Encoding and Content-Type are not set (and deleted
         if present in the msg).<br />
         The default value is 7bit.</dd>
     <dt>raw=True</dt>
     <dd>If this parameter is set to true the contents of the message
         is not altered in any way. The message is given in the parameter
         <tt>msg</tt>. In this case the envelope_sender
         has to be set, the receivers are taken from to_addrs as
         usual</dd>
    </dl>
    """

    # force SkunkWeb administrator to change the default envelope sender
    if from_addr == 'root@localhost':
        WARN("MailServices: FromAddress not changed, use a deliverable address!")
        raise MailError, "FromAddress not changed, use a deliverable address!"
    

    # if they supplied only a string as to_addrs (i.e. one address),
    # make it a list
    if type(to_addrs) == type(''):
        to_addrs = [to_addrs]
    rnum = len(to_addrs)       # number of receivers

    # do defined address checks, raise exception in case of problems
    address_check(_addresscheck_level, to_addrs)

    # check if the message is to be sent 'as is'
    if extended.has_key('raw') and extended['raw']:
        if not extended.has_key('envelope_sender'):
           WARN("MailServices: envelope_sender not set, but 'raw' send requested")
           raise MailError, "envelope_sender not set, but 'raw' send requested"
        dispatch_to_send_method(to_addrs, msg, extended['envelope_sender'])
        return

    # charset setting
    if extended.has_key('charset'):
        charset = string.lower(extended['charset'])
        if charset not in valid_charsets:
           WARN("MailServices: invalid character set parameter given: %s" \
	         % (extended['charset']))
           raise MailError, "invalid character set parameter given"
    else:
        charset = 'us-ascii'

    # check envelope sender
    if extended.has_key('envelope_sender'):
        envelope_sender = extended['envelope_sender']
    else:
        envelope_sender = from_addr

    mailfile = StringIO(msg)
    mail = mimetools.Message(mailfile)

    # insert subject
    if not subj or subj == '':
        subj = 'no subject'
    # work around limitation in mimify
    mail['Subject'] = mimify.mime_encode_header(subj + ' <')[:-2]

    # insert from header
    if extended.has_key('from_name'):
        fromheader = extended['from_name'] + ' <' + from_addr + '>'
        fromheader = mimify.mime_encode_header(fromheader)
    else:
        fromheader = from_addr
    mail['From'] = fromheader

    # insert to header
    if extended.has_key('to_name'):
        toheader = extended['to_name']
        if rnum == 1:
            if len(filter(lambda x: x in ['<','>'], list(toheader))) != 0:
                WARN("MailServices: angle bracket in to_name when using single recipient")
                raise MailError, "angle bracket in to_name when using single recipient"
            toheader = toheader + ' <' + to_addrs[0] + '>'
        mail['To'] = mimify.mime_encode_header(toheader)
    else:    
        if rnum == 1:
            mail['To'] = to_addrs[0]
        else:
            mail['To'] = "recipient list not shown: ;"

    # required Date: header
    lt=time.time()
    mail['Date']=arpa(lt)

    # not necessary but useful - Message-Id
    utcdate = time.strftime('%Y%m%d%H%M%S', time.gmtime(lt))
    pid = os.getpid()
    idhost = socket.getfqdn()
    randint = random.randrange(100000)
    mail['Message-Id'] = \
             '<%s.%s.%s.skunkweb@%s>' % (utcdate, pid, randint, idhost)

    # character set
    if extended.has_key('charset'):
        charset = string.lower(extended['charset'])
        if charset not in ['us-ascii', 'iso-8859-1']:
            WARN("MailServices: charset %s is not supported" % (charset))
            raise MailError, "charset %s is not supported" % (charset)
    else:
        charset = 'us-ascii'

    # encoding
    if extended.has_key('encoding'):
        encoding = string.lower(extended['encoding'])
        if encoding not in ['7bit', '8bit', 'base64', 'quoted-printable']:
            WARN("MailServices: encoding %s is not supported" % (encoding))
            raise MailError, "encoding %s is not supported" % (encoding)
    else:
        encoding = '7bit'

    # check the presence of 8bit data
    if len(filter(lambda x: ord(x) > 127, list(msg))) > 0:
        eightbitdata = True
    else:
        eightbitdata = False

    if encoding == '7bit':
        # check for correctness
        if charset != 'us-ascii':
            WARN("MailServices: 7bit encoding but charset is not us-ascii")
            raise MailError, "7bit encoding but charset is not us-ascii"
        if eightbitdata:
            WARN("MailServices: 7bit encoding but 8bit data present")
            raise MailError, "7bit encoding but 8bit data present"
        # delete present MIME headers if 7bit encoding is used
        if mail.has_key('Content-Transfer-Encoding'):
            del mail['Content-Transfer-Encoding']
        if mail.has_key('Mime-Version'):
            del mail['Mime-Version']
        if mail.has_key('Content-Type'):
            del mail['Content-Type']
    else:                                     # not 7bit
        mail['Content-Transfer-Encoding'] = encoding
        mail['Mime-Version'] = '1.0'
        mail['Content-Type'] = 'text/plain; charset=%s' % (charset)
        headers = mail.__str__() + '\n'
        mail.rewindbody()
        body = mailfile.read()
        mailfile.close()
        mailfile=StringIO(body)
        newmfile = StringIO()
        # only encode body - mimetools doesn't check this
        mimetools.encode(mailfile, newmfile, encoding)
        mailfile = StringIO(headers + newmfile.getvalue())
        newmfile.close()
        mail = mimetools.Message(mailfile)

    mail.rewindbody()
    messagetext = mail.__str__() + '\n' + mailfile.read()
    mailfile.close()
    # now send
    dispatch_to_send_method(to_addrs, messagetext, envelope_sender)


def address_check (level, addresses):
    bad = []
    good = []
    errors = ''
    if level == 0:
        return
    if level == 1:
        # minimal, stupid sanity check for addresses
        for addr in addresses:
           if len(filter(lambda x: ord(x) > 127, list(addr))) > 0:
               errors += "8bit character in address %s\n" % (addr)
               bad.append(addr)
           elif string.find(addr, '@') == -1:
               errors += "address '%s' is no FQDN\n" % (addr)
               bad.append(addr)
           else:
               good.append(addr)
        if len(bad) > 0:
	   raise AddressValidationError, (errors, bad, good)
        return
    raise NotImplementedError, "MailServices/address_check: level %i" % (level)

def dispatch_to_send_method(to_addrs, messagetext,envelope_sender):
    # dispatch to correct function based on method
    if _method == 'relay':
	sendmail_smtp(to_addrs, messagetext, envelope_sender)
    elif _method == 'qmail':
	qmail_pipe(to_addrs, messagetext, envelope_sender)
    elif _method == 'sendmail':
	sendmail_pipe(to_addrs, messagetext, envelope_sender)
    else:
        WARN ("MailServices: no such method: %s" % (_method))
        raise NotImplementedError, "MailServices: no such method: %s" % (_method)


def sendmail_smtp ( to_addrs, msg, envelope_sender):
    """**
    <p>Called by <code>sendmail</code> function, this function
    uses SMTP to send a mail message. Function raises a 
    <code>MailError</code> if it cannot connect to the SMTP
    server; any other errors are merely sent as warnings
    to the SkunkWeb error log.</p>
    """
    try:
        conn = smtplib.SMTP ( _mailhost )
    except (socket.error, smtplib.SMTPException), val:
        WARN ( 'Cannot open smtp connection to %s: %s' % 
                  (_mailhost, str(val)) )
        raise MailError, 'cannot connect to %s: %s' % (_mailhost, str(val) )

    try:
        try:
            errs = conn.sendmail ( envelope_sender, to_addrs, msg )
        except smtplib.SMTPException, val:
            # Log, in case the template catches the exception
            WARN ( 'sendmail: %s' % str(val)  )

            # Raise the error
            raise MailError, 'error while sending mail: %s' % str(val)
    finally:
        # Always close the connection
        conn.quit()

    if errs:
        # Not everyone received messages, just print an error
        WARN ( 'URL %s: sendmail(smtp): not all recepients received mail:' )
        for k, v in errs.items:
            WARN ( '---> %s: %s' % ( k, v ) )

    # All done!

def sendmail_pipe ( to_addrs, msg, envelope_sender):
    """**
    <p>This function, called by the <code>sendmail</code> function,
    sends an email message by opening a pipe to the Unix <tt>sendmail</tt>
    utility. Function raises a <code>MailError</code> if it cannot
    create the pipe; any other errors returned by sendmail are
    recorded as warnings in the SkunkWeb error log.</p>
    """

    sendmailcmd = _sendmail_cmd + ' -f %s' % (envelope_sender)
    for receiver in to_addrs:
        sendmailcmd = sendmailcmd + ' ' + receiver

    try:
	pi = popen2.Popen3(sendmailcmd, capturestderr=1)
    except:
       raise MailError, "could not open pipe to sendmail utility %s: %s, %s" \
			% (repr(_sendmail_cmd), sys.exc_type, sys.exc_value)
    
    try:
        out = pi.tochild
	# write out the message.
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


def qmail_pipe ( to_addrs, msg, envelope_sender):
    """**
    <p>This function, called by the <code>sendmail</code> function,
    sends an email message by opening a pipe to the Qmail <tt>qmail-inject</tt>
    program. Function raises a <code>MailError</code> if it cannot
    create the pipe; any other errors returned by qmail-inject are
    recorded as warnings in the SkunkWeb error log.</p>
    """

    qmailcmd = _qmailinject + ' -f %s' % (envelope_sender)
    for receiver in to_addrs:
        qmailcmd = qmailcmd + ' ' + receiver

    try:
	pi = popen2.Popen3(qmailcmd, capturestderr=1)
    except:
       raise MailError, "could not open pipe to qmail-inject %s: %s, %s" \
			% (repr(_qmailinject), sys.exc_type, sys.exc_value)
    
    try:
        out = pi.tochild
	# write out the message.
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
	WARN("Error messages from qmail-inject %s: exit status %s" 
		% (_qmailinject, status))
        for line in errs:
	    WARN("---> %s" % line)

