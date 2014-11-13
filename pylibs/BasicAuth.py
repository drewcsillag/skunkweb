#  
#  Copyright (C) 2001 Andrew T. Csillag <drew_csillag@geocities.com>
#  
#      You may distribute under the terms of either the GNU General
#      Public License or the SkunkWeb License, as specified in the
#      README file.
#   
"""
This module implements the back-end details of "basic" 
authentication as used by many HTTP servers 
(and, actually, Unix logins).

Basic authentication consists of accepting a submitted 
username and password and comparing it to a username/password
pair stored by some device. On the surface, pretty basic,
right?

This module provides classes which can be the building blocks
for your own authentication objects, which could use
a variety of sources to store the username/password pairs.
See the DictAuthenticator and Cryptor classes for details.

This module also implements a fully functional, usable class
called CryptedFileAuthenticator, which will perform
authentication against Apache "htpasswd" files and even
Unix passwd files...

The biggest caveat: To use the CryptedFileAuthenticator, you 
must have your Python interpreter built with
the crypt module. It's not installed by default,
so you will have to hack around in the Python source
and re-install, or verify that your binary installation
does include the crypt module. If you don't want to use
crypt, you can use the other contents of this module
without a hitch.
"""

import os, types, string

# hacky wrap of crypt module import,
# so that someone is told what to do about 
# the absence of crypt...
try:
    import crypt
except ImportError:
    crypt = None

from types import StringType

class Authenticator:
    """
    Defines the interface for a basic authenticator.
    All "public" methods must be implemented by subclasses.

    All "private" methods (those starting with _) are
    optional to implement; their default behavior is as simple
    as possible, often "pass".
    """
    # required public methods
    def add_user(self, username, password, flush=1): 
	raise NotImplementedError, "Authenticator.add_user method"
    def remove_user(self, username, flush=1): 
	raise NotImplementedError, "Authenticator.remove_user method"
    def is_user(self, username): 
	raise NotImplementedError, "Authenticator.is_user method"
    def is_valid(self, username, password): 
	raise NotImplementedError, "Authenticator.is_valid method"

    # optional private methods
    def _encrypt_password(self, password):
	"""
	If overridden, should return the "encrypted"
	version of password. By default, this method
	returns the password intact ("unecrypted").
	"""
	return password

    def _match_password(self, password, candidate):
	"""
	Returns 1 or 0, whether the real password
	password and the submitted password 
	candidate (which is assumed to be 
	unencrypted) are equal.  By default, this method 
	just returns (password == candidate).
	"""
	return password == candidate

class DictAuthenticator(Authenticator):
    users = {}

    def __init__(self, users={}):
	if type(users) != types.DictType:
	    raise TypeError, "users must be a dictionary: %s" % users
        self.users()
	self.reset()

    def add_user(self, username, password, flush=1):
	"""
	Adds (or updates) a user entry in its user database.
	username and password must be non-empty strings, or a 
	TypeError is raised. flush, if true, causes the 
	flush() method to be called after adding the user entry.
	"""
	if type(username) != StringType or not username:
	    raise TypeError, "user %s must be a string" % repr(user)
	if type(password) != StringType or not password:
	    raise TypeError, "password %s must be a non-empty string" % repr(password)
	password = self._encrypt_password(password)
        self.users[username] = password
	if flush: self.flush()

    def remove_user(self, username, flush=1):
	"""
	Removes the user identified by username from the database.
	If flush is true, the database is written out to the auth file
	afer removing the user. If the user does not exist in the database,
	this method silently returns.
	"""
	# sliently return if user not present
	if not self.users.has_key(username): return
	del self.users[username]
	if flush: self.flush()

    def is_user(self, username):
	"""
	Tells whether the user identified by username
	exists in the user database. Returns 1 or 0.
	"""
	return self.users.has_key(username)

    def is_valid(self, username, password):
	"""
	Tells whether the username and password
	identify a valid entry in the user database.
	Returns 1 or 0. password cannot be empty and must be in plaintext:
	don't try to crypt.crypt() it yourself!
	"""
	if not type(password) == StringType or not password: return 0
	p = self.users.get(username)
	if not p: return 0
	return self._match_password(p, password)

    # public persistence methods
    def reset(self): 
	"""
	This method, if overridden, should "reset" the users
	dictionary attribute so that it has no "dirty" or "stale"
	information in memory. Overrider reset only if the users
	attribute is a memory cache for username/password pairs.
	If you are not caching in memory, but merely accessing
	your persistence directly, you may leave this method
	as is. By default, reset does nothing.
	"""
	pass

    def flush(self): 
	"""
	This method, if overridden, should flush all "dirty"
	or "unwritten" username/password pairs to persistence,
	such as a file or database. If you are accessing your
	persistence directly, and not caching "dirty" or "new"
	entries in self.users, leave this method as is. By default,
	flush does nothing.
	"""
	pass

