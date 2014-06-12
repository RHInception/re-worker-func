%if 0%{?rhel} && 0%{?rhel} <= 6
%{!?__python2: %global __python2 /usr/bin/python2}
%{!?python2_sitelib: %global python2_sitelib %(%{__python2} -c "from distutils.sysconfig import get_python_lib; print(get_python_lib())")}
%{!?python2_sitearch: %global python2_sitearch %(%{__python2} -c "from distutils.sysconfig import get_python_lib; print(get_python_lib(1))")}
%endif

%global _pkg_name replugin
%global _src_name reworkerfunc

Name: re-worker-func
Summary: RE Worker to run commands over Func
Version: 0.0.1
Release: 3%{?dist}

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
%doc README.md LICENSE AUTHORS conf/*
%dir %{python2_sitelib}/%{_pkg_name}

%changelog
* Thu Jun 12 2014 Steve Milner <stevem@gnulinux.et> - 0.0.1-3
- python-setuptools is required.

* Mon Jun  9 2014 Tim Bielawa <tbielawa@redhat.com> - 0.0.1-2
- Fix dep on reworker to re-worker

* Thu Jun  5 2014 Steve Milner <stevem@gnulinux.et> - 0.0.1-1
- First release
