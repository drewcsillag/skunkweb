#  which python binary to use, list the full path or "auto"
%define config_pythonpath auto

# name of the python rpm -- may be called "python2" on some systems
#  "auto" will try to figure it out
%define config_pythonpkgname auto

#  name of apache package, Red Hat >= 8.0 uses "httpd", older uses "apache"
#  "auto" will try to figure it out
%define config_apachepkgname auto

#################################
#  End of user-modifiable configs
#################################

%define name skunkweb
%define version 20030524
%define release 1

#  locate python executable
%define pythonpath %(if [ "%{config_pythonpath}" != auto ]; then echo %{config_pythonpath}; else ls /usr/bin/python[23].* | sort | tail -1; fi)

#  find the name of the python package
%define pythonreq %(if [ "%{config_pythonpkgname}" != auto ]; then echo %{config_pythonpkgname}; else rpm -qf --qf '%''{name}' %{pythonpath}; fi)

#  find the name of the apache package
%define apachereq %(if [ "%{config_apachepkgname}" != auto ]; then echo %{config_apachepkgname}; else rpm -qi httpd >/dev/null 2>&1 && echo httpd || echo apache; fi)

#  location to apxs executable
%define apxspath /usr/sbin/apxs

#  get python lib directory
%define pylibdir %(%{pythonpath} -c "import sys; print '%s/lib/python%s' % (sys.prefix, sys.version[:3])")

Summary: An easily extensible web application server written in Python.
Name: %{name}
Version: %{version}
Release: %{release}
Copyright: GPL/BSD (dual licensed)
Group: System Environment/Daemon
Source0: http://prdownloads.sourceforge.net/skunkweb/%{name}-%{version}.tar.gz
URL: http://skunkweb.sourceforge.net/
Packager:  Jacob Smullyan <smulloni@smullyan.org>
BuildRoot: /var/tmp/%{name}-%{version}-root
Requires: %{pythonpath}
Requires: %{pylibdir}/site-packages/mx/__init__.py
BuildRequires: %{apxspath}
BuildRequires: %{pythonreq} >= 2.1

%description
SkunkWeb is a scalable, extensible and easy to use web application server
designed for handling both high-traffic and smaller sites, written in Python.

%package mod_skunkweb
Summary: A module for including Skunkweb in Apache.
Group: System Environment/Daemons
Requires: %{name}
Requires: %{apachereq}

%description mod_skunkweb
A module for including the Skunkweb environment in the Apache web server.

%changelog
* Sun May 25 2003 Sean Reifschneider <jafo-rpms@tummy.com> [3.4b3+-1]
- Addinig an init file.
- Switching to use a skunkweb user, and pre/post for adding/deleting user.
- Adding a logrotate script.

* Sat May 24 2003 Sean Reifschneider <jafo-rpms@tummy.com> [3.4b3+-1]
- Changing the cache directory and ownership.
- Changing the sw.conf to reflect the new cache location.
- Changing how the python executable version is found.

* Fri May 23 2003 Sean Reifschneider <jafo-rpms@tummy.com> [3.4b3+-1]
- Setting INSTALL for build.
- Sets up cache reaper cron job.
- mod_skunkweb defaults to using root for the file attributes.

