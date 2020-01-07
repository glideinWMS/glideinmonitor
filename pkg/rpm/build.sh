#!/usr/bin/env bash
# Script to build the RPM and OSG release

################### Constants #####
RPM_DIR=build/bdist.linux-x86_64/rpm
SOURCES_DIR=$RPM_DIR/SOURCES/
SPECS_DIR=$RPM_DIR/SPECS/
OSG_USER=
OSG_SVN=
OSG_HOST=library.cs.wisc.edu
OSG_UPSTREAM=/p/vdt/public/html/upstream/
GMONITOR_REPO="ssh://p-glideinwms@cdcvs.fnal.gov/cvs/projects/glideinwms-glideinmonitor"
work_dir="/tmp/osgrelease.$$"


################### Fnctions #####
help_msg (){
  cat << EOF
$0 [options] [ PKG_VERSION [ PKG_RELEASE ]]
  PKG_VERSION  Version of the package (e.g. 1, x.y.z, default: 0.1)
  PKG_RELEASE  RPM Package release number (e.g. 1, 0.1.rc1, default: 0.1.rc1)
  -v       verbose
  -h       print this message
  -f       force the update of the PKG_VERSION in setup.py (can be used only if -i is also there)
  -i       build in place, without checking out the specific branch
  -o USER  upload to OSG upstream the source packages. USER at the OSG library host
  -s DIR   update the OSG SVN files in DIR (directrory of the glideinmonitor package w/ osg and upstream subdirs)
EOF
}


update_setup () {
    pass
}


update_osg () {
    echo "--- Uploading to the OSG library (your password is required twice)"
    ssh "$OSG_USER@$OSG_HOST" "mkdir -p $osg_uploaddir"
    if [ $? -eq 0 ]; then
        scp -q "${SOURCES_DIR}/glideinmonitor-${PKG_VERSION}.tar.gz" "${SOURCES_DIR}/glideinmonitor-pkgrpm-${PKG_VERSION}.tar.gz" "${OSG_USER}@${OSG_HOST}:$osg_uploaddir/"
        [ $? -eq 0 ] && echo "Tarballs Uploaded to $OSG_HOST: $osg_uploaddir" || { echo "ERROR: failed to upload the tarball to $OSG_HOST: $osg_uploaddir"; exit 1; }
    else
        echo "ERROR: Failed to create directory $osg_uploaddir on the OSG build machine ($OSG_HOST)"
        exit 1
    fi
}


update_git () {
    # 1 - PKG_VERSION
    pass
}


update_svn () {
    echo "--- Updating OSG SVN repo "
    # updating OSG SVN repo: upstream and spec file in osg of glideinmonitor
    cp "$SPECS_DIR/glideinmonitor.spec" "$OSG_SVN/osg/"
    f1_sha1="$(sha1sum "${SOURCES_DIR}/glideinmonitor-${PKG_VERSION}.tar.gz" | cut -f1 -d' ' )"
    f2_sha1="$(sha1sum "${SOURCES_DIR}/glideinmonitor-pkgrpm-${PKG_VERSION}.tar.gz" | cut -f1 -d' ' )"
    pushd $OSG_SVN > /dev/null
        echo "glideinmonitor/${src_version}/glideinmonitor-pkgrpm-${PKG_VERSION}.tar.gz sha1sum=$f2_sha1" > upstream/developer_pkg.tarball.source
        echo "glideinmonitor/${src_version}/glideinmonitor-${PKG_VERSION}.tar.gz sha1sum=$f1_sha1" > upstream/developer.tarball.source
    popd > /dev/null
    echo "To commit the SVN changes type the following:"
    echo "pushd $OSG_SVN; svn ci -m 'Ready for GlideinMonitor $PKG_VERSION $PKG_RELEASE'"
    echo "popd"
}


# Parameters defaults, evaluation and validation
VERBOSE=
UPDATE_SETUP=
DO_INPLACE=

while getopts "hvfis:o:" option
do
  case "${option}"
  in
  h) help_msg; exit 0;;
  v) VERBOSE=yes;;
  f) UPDATE_SETUP=yes;;
  i) DO_INPLACE=yes;;
  s) OSG_SVN=$OPTARG;;
  o) OSG_USER=$OPTARG;;
  esac
done

