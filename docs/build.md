# Compiling and building the GlideinMonitor packages

GlideinMonitor can be distributed as python package or as RPM.

## RPM building

* Clone the git repository 
* cd to the root directory `glideinmonitor` and change to the desired branch (or keep master)
* Run the script `pkg/rpm/build.sh`

The RPM files will be in the folder `build/bdist.linux-x86_64/rpm/RPMS/noarch/`

## Possible deployments

GlideinMonitor has two components, Indexer and Web Server, and uses a Database.

The simplest installation has all the GlideinMonitor components (including the database) 
on a single host. In this case, especially for small installations, you can use sqlite 
as database and the files will be on a local file system.

A more complex deployment separates the Indexer and the Web Server. In this case the database could be 
a MySQL server on a third host. The archived files must be on a shared file system readable also from the Web Server. 

## Install RPMs

### One host deployment

One host deployment using sqlite.

If you are installing from local files yum dependencies between the GlideinMonitor packages will not work, 
so you have to install them in order.

```shell
for i in  glideinmonitor-common glideinmonitor-indexer glideinmonitor-webserver glideinmonitor-monolith; do yum install -y ./$i*; done
```

Use configuration files with sqlite.
Check `/etc/glideinmonitor.conf`.

Optionally prepare some sample files 
```bash
pushd /var/lib/glideinmonitor/upload/
tar xvzf ~/sample.tar.gz
mv archive/client ./
chown -R gmonitor: *
rmdir archive/
```

To start/stop the services you can use systemctl:
```bash
systemctl reload systemd
systemctl start glideinmonitor-indexer.service
systemctl status glideinmonitor-indexer.service

systemctl start glideinmonitor-webserver
systemctl status glideinmonitor-webserver

# To stop
systemctl stop glideinmonitor-webserver
systemctl stop glideinmonitor-indexer.service
```

### Three hosts deployment


## Install via Docker