* Thu May 22 2003 Jacob Smullyan <smulloni@smullyan.org>
- some revisions to layout
- simpler way of getting python library path
- update license
- no longer requires a patch (Sean's changes moved into source)

* Thu May 22 2003 Sean Reifschneider <jafo-rpms@tummy.com> [3.4b3-2]
- Making a mod_skunkweb sub-package

* Mon May 19 2003 Sean Reifschneider <jafo-rpms@tummy.com> [3.4b3]
- Updating to 3.4b3.
- Misc changes for building.
- Able to build as non-root user.

* Wed Nov 14 2001 Jacob Smullyan <smulloni@smullyan.org>
- originally by Steve Coursen <talon@coursen.tempestnetworks.net>
- use defines

%prep
%setup -q

%build
%configure --with-user=skunkweb \
           --with-group=skunkweb \
           --localstatedir=/var \
           --bindir=/usr/bin \
           --libdir=/usr/lib/skunkweb \
           --sysconfdir=/etc/skunkweb \
           --prefix=/usr/share/skunkweb \
           --with-cache=/var/lib/skunkweb/cache \
           --with-docdir=/usr/share/doc/skunkweb-%{version} \
           --with-logdir=/var/log/skunkweb \
           --with-python=%{pythonpath} \
           --with-apxs=%{apxspath}

make RPM_OPT_FLAGS="$RPM_OPT_FLAGS"

%install
[ ! -z "$RPM_BUILD_ROOT" -a "$RPM_BUILD_ROOT" != / ] && rm -rf $RPM_BUILD_ROOT
mkdir -p $RPM_BUILD_ROOT%{_prefix}
mkdir -p $RPM_BUILD_ROOT/etc/cron.daily
mkdir -p $RPM_BUILD_ROOT/etc/rc.d/init.d
mkdir -p $RPM_BUILD_ROOT/etc/logrotate.d
%makeinstall DESTDIR="%{buildroot}" APXSFLAGS="-c" \
           INSTALL=install INSTALL_DATA=install

#  set up cache reaper
echo '0 0 * * * skunkweb /usr/share/skunkweb/util/cache_reaper.py -c /var/lib/skunkweb/cache' >"$RPM_BUILD_ROOT"/etc/cron.daily/skunkweb

#  set up logrotate script
cp util/rpm/skunkweb.logrotate $RPM_BUILD_ROOT/etc/logrotate.d/skunkweb

#  build file list
find "${RPM_BUILD_ROOT}" -type f | sed 's|^'"${RPM_BUILD_ROOT}"'||' |
   grep -v -e '^/etc/skunkweb/' >skunkweb.files
echo '%attr(750,skunkweb,skunkweb) %dir /var/lib/skunkweb/cache' >>skunkweb.files

#  set up init file
cp util/rpm/skunkweb.init $RPM_BUILD_ROOT/etc/rc.d/init.d/skunkweb
echo '%attr(755,root,root) /etc/rc.d/init.d/skunkweb' >>skunkweb.files

#  set up log-file
mkdir -p $RPM_BUILD_ROOT/var/log/skunkweb
echo '%attr(750,skunkweb,skunkweb) %dir /var/log/skunkweb' >>skunkweb.files

#  install skunkweb
MODFILELIST=`pwd`/mod_skunkweb.files
export MODFILELIST
(
   cd SkunkWeb/mod_skunkweb
   moddir=`%{apxspath} -q LIBEXECDIR`
   mkdir -p "${RPM_BUILD_ROOT}/${moddir}"
   MODSWNAME=mod_skunkweb.so
   [ -f .libs/mod_skunkweb.so ] && MODSWNAME=.libs/mod_skunkweb.so
   cp "${MODSWNAME}" "${RPM_BUILD_ROOT}/${moddir}"
   echo "/${moddir}"/mod_skunkweb.so >>"$MODFILELIST"

   #  use conf.d?
   confdir=`%{apxspath} -q SYSCONFDIR`
   if [ -d "${confdir}".d ]
   then
      mkdir -p "${RPM_BUILD_ROOT}/${confdir}.d/"
      cp httpd_conf.stub "${RPM_BUILD_ROOT}/${confdir}.d/"skunkweb.conf
      echo "%config /${confdir}.d/"skunkweb.conf >>"$MODFILELIST"
   else
      mkdir -p "${RPM_BUILD_ROOT}/${confdir}/"
      cp httpd_conf.stub "${RPM_BUILD_ROOT}/${confdir}/"skunkweb.conf
      echo "%config /${confdir}/"skunkweb.conf >>"$MODFILELIST"
   fi
)

%clean
[ ! -z "$RPM_BUILD_ROOT" -a "$RPM_BUILD_ROOT" != / ] && rm -rf $RPM_BUILD_ROOT

%pre
useradd -r skunkweb
exit 0

%post
chkconfig --add skunkweb
chkconfig skunkweb on

%preun
chkconfig --del skunkweb
userdel skunkweb

%files -f skunkweb.files
%defattr(-,skunkweb,skunkweb)
%config /etc/skunkweb/sw.conf
%config /etc/skunkweb/mime.types

%files mod_skunkweb -f mod_skunkweb.files
%defattr(-,root,root)
