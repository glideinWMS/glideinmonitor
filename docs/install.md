# GlideinMonitor Installation

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
  "Users": {
    "admin": "21232f297a57a5a743894a0e4a801fc3"
  },
  "Port": 8888,
  "Host": "127.0.0.1"
}
```

example 2, for RPM w/ sqlite (/etc/glideinmonitor.conf):
```json
{
  "GWMS_Log_Dir": "/var/lib/glideinmonitor/upload",
  "Saved_Log_Dir": "/var/lib/glideinmonitor/archive",
  "db": {
    "type": "sqlite",
    "dir": "/var/lib/glideinmonitor/db",
    "host": "localhost",
    "user": "root",
    "pass": "",
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

This will also be documented later but here is what they briefly mean,
* GWMS_Log_Dir - The archive directory which should/Must contain a sub directory called "client"
* Saved_Log_Dir - A directory the indexer will use to zip and save the out/err files
* db_type - Can be MySQL or SQLite
* db_dir - SQLite - A directory to store the SQLite database file
* db_host, db_user, db_pass, db_name - MySQL - connection info, on first run the database should be created manually without any tables in it
* Log_Dir - A place to store logs from the webserver and indexer running
* Log_Level - NONE, ERROR, WARNING, INFO are the acceptable options
* Users - For the webserver http auth, the key is the username and the value is an MD5 hash of the password (in the example above, the password is "admin". To create your own you can use something like `echo -n MY_PASSWORD | md5sum`)
* Port, Host - For the webserver to operate on

It can be tested using a sample Glidein logs archive which contains the proper client subdirectory.

Once that's all complete, then run "glideinmonitor-indexer" and then "glideinmonitor-webserver".
