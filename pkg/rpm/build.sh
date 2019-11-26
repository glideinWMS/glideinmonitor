#!/usr/bin/env bash

[[ "$1" = "-h" || "$1" = "--help" ]] && { echo "$0 [ PKG_VERSION [ PKG_RELEASE ]]" ; exit }

PKG_VERSION=${1:-0.1}
PKG_RELEASE=${2:-0.1.rc1}

echo "Building GlideinMonitor v${PKG_VERSION}, RPM release ${PKG_RELEASE} starting from the current branch"

echo "--- 1 --- creating the source packages "
# Make the new RPM spec file and tarball (package is not actually used)
python3 setup.py bdist_rpm
cp build/bdist.linux-x86_64/rpm/SPECS/glideinmonitor.spec pkg/rpm/generated-glideinmonitor.spec

# Add the second source file
tar cvzf glideinmonitor-pkgrpm-${PKG_VERSION}.tar.gz pkg/rpm/templates
mv glideinmonitor-pkgrpm-${PKG_VERSION}.tar.gz build/bdist.linux-x86_64/rpm/SOURCES/

echo "--- 2 --- building the RPMs "
# Build RPM
# which buildroot is it using?
# starting in /opt/glideinmonitor/glideinmonitor/build/bdist.linux-x86_64/rpm/SPECS
# BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)
# using ~/rpmbuild/ (linked to /opt/glideinmonitor/glideinmonitor/build/bdist.linux-x86_64/rpm )
# https://linux.die.net/man/8/rpmbuild

sed -e "s/__GMONITOR_PKG_VERSION__/$PKG_VERSION/g" -e "s/__GMONITOR_PKG_RELEASE__/PKG_RELEASE/g" pkg/rpm/glideinmonitor.spec > build/bdist.linux-x86_64/rpm/SPECS/glideinmonitor.spec
pushd build/bdist.linux-x86_64/rpm/SPECS/
rpmbuild -ba glideinmonitor.spec

cd ../RPMS
echo "RPM files are in `pwd`"
popd