[[ -n "$UPDATE_SETUP" && -z "$DO_INPLACE" ]] && { echo "ERROR: Cannot update setup.py on a checked out branch/tag."; help_msg;  exit 1; }
[[ -n "$OSG_SVN" && ! -d "$OSG_SVN" ]] && { echo "ERROR: Invalid OSG SVN directory: $OSG_SVN"; help_msg;  exit 1; }

shift $((OPTIND-1))

PKG_VERSION=${1:-0.1}
PKG_RELEASE=${2:-0.1.rc1}
# git version tag: "v" at beginning, underscore instead of dots, _rcN if RC
src_version="v${PKG_VERSION//./_}"
[[ "$PKG_RELEASE" = *rc* ]] && src_version="${src_version}_rc${PKG_RELEASE##*rc}"
osg_uploaddir="$OSG_UPSTREAM/glideinmonitor/$src_version"


if [[ -n "$DO_INPLACE" ]]; then
    echo "Building GlideinMonitor v${PKG_VERSION}, RPM release ${PKG_RELEASE} starting from the current branch"
else
    mkdir -p "$work_dir"
    pushd "$work_dir" > /dev/null
    git clone $GMONITOR_REPO gmonitor
    cd gmonitor
    if ! git checkout $src_version ; then
        echo "ERROR: Failed to checkout $src_version, aborting. Did you push your commit?"
        exit 1
    fi
    echo "Building GlideinMonitor v${PKG_VERSION}, RPM release ${PKG_RELEASE} starting from branch/tag $src_version (in ${work_dir}/gmonitor)"
fi
setup_version="$(grep "^    version='" setup.py)"
setup_version="${setup_version#*\'}"
setup_version="${setup_version%\'*}"
if [[ "$setup_version" != "$PKG_VERSION" ]]; then
    if [[ -n "$UPDATE_SETUP" ]]; then
        echo "ERROR: Update of setup.py not implemented. Exiting."
        exit 1
        update_setup $PKG_VERSION
    else
        echo "ERROR: PKG_VERSION and version in setup.py mismatch ($PKG_VERSION vs $setup_version). Exiting."
        exit 1
    fi
fi

echo "--- 1 --- creating the source packages"
# Make the new RPM spec file and tarball (package is not actually used)
if [[ -n "$VERBOSE" ]]; then
    python3 setup.py bdist_rpm
else
    python3 setup.py bdist_rpm &> /dev/null
fi
cp $SPECS_DIR/glideinmonitor.spec pkg/rpm/generated-glideinmonitor.spec

# Add the second source file
if [[ -n "$VERBOSE" ]]; then
    tar cvzf glideinmonitor-pkgrpm-${PKG_VERSION}.tar.gz pkg/rpm/templates
else
    tar czf glideinmonitor-pkgrpm-${PKG_VERSION}.tar.gz pkg/rpm/templates
fi
mv glideinmonitor-pkgrpm-${PKG_VERSION}.tar.gz "${SOURCES_DIR}/"


echo "--- 2 --- building the RPMs "
# Build RPM
# which buildroot is it using?
# starting in /opt/glideinmonitor/glideinmonitor/build/bdist.linux-x86_64/rpm/SPECS
# BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)
# using ~/rpmbuild/ (linked to /opt/glideinmonitor/glideinmonitor/build/bdist.linux-x86_64/rpm )
# https://linux.die.net/man/8/rpmbuild

sed -e "s/__GMONITOR_PKG_VERSION__/$PKG_VERSION/g" -e "s/__GMONITOR_PKG_RELEASE__/$PKG_RELEASE/g" pkg/rpm/glideinmonitor.spec > build/bdist.linux-x86_64/rpm/SPECS/glideinmonitor.spec
pushd $SPECS_DIR > /dev/null
if [[ -n "$VERBOSE" ]]; then
    rpmbuild -ba glideinmonitor.spec
else
    rpmbuild -ba glideinmonitor.spec &> /dev/null
fi
cd ../RPMS/noarch
echo "RPM files are in `pwd`"
popd > /dev/null

# git update and tagging?

[[ -n "$OSG_USER" ]] && update_osg

[[ -n "$OSG_SVN" ]] && update_svn

[[ -z "$DO_INPLACE" ]] && { popd > /dev/null ; }

