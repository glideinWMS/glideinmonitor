# GlideinMonitor Installation

## Possible deployments

GlideinMonitor has two components, Indexer and Web Server, and uses a Database.

The simplest installation has all the GlideinMonitor components (including the database) 
on a single host. In this case, especially for small installations, you can use sqlite 
as database and the files will be on a local file system.

A more complex deployment separates the Indexer and the Web Server. In this case the database could be 
a MySQL server on a third host. The archived files must be on a shared file system readable also from the Web Server. 


## Using setuptools (and wheel)

To install the python package, run the following commands,

```shell
# install for the system or the user
pip3 install buildtools
pip3 install wheel

git clone https://github.com/glideinWMS/glideinmonitor
cd glideinmonitor
python3 setup.py bdist_wheel
pip3 install dist/glideinmonitor-*.whl
```

### Configuration
Next, setup the configuration.  For the config.json file (which must be located in "/etc/.glideinmonitor/config.json"), below is an example file,

```json
{
  "GWMS_Log_Dir": "/etc/.glideinmonitor/archive",
  "Saved_Log_Dir": "/etc/.glideinmonitor/longterm_archive",
  "db": {
    "type": "mysql",
    "dir": "/etc/.glideinmonitor/sqlite_dir",
    "host": "localhost",
    "user": "root",
    "pass": "",
    "db_name": "glideinmonitor"
  },
  "Log_Dir": "/etc/.glideinmonitor/logs",
  "Log_Level": "INFO",
  "Users": [
    {
      "name": "admin",
      "password": "21232f297a57a5a743894a0e4a801fc3",
      "filter": "original"
    },
    {
      "name": "john",
      "password": "f57dd60e195b04a106b90dfbd297db02"
    }
  ],
  "DisplayType": "filter",
  "Port": 8888,
  "Host": "127.0.0.1"
}
```

This will also be documented later but here is what they briefly mean,
* GWMS_Log_Dir - The archive directory which should/Must contain a sub directory called "client"
* Saved_Log_Dir - A directory the indexer will use to zip and save the out/err files
* db_type - Can be MySQL or SQLite
* db_dir, db_name - SQLite - A directory and DB file name to store the SQLite database file
* db_host, db_user, db_pass, db_name - MySQL - connection info, on first run the database should be created manually without any tables in it
* Log_Dir - A place to store logs from the webserver and indexer running
* Log_Level - NONE, ERROR, WARNING, INFO are the acceptable options
* Users - For the webserver http auth and providing archives
    * Name: http auth username
    * Password: http auth password; represented as a MD5 hash of the password (in the example above, the password is "admin"); To create your own you can use something like `echo -n MY_PASSWORD | md5sum`)
    * Filter: The filter version to provide to the user on the web portal; Defaults to "original"
* Port, Host - For the webserver to operate on

It can be tested using a sample Glidein logs archive which contains the proper client subdirectory.

Once that's all complete, then run "glideinmonitor-indexer" and then "glideinmonitor-webserver".


## Install using RPM

There are multiple RPM packages:
* glideinmonitor-indexer - GlideinMonitor Indexer 
* glideinmonitor-webserver - GlideinMonitor Web Server
* glideinmonitor-monolith - Install both Indexer and Web Server on the same host
* glideinmonitor-common - common elements between Indexer and Web Server (never installed directly)


### One host deployment

One host deployment using sqlite.

GlideinMonitor is available in the OSG development repository.
Prepare the [required Yum repositories](https://opensciencegrid.org/docs/common/yum/).
Install GlideinMonitor:
```shell
yum install --enablerepo=osg-development glideinmonitor-monolith
```

If you are installing from local files (RPM downloaded manually) yum dependencies between the GlideinMonitor packages will not work, 
so you have to install them in order:
```shell
for i in  glideinmonitor-common glideinmonitor-indexer glideinmonitor-webserver glideinmonitor-monolith; do yum install -y ./$i*; done
```

Here a configuration example using sqlite (`/etc/glideinmonitor.conf`) and the default RPM directories:
```json
{
  "GWMS_Log_Dir": "/var/lib/glideinmonitor/upload",
  "Saved_Log_Dir": "/var/lib/glideinmonitor/archive",
  "db": {
    "type": "sqlite",
    "dir": "/var/lib/glideinmonitor/db",
    "db_name": "glideinmonitor"
  },
  "Log_Dir": "/var/log/glideinmonitor",
  "Log_Level": "INFO",
  "Users": {
    "admin": "21232f297a57a5a743894a0e4a801fc3"
  },
  "Port": 8888,
  "Host": "127.0.0.1"
}
```
See the [configuration section above](#configuration) for more information.

Optionally prepare some sample files 
```bash
pushd /var/lib/glideinmonitor/upload/
tar xvzf ~/sample.tar.gz
mv archive/client ./
chown -R gmonitor: *
rmdir archive/
```

To start/stop the services you should use systemctl:
```bash
# After the RPM install
systemctl reload systemd

# To start
systemctl start glideinmonitor-indexer.service
systemctl status glideinmonitor-indexer.service

systemctl start glideinmonitor-webserver
systemctl status glideinmonitor-webserver

# To stop
systemctl stop glideinmonitor-webserver
systemctl stop glideinmonitor-indexer.service
```

### Three hosts deployment

Instructions coming soon

### Troubleshooting a RPM installation

You can start manually the services to get a better view of the error messages.
Make sure that you start the services as `gmonitor` user and not `root`, 
otherwise there will be files created by `root` that will cause the regular startup
to fail
```bash
su - gmonitor
/usr/sbin/glideinmonitor-indexer start
/usr/sbin/glideinmonitor-webserver start
```

If the Python requirements (from requirements.txt) have not been installed as dependency for the current python, 
they can be installed manually using the correct pip3, as `root`: 
```bash
pip3 install flask
pip3 install flask_httpauth
pip3 install mysql-connector-python
```


## Install via Docker

Coming soon
