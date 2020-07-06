#!/bin/bash

# setup system

apt-get update
apt-get upgrade -y

apt-get update
apt-get install firmware-atheros

# install python
apt-get install python3-dev python3-pip python3-setuptools

# install dependencies for tshark
apt-get install tshark

# install required packages for wifi control
apt-get install -y hostapd dnsmasq

# installing netifaces
pip3 install netifaces requests configargparse dbus-python

# installing systemd-manager
sudo apt install dbus libdbus-glib-1-dev libdbus-1-dev
pip3 install git+https://github.com/emlid/systemd-manager.git#egg=sysdmanager
