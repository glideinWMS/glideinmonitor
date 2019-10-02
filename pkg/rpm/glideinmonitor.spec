# How to build tar file
# ...
# https://docs.fedoraproject.org/en-US/packaging-guidelines/Python/

# Release Candidates NVR format
#%define release 0.1.rc1
# Official Release NVR format
#%define release 1

%global version __GWMS_RPM_VERSION__
%global release __GWMS_RPM_RELEASE__

%global srcname glideinmonitor

%global config_file %{_sysconfdir}/%{srcname}
%global archive_dir %{_localstatedir}/lib/glideinmonitor/archive
%global upload_dir %{_localstatedir}/lib/glideinmonitor/upload
# DB defined in config file (may be local or remote) 
# %global db_dir %{_localstatedir}/lib/glideinmonitor/db
# using also:
# /usr/sbin %{_sbindir} , /var/lib %{_sharedstatedir}, /usr/share %{_datadir}, cron dir, ?
%global systemddir %{_prefix}/lib/systemd/system

Name:           glideinmonitor
Version:        %{version}
Release:        %{release}%{?dist}
Summary:        The Glidein Monitoring service (GlideinMonitor)
Group:          System Environment/Daemons
License:        Fermitools Software Legal Information (Modified BSD License)
URL:            https://github.com/glideinWMS/glideinmonitor
BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)
BuildArch:      noarch

Requires: python3
# Should Flask be required or pip-installed?
Requires: python3-flask
BuildRequires:  python3-devel

Source:         %{srcname}.tar.gz


%description
This is a package for archiving and serving the log files written by 
the Glidein of GlideinWMS (Glidein Workload Management System).

%prep
#%setup -qn %{srcname}-%{version}
#%autosetup -n %{srcname}-%{version}

%install
install -d $RPM_BUILD_ROOT%{_sbindir}
install -D bin/stashcp %{buildroot}%{_bindir}/stashcp
install -D -m 0644 bin/caches.json %{buildroot}%{_datarootdir}/stashcache/caches.json
install -D -m 0644 %{SOURCE1} %{buildroot}%{_datarootdir}/stashcache/README-caches

%files
%{_bindir}/stashcp
%{_datarootdir}/stashcache/caches.json
%{_datarootdir}/stashcache/README-caches

%changelog

