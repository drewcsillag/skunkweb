# initial draft thanks to Steve Coursen <talon@coursen.tempestnetworks.net>,

%define name skunkweb
%define version 3.1.3
%define release 1
%define __prefix /usr/local/skunk

Summary: an easily extensible web application server written in Python,
Name: %{name}
Version: %{version}
Release: %{release}
Copyright: GPL
Group: System Environment/Daemon
Source0:  http://prdownloads.sourceforge.net/skunkweb/%{name}-%{version}.tgz
URL: http://skunkweb.sourceforge.net/
Packager:  Jacob Smullyan <smulloni@smullyan.org>
BuildRoot: /var/tmp/%{name}-%{version}-root
requires: /usr/bin/python /usr/lib/python2.1  /usr/lib/python2.1/site-packages/mx

%description
SkunkWeb is a scalable, extensible and easy to use web application server
designed for handling both high-traffic and smaller sites, written in Python.

%changelog
* Wed Nov 14 2001 Jacob Smullyan <smulloni@smullyan.org>
- originally by Steve Coursen <talon@coursen.tempestnetworks.net>
- use defines

%prep
%setup -q

%build
./configure --with-user=nobody --with-group=nobody
# this doesn't check for apache at all!  
make RPM_OPT_FLAGS="$RPM_OPT_FLAGS"

%install
[ -d $RPM_BUILD_ROOT ] && rm -rf $RPM_BUILD_ROOT
mkdir -p $RPM_BUILD_ROOT%{__prefix}
make RPM_OPT_FLAGS="$RPM_OPT_FLAGS" install

%clean
rm -rf $RPM_BUILD_ROOT

%files
%defattr(-,nobody,nobody)
%config %{__prefix}/etc/sw.conf
%config %{__prefix}/etc/mime.types
%dir %{__prefix}