class FileAuthenticator(DictAuthenticator):
    auth_file = None

    def __init__(self, auth_file):
	"""
	auth_file is the path to the auth file.
	"""
        self.auth_file = auth_file
	self.reset()

    def flush(self):
	"""
	Writes out the user database to the auth file.
	"""

	fd = self._open_for_write()
	for u, p in self.users.items():
	    fd.write("%s:%s\n" % (u,p))
	fd.close()

    def reset(self):
	"""
	Causes the user database to be reloaded from disk.
	Called by __init__, and you shouldn't need to call
	it unless you're doing strange things.
	"""
	# clear out users
	self.users = {}
	fd = self._open_for_read()
	lines = fd.readlines()
	fd.close()
	for line in lines:
	    self._parse_line(line)

    # special private methods for this class
    def _open_for_read(self):
	try:
	    return open(self.auth_file, 'r')
        except:
	    raise IOError, "cannot open auth file %s for read" % self.auth_file

    def _open_for_write(self):
	try:
	    return open(self.auth_file, 'w')
        except:
	    raise IOError, "cannot open auth file %s for write" % self.auth_file

    def _parse_line(self, line):
	if not line: return
	# strip the newline
	line = string.replace(line, '\n', '')
	# split on colon
	spls = string.split(line, ':')
	# if != 2 items, skip
	if len(spls) < 2: return
	# first is username, second is crypted password
	# password must be at least 3 chars crypted!
	if len(spls[1]) <= 2: return
	# assign to user hash
	self.users[spls[0]] = spls[1]

# stand-in for exception raised if crypt module not available
EncryptionError = 'EncryptionError'

class Cryptor:
    """
    A mix-in class which implements encryption
    using the Unix crypt(3) call. Only works if
    the crypt module has been built into your Python
    install. If the crypt module is not available,
    an "EncryptionError" will be raised whenever
    a crypt operation would be attempted.

    This class works by overriding two methods
    which are present in any class which implements
    the Authenticator interface.

    When mixing in this class, be sure to have it
    precede other base classes in this module, such
    as FileAuthenticator! Otherwise your crypted
    methods will not work properly.
    """

    def _encrypt_password(self, password):
	if crypt is None:
	    raise EncryptionError, \
	    "encrypted authentication not possible without crypt module"
	if len(password) < 2: salt = 'XX'
	else: salt = password[0:2]
        return crypt.crypt(password, salt)

    def _match_password(self, password, candidate):
	if crypt is None:
	    raise EncryptionError, \
	    "encrypted authentication not possible without crypt module"
	salt = password[0:2]
	return crypt.crypt(candidate, salt) == password

# note that Cryptor must come before Fileauthenticator in bases
class CryptedFileAuthenticator(Cryptor, FileAuthenticator):
    """
    Combines FileAuthenticator and Cryptor to provide
    authentication against an Apache htpasswd file, or
    a Unix passwd file, or any file whose lines start of
    the form:

    <username>:<crypted_password>[:<other_garbage>][\n]
    """

# a caching "registry" for crypted passwd files,

_crypted_auth_registry = {}

# and a caching factory function for crypted authenticators

def get_crypted_authenticator(filename, auth_type='htpasswd'):
    """
    A nice factory function. Hand it a file path,
    and it will return a CryptedFileAuthenticator instance.
    It also stores the CryptedFileAuthenticator in a registry
    under its filename, so that subsequent calls to
    this function with the same filename return immediately.

    If filename is not a non-empty string, a TypeError is raised.
    """
    if type(filename) != StringType or not filename: 
	raise TypeError, "filename %s must be a non-empty string" % repr(filename)
    if _crypted_auth_registry.has_key(filename): return _crypted_auth_registry[filename]
    if not os.path.isfile(filename):
	raise IOError, "Basic auth file %s does not exist!" % filename
    a = CryptedFileAuthenticator(filename)
    _crypted_auth_registry[filename] = a
    return a

if __name__ == '__main__':
    file = '/usr/local/skunk/etc/apache.auth'
    a = get_crypted_authenticator(file)
    u, p = '__total__test__fooboy', 'mrman'
    for un, pw in a.users.items():
	if not a.is_user(un): raise RuntimeError
	if un == u:
	    raise RuntimeError, \
	    "Oh my god, the test user %s is in the db!" % u
        print (un, pw)
    a.add_user(u, p)
    print "user added"
    print a.is_user(u) and "added user tested"
    print a.is_valid(u, p) and "added user re-tested"
    print not a.is_valid(u, p + 'blah') and "added user re-re-tested"
    a.remove_user(u, p)
    print "user removed"
    print a.is_user(u) or "user removal tested"
    print a.is_valid(u, p) or "user removal re-tested"

