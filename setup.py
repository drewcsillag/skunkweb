#!/usr/local/bin/python
# 
# A setup script for Skunk platform
#
# The scripts performs interactive configuration of the system, and prepares
# it for installation
#

import os, sys, string, cStringIO
import pwd, grp

# Local imports - make sure we're using most up to date pylibs!
sys.path.insert ( 0, './pylibs' )
from prompt import *
import LineWrap

# Some defaults
_def_user = pwd.getpwuid(os.getuid())[0]
_def_prefix = '/usr/local/skunk'

qdict = {
    'AED' : BoolQuestion ( 'Do you wish to install AED', 1 ),
    'Prefix' : StringQuestion ( 'Enter default prefix for the installation', 
                                _def_prefix ),
    'User' : StringQuestion ( 'Enter the username to install as', _def_user ),
    'Group' : StringQuestion ( 'Enter the group to install as', '' ),
    'DCOracle' : BoolQuestion ( 'Do you wish to install DCOracle library - \n'
       'NOTE: full Oracle 8 server installation required to build',
       0 ),
    'MySQLDir' : StringQuestion ( 'Enter the MySQL root directory. If you leave the field blank, MySQL will NOT get installed', '' ),
    'PostgreSQLDir' : StringQuestion ( 'Enter the PostgreSQL root directory. If you leave the field blank, PostgreSQL will NOT get installed', '' ),
    }

# The list of personalities we ship by default. The tuples are 
# ( default state, dependent personalities )
persdict = {
        'mysql' : ( 0, None ),
        'postgresql' : ( 0, None ),
        'skunkorg' : ( 0, None ),
        'sql' : ( 0, None ),
        'superteam' : ( 0, ('sql', ) ),
        'helix' : ( 0, ('sql', ) )
           }

# The personality questions
persq = {}
for k, v in persdict.items():
    persq[k] = BoolQuestion ( 'Do you wish to install personality %s' % k, 
                              v[0])

# A function to check personality dependencies
def _checkPers ( p ):
    deps = persdict[p][1]

    if deps:
        for i in deps:
            if not persq[i].get():
               print 'Personality %s depends on %s, added' % (p, i)
               persq[i].set(1)

               # Check further dependencies
               _checkPers ( i )
                
bypass = BoolQuestion('Some skunk modules may not work, continue', 0)
# Ok, start configuration
print 'Welcome to Skunk software installation'
print "First we'll check a few things"
print "checking for syslog module...",
sys.stdout.flush()
try:
    import syslog
except:
    print "No!"
    print "install the python syslog module (see ops manual) and try again"
    if not bypass.ask():
        sys.exit()
else:
    print "Ok"
print "checking for crypt module...",
sys.stdout.flush()
try:
    import crypt
except:
    print "No!"
    print "install the python crypt module (see ops manual) and try again"
    if not bypass.ask():
        sys.exit()
else:
    print "Ok"
    
print 'Second, we need to ask a few questions' 

