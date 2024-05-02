#!/bin/bash

rm -rf /etc/glideinmonitor/sqlite_dir/glideinmonitor.sqlite
rm -rf /etc/glideinmonitor/archive/index_lock
rm -rf /etc/glideinmonitor/archive/filter/glidein_gfactory_instance/user_frontend/*
rm -rf /etc/glideinmonitor/archive/original/glidein_gfactory_instance/user_frontend/*
echo "done"