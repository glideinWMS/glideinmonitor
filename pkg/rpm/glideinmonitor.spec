# Modified version starting from the setuptools generated one
# https://docs.fedoraproject.org/en-US/packaging-guidelines/Python/
# Wheels packaging is possible but not recommended
# https://fedoraproject.org/wiki/PythonWheels

# Release Candidates NVR format
#%define release 0.1.rc1
# Official Release NVR format
#%define release 1

#%global version __GWMS_RPM_VERSION__
#%global release __GWMS_RPM_RELEASE__

%define name glideinmonitor
%define version 0.1
%define unmangled_version %{version}
%define release 0.1.rc1

Summary: GlideinMonitor Web Server and Indexer
Name: %{name}
Version: %{version}
Release: %{release}%{?dist}
License: Fermitools Software Legal Information (Modified BSD License)
Group: Development/Libraries
#BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-buildroot
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)
Prefix: %{_prefix}
BuildArch: noarch
Vendor: GlideinWMS team <glideinwms-support@fnal.gov>
Url: https://github.com/glideinWMS/glideinmonitor

Source0: %{name}-%{unmangled_version}.tar.gz

%global srcname glideinmonitor

%global config_file %{_sysconfdir}/%{srcname}
%global archive_dir %{_localstatedir}/lib/glideinmonitor/archive
%global upload_dir %{_localstatedir}/lib/glideinmonitor/upload
%global processing_dir %{_localstatedir}/lib/glideinmonitor/processing
%global db_dir %{_localstatedir}/lib/glideinmonitor/db
# DB defined in config file (may be local or remote)
# %global db_dir %{_localstatedir}/lib/glideinmonitor/db
# using also:
# /usr/sbin %{_sbindir} , /var/lib %{_sharedstatedir}, /usr/share %{_datadir}, cron dir, ?
%global systemddir %{_prefix}/lib/systemd/system


Requires: python3
# Should Flask be required or pip-installed?
Requires: python3-flask
BuildRequires: python3-devel


%description
GlideinMonitor is a package for archiving and serving the log files written by
the Glidein of GlideinWMS (Glidein Workload Management System).

glideinmonitor-webserver
glideinmonitor-indexer

%prep

#%autosetup -n %{srcname}-%{version}
%setup -n %{name}-%{unmangled_version}

%build
%{__python3} setup.py build

#install -D bin/stashcp %{buildroot}%{_bindir}/stashcp
#install -D -m 0644 bin/caches.json %{buildroot}%{_datarootdir}/stashcache/caches.json

%install
%{__python3} setup.py install --single-version-externally-managed -O1 --root=$RPM_BUILD_ROOT --record=INSTALLED_FILES
install -d $RPM_BUILD_ROOT%{archive_dir}
install -d $RPM_BUILD_ROOT%{upload_dir}
install -d $RPM_BUILD_ROOT%{processing_dir}
install -d $RPM_BUILD_ROOT%{db_dir}
echo %{archive_dir} >> INSTALLED_FILES
echo %{upload_dir} >> INSTALLED_FILES
echo %{processing_dir} >> INSTALLED_FILES
echo %{db_dir} >> INSTALLED_FILES


%clean
rm -rf $RPM_BUILD_ROOT

%files -f INSTALLED_FILES
%defattr(-,root,root)

#%files
#%{_bindir}/stashcp
#%{_datarootdir}/stashcache/caches.json
#%{_datarootdir}/stashcache/README-caches


%changelog