try:
    qdict['DCOracle'].ask()
    qdict['Prefix'].ask(convert=os.path.expanduser) 
    qdict['User'].ask()

    # Get the group of the user
    try:
        _def_group = grp.getgrgid(pwd.getpwnam(qdict['User'].get())[3])[0]
    except KeyError:
        print 'Error: cannot seem to find user %s!' % qdict['User'].get()
        sys.exit(1)

    qdict['Group'].setDefault ( _def_group )
    qdict['Group'].ask()

    if 1:#qdict['AED'].get():
        # Check the webroot directory
        _web_dir = os.path.join ( qdict['Prefix'].get(), 'webroot' )

        if os.path.exists ( _web_dir ):
            print 
            print 'WARNING: directory %s exists. The installation usually ' % \
                   _web_dir
            print 'installs some sample documents there. If you did any '
            print 'development in that directory, files could be lost.' 
            print 'If you would like to skip the the AED documents '
            print 'installation, answer "y" (default) to the next question'

            _install_web = BoolQuestion ( 'Skip default content installation', 
                                          1 ).ask()
        else:
            _install_web = 1

        print
        print 'Please choose which personalities to install.'
        print 'The templating personality is installed by default. You can'
        print 'install a number of additional personalities, depending on what'
        print 'you are planning to do with the server'
        print 

        # Ask the personality question
        for p, q in persq.items():
            q.ask()

        # Check the personality dependencies
        print 'Checking personality dependencies...' 
        for p in filter( lambda x, persq=persq : persq[x].get(), persq.keys()):
            _checkPers ( p )

        # Ask for mysql / postgresql directories
        if persq['mysql'].get() and not qdict['MySQLDir'].ask(convert=os.path.expanduser):
            persq['mysql'].set(0)

        if persq['postgresql'].get() and not qdict['PostgreSQLDir'].ask(convert=os.path.expanduser):
            persq['postgresql'].set(0)

    # Ok, now re-iterate what the user has selected and save it to a file 
    # to avoid users later saying 'but I chose that option...'
    f = cStringIO.StringIO()

    f.write ( 'Installation directory: %s\n' % qdict['Prefix'].get() )
    f.write ( 'User to install as: %s.%s\n' % (qdict['User'].get(), 
                                               qdict['Group'].get()) )

    _perslist = ['templating']
    if 1:#qdict['AED'].get():
        f.write ( 'Install AED\n' )

        # Show the list of personalities to install
        _perslist = _perslist + filter ( lambda x, persq=persq : persq[x].get(), 
                                                   persq.keys() )

        f.write ( '--> Selected personalities: %s\n' % 
                                               string.join ( _perslist, ', ' ))

        if _install_web:
            f.write ( '--> Install sample Web content\n' )
        else:
            f.write ( '--> Do not install sample Web content\n' )

    if qdict['DCOracle'].get():
        f.write ( 'Install DCOracle oracle python interface\n' )

    out = f.getvalue()
    print '\nThis is what you have selected:'
    print out

    _confirm = BoolQuestion ( 'Are you sure you want to proceed', 1 )

    if not _confirm.ask():
        print 'Interrupting, please re-run setup...'
        sys.exit(1)

except KeyboardInterrupt:
    print ( 'Interrupted...' )
    sys.exit ( 1 )

# Store the answers to keep log
try:
   _fname = '.setup.log'
   open ( '.setup.log', 'w' ).write ( out )
   print 'Stored your answers in %s' % _fname
except (OSError, IOError), val:
   print 'Cannot write %s: %s' % (_fname, val)
   sys.exit(1)

print 'Running selected configure scripts...'

config_parms = '--with-user=%s --with-group=%s --prefix=%s' % \
                                                ( qdict['User'].get(),
                                                qdict['Group'].get(),
                                                qdict['Prefix'].get(),
                                                )

root_parms = config_parms + ' --with-mysql=%s --with-postgresql=%s' % ( 
                                                qdict['MySQLDir'].get(),
                                                qdict['PostgreSQLDir'].get() )

if 1:#qdict['AED'].get():
    root_parms = root_parms + ' --with-aed'


if qdict['DCOracle'].get():
    root_parms = root_parms + ' --with-dcoracle'

#print '===== Running top level config'
print '===== Running configure'

if 1:#qdict['AED'].get():
    #aed_config = config_parms + ' --with-pers="%s"' % \
    aed_config = ' --with-pers="%s"' % string.join ( _perslist, ' ' ) 

    # Do we do web install?
    if _install_web:
        aed_config = aed_config + ' --with-webdoc'


syscmd = './configure %s%s' % (root_parms, aed_config)
print 'running', syscmd
if os.system ( syscmd ):
    print 'Top level config failed'
    sys.exit(1)


print
print 'All done! Now run gmake; gmake install to install Skunk'
