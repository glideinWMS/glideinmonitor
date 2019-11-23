#!/usr/bin/env bash

PKG_VERSION=0.1
PKG_RELEASE=0.1.rc1

# Make the new RPM spec file and tarball (package is not actually used)
python3 setup.py bdist_rpm
cp build/bdist.linux-x86_64/rpm/SPECS/glideinmonitor.spec pkg/rpm/generated-glideinmonitor.spec

# Add the second source file
tar cvzf glideinmonitor-pkgrpm-${PKG_VERSION}.tar.gz pkg/rpm/templates
mv glideinmonitor-pkgrpm-${PKG_VERSION}.tar.gz build/bdist.linux-x86_64/rpm/SOURCES/

# Build RPM
sed -e "s/__GMONITOR_PKG_VERSION__/$PKG_VERSION/g" -e "s/__GMONITOR_PKG_RELEASE__/PKG_RELEASE/g" pkg/rpm/glideinmonitor.spec > build/bdist.linux-x86_64/rpm/SPECS/glideinmonitor.spec
pushd build/bdist.linux-x86_64/rpm/SPECS/
rpmbuild -ba glideinmonitor.spec
popd

