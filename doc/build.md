# Compiling and building the GlideinMonitor packages

GlideinMonitor can be distributed as python package or as RPM.

## RPM building

* Clone the git repository 
* cd to the root directory `glideinmonitor` and change to the desired branch (or keep master)
* Run the script `pkg/rpm/build.sh`

The RPM files will be in the folder `build/bdist.linux-x86_64/rpm/RPMS/noarch/`

The build script allows to specify the version (PKG_VERSION), the release (PKG_RELEASE), and some more options:
```
build.sh [options] [ PKG_VERSION [ PKG_RELEASE ]]
  PKG_VERSION  Version of the package (e.g. 1, x.y.z, default: 0.1)
  PKG_RELEASE  RPM Package release number (e.g. 1, 0.1.rc1, default: 0.1.rc1)
  -v       verbose
  -h       print this message
  -f       force the update of the PKG_VERSION in setup.py (can be used only if -i is also there)
  -i       build in place, without checking out the specific branch
  -o USER  upload to OSG upstream the source packages. USER at the OSG library host
  -s DIR   update the OSG SVN files in DIR (directrory of the glideinmonitor package w/ osg and upstream subdirs)
  -p PARTS to run only part of the setup, comma separated list of parts (defaults to all: p1,p2). Parts meaning:
            p1 - is the source file preparation using setuptools
            p2 - is the building of the RPMs using rpmbuild
```

When building a specific branch/tag (invocation without -i), the branch/tag must exist in the repository. The name will be the PKG_VERSION with dots replaced by underscores.
e.g. v1.2.3 becomse v1_2_3

NOTE: if you are building the RPMs for OSG then the version and release numbers combination must be unique and bigger than the last one in OSG. This is a requirement for Koji.
Build in place (-i) should not be used when building for OSG

