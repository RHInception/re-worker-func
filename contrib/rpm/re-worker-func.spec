%if 0%{?rhel} && 0%{?rhel} <= 6
%{!?__python2: %global __python2 /usr/bin/python2}
%{!?python2_sitelib: %global python2_sitelib %(%{__python2} -c "from distutils.sysconfig import get_python_lib; print(get_python_lib())")}
%{!?python2_sitearch: %global python2_sitearch %(%{__python2} -c "from distutils.sysconfig import get_python_lib; print(get_python_lib(1))")}
%endif

%global _pkg_name replugin
%global _src_name reworkerfunc

Name: re-worker-func
Summary: RE Worker to run commands over Func
Version: 0.0.8
Release: 6%{?Dist}

Group: Applications/System
License: AGPLv3
Source0: %{_src_name}-%{version}.tar.gz
Url: https://github.com/rhinception/re-worker-func

BuildArch: noarch
BuildRequires: python2-devel, python-setuptools
Requires: func, re-worker, python-setuptools

%description
Release Engine Worker to run commands over Func.

%prep
%setup -q -n %{_src_name}-%{version}

%build
%{__python2} setup.py build

%install
%{__python2} setup.py install -O1 --root=$RPM_BUILD_ROOT --record=re-worker-func-files.txt

%files -f re-worker-func-files.txt
%defattr(-, root, root)
%doc README.md LICENSE AUTHORS conf/*
%dir %{python2_sitelib}/%{_pkg_name}
%exclude %{python2_sitelib}/%{_pkg_name}/__init__.py*

%changelog
* Wed Nov  12 2014 Ryan Cook <rcook@redhat.com> - 0.0.8-6
- Fix for func update

* Wed Oct  2 2014 Steve Milner <stevem@gnulinux.net> - 0.0.8-5
- fileops Tar has to have switches flipped.

* Wed Oct  1 2014 Steve Milner <stevem@gnulinux.net> - 0.0.8-4
- fileops ChangeOwnership needs to use a capital R.

* Wed Oct  1 2014 Steve Milner <stevem@gnulinux.net> - 0.0.8-3
- Disabling puppet run enable support.

* Wed Oct  1 2014 Steve Milner <stevem@gnulinux.net> - 0.0.8-2
- Disabling puppet motd support.

* Tue Sep 30 2014 Steve Milner <stevem@gnulinux.net> - 0.0.8-1
- FileOps now added.

* Mon Sep 22 2014 Tim Bielawa <tbielawa@redhat.com> - 0.0.7-2
- puppet:Disable using 'motd' param now behaves correctly if the token is a 'str' or 'unicode' type

* Thu Sep 18 2014 Steve Milner <stevem@gnulinux.net> - 0.0.7-1
- Exit codes can now be defined.

* Thu Sep 18 2014 Tim Bielawa <tbielawa@redhat.com> - 0.0.6-2
- Fix issue with returned params update dict not setting a required key

* Wed Sep 17 2014 Tim Bielawa <tbielawa@redhat.com> - 0.0.6-1
- Now with puppet worker

* Fri Jul 25 2014 Steve Milner <stevem@gnulinux.net> - 0.0.5-1
- Added more app logging.

* Mon Jul 7 2014 Ryan Cook <rcook@redhat.com> - 0.0.4-3
- Support for multiple response types

* Sun Jun 29 2014 Tim Bielawa <tbielawa@redhat.com> - 0.0.4-2
- Finish custom parameter parser

* Tue Jun 24 2014 Tim Bielawa <tbielawa@redhat.com> - 0.0.4-1
- Begin implementing a system for custom func module parameter/result handlers

* Mon Jun 23 2014 Tim Bielawa <tbielawa@redhat.com> - 0.0.3-5
- Fix 'Invoking func method' output inserting an empty string for the called method

* Fri Jun 20 2014 Steve Milner <stevem@gnulinux.net> - 0.0.3-4
- Try loops now work properly.

* Fri Jun 20 2014 Tim Bielawa <tbielawa@redhat.com> - 0.0.3-3
- OK. Actually REALLY fix the async polling procedure

* Fri Jun 20 2014 Tim Bielawa <tbielawa@redhat.com> - 0.0.3-2
- Fix async polling procedure

* Thu Jun 19 2014 Steve Milner <stevem@gnulinux.net> - 0.0.3-1
- Config now allows for static_host overrides.

* Thu Jun 19 2014 Ryan Cook <rcook@redhat.com> - 0.0.2-3
- Pulled in updates to Makefile

* Thu Jun 19 2014 Steve Milner <stevem@gnulinux.net> - 0.0.2-2
- Defattr not being used in files section.

* Wed Jun 18 2014 Tim Bielawa <tbielawa@redhat.com> - 0.0.2-1
- Func commands run in async mode now

* Tue Jun 17 2014 Ryan Cook <rcook@redhat.com> - 0.0.1-4
- Added exclude __init__.py*

* Thu Jun 12 2014 Steve Milner <stevem@gnulinux.et> - 0.0.1-3
- python-setuptools is required.

* Mon Jun  9 2014 Tim Bielawa <tbielawa@redhat.com> - 0.0.1-2
- Fix dep on reworker to re-worker

* Thu Jun  5 2014 Steve Milner <stevem@gnulinux.et> - 0.0.1-1
- First release
