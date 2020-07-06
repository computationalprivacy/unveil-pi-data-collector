# Supervisord Setup

Use [supervisord](http://supervisord.org/) to setup autostart.

## Purpose 

For autostart of the modules during startup.

## Installation

```bash
pip3 install supervisord
```

## Setup supervisord

```shell
cp default.supervisord.conf supervisord.conf
# now change the username and password in supervisord.conf

cp supervisord.conf /etc/supervisord.conf
/usr/local/bin/supervisord -n  # to check
```

## Start Supervisord during startup

```
cp supervisord.service /lib/systemd/system/
systemctl daemon-reload
systemctl enable supervisord
```

## Commands

**To check status**

```bash
supervisorctl -u username -p password
# use status command to check
```
